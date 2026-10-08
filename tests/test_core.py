import tempfile
import unittest
from pathlib import Path

from app.core import answer, connect, run_metric, seed, today_answer
from app.demo_auth import authenticate, issue_cookie, parse_cookie


class WarehouseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "demo.db"
        seed(self.path, force=True)
        self.conn = connect(self.path)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def _sum(self, metric, key, account_id=None):
        rows = run_metric(self.conn, metric, account_id)
        return round(sum(row[key] for row in rows), 2)

    def test_net_sales_reconcile_across_cuts(self):
        channel = self._sum("net_by_channel", "net_sales")
        family = self._sum("net_by_family", "net_sales")
        region = self._sum("net_by_region", "net_sales")
        month = self._sum("net_by_month", "net_sales")
        kpi = run_metric(self.conn, "kpi_summary")[0]["net_sales"]
        self.assertAlmostEqual(channel, family, places=1)
        self.assertAlmostEqual(channel, region, places=1)
        self.assertAlmostEqual(channel, month, places=1)
        self.assertAlmostEqual(channel, kpi, places=1)
        self.assertGreater(channel, 1_000_000)

    def test_quarantine_stays_out_of_gold(self):
        bronze = self.conn.execute("SELECT COUNT(*) AS n FROM bronze_invoice").fetchone()["n"]
        gold = self.conn.execute("SELECT COUNT(*) AS n FROM gold_invoice").fetchone()["n"]
        quarantine = self.conn.execute("SELECT COUNT(*) AS n FROM quarantine").fetchone()["n"]
        self.assertEqual(bronze, gold + quarantine)
        self.assertGreaterEqual(quarantine, 4)
        leaked = self.conn.execute(
            "SELECT COUNT(*) AS n FROM gold_invoice WHERE invoice_id LIKE 'INV-BAD%'"
        ).fetchone()["n"]
        self.assertEqual(leaked, 0)

    def test_funnel_counts_are_ordered(self):
        row = run_metric(self.conn, "commercial_funnel")[0]
        self.assertGreater(row["activities"], row["opportunities"])
        self.assertGreater(row["opportunities"], row["won"])
        self.assertGreater(row["net_sales"], row["incremental_net"])
        self.assertGreater(row["incremental_net"], 0)

    def test_account_scope_cannot_see_other_customers(self):
        rows = run_metric(self.conn, "top_accounts", "ACCT-0001")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["account_id"], "ACCT-0001")
        scoped = self._sum("net_by_channel", "net_sales", "ACCT-0001")
        full = self._sum("net_by_channel", "net_sales")
        self.assertLess(scoped, full * 0.2)

    def test_assistant_answers_margin_and_refuses_outside_scope(self):
        margin = answer(self.conn, "margin by brand", "operator", None)
        self.assertEqual(margin["route"], "metric")
        self.assertEqual(margin["metric"], "margin_by_family")
        self.assertIn("gold_invoice", margin["sql"])
        self.assertGreater(len(margin["rows"]), 0)

        share = answer(self.conn, "what is our Nielsen share", "operator", None)
        self.assertEqual(share["route"], "refuse")
        self.assertIsNone(share["sql"])

        forecast = answer(self.conn, "SAP IBP forecast for Nerds", "operator", None)
        self.assertEqual(forecast["route"], "refuse")
        self.assertIsNone(forecast["sql"])

    def test_scoped_answer_binds_account_parameter(self):
        payload = answer(self.conn, "top accounts", "acct-0001", "ACCT-0001")
        self.assertEqual(payload["params"], ["ACCT-0001"])
        self.assertEqual(len(payload["rows"]), 1)
        audit = self.conn.execute(
            "SELECT account_scope, metric FROM audit_log WHERE username = ?",
            ("acct-0001",),
        ).fetchone()
        self.assertEqual(audit["account_scope"], "ACCT-0001")
        self.assertEqual(audit["metric"], "top_accounts")

    def test_today_path_does_not_query(self):
        text = today_answer("trade spend by channel")
        self.assertIn("one-off export", text)
        self.assertNotIn("SELECT", text)

    def test_halloween_month_beats_january(self):
        rows = {row["month"]: row["net_sales"] for row in run_metric(self.conn, "net_by_month")}
        self.assertGreater(rows["2025-10"], rows["2026-01"])
        self.assertGreater(rows["2026-09"], rows["2026-01"])


class PublicAndLabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "demo.db"
        seed(self.path, force=True)
        self.conn = connect(self.path)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_public_context_keeps_scopes_separate(self):
        from app.core import answer

        rows = run_metric(self.conn, "public_landscape")
        by_entity = {}
        for row in rows:
            by_entity.setdefault(row["entity"], []).append(row)
        ferrara = next(row for row in by_entity["Ferrara Candy Company"] if row["metric"] == "Net sales")
        self.assertEqual(ferrara["value_num"], 2200)
        hershey = next(row for row in rows if row["entity"] == "The Hershey Company")
        self.assertEqual(hershey["value_num"], 11692.6)
        mars = next(row for row in rows if row["entity"] == "Mars / Mars Wrigley")
        self.assertIsNone(mars["value_num"])
        workforce = [row["value_num"] for row in by_entity["Ferrara Candy Company"] if "Workforce" in row["metric"]]
        self.assertEqual(sorted(workforce), [8600, 9400])
        payload = answer(self.conn, "show the public competitive set", "operator", None)
        self.assertEqual(payload["metric"], "public_landscape")
        refused = answer(self.conn, "what is our Nielsen share", "operator", None)
        self.assertEqual(refused["route"], "refuse")
        self.assertIsNone(refused["sql"])

    def test_lab_evals_and_scope_pin(self):
        from app.lab import board_brief, run_evals, scope_pin

        report = run_evals(self.conn)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["passed"], report["total"])
        pin = scope_pin(self.conn)
        self.assertGreater(pin["operator_net_sales"], pin["lakeshore_net_sales"])
        brief = board_brief(self.conn)
        self.assertEqual(len(brief["sections"]), 5)
        self.assertIn("public competitive set", brief["narrative"])

    def test_databricks_is_staged_not_pretended(self):
        from app.databricks_backend import connection_status, genie_status, resolve_config

        status = connection_status(resolve_config(environ={}, env_file=Path("/no/such.env"), profile_file=Path("/no/such.cfg")))
        self.assertFalse(status["configured"])
        self.assertIn("01_commercial.sql", status["sql_files"])
        self.assertIn("DATABRICKS_TOKEN", status["missing"])
        self.assertFalse(genie_status()["called"])

    def test_databricks_profile_builds_http_path_without_exposing_token(self):
        from app.databricks_backend import ddl_statements, qmark_to_pyformat, resolve_config, safe_error

        profile = Path(self.tmp.name) / "databrickscfg"
        profile.write_text(
            "[DEFAULT]\nhost = https://adb-1.cloud.databricks.net\ntoken = dapiSECRETVALUE\nwarehouse_id = abc123\n"
        )
        env_file = Path(self.tmp.name) / ".env"
        env_file.write_text("DATABRICKS_SCHEMA=ferrara_commercial\n")
        config = resolve_config(environ={}, env_file=env_file, profile_file=profile)
        self.assertTrue(config["configured"])
        self.assertEqual(config["hostname"], "adb-1.cloud.databricks.net")
        self.assertEqual(config["http_path"], "/sql/1.0/warehouses/abc123")
        self.assertEqual(config["source"], "databrickscfg")
        status_keys = ("hostname", "http_path", "catalog", "schema", "missing", "configured")
        public = {key: config[key] for key in status_keys}
        self.assertNotIn("dapiSECRETVALUE", str(public))
        ddl = "\n".join(ddl_statements(config))
        self.assertIn("CREATE SCHEMA IF NOT EXISTS ferrara_commercial", ddl)
        self.assertIn("gold_invoice", ddl)
        self.assertIn("bronze_activity", ddl)
        self.assertEqual(qmark_to_pyformat("SELECT * FROM gold_invoice WHERE account_id = ?"), "SELECT * FROM gold_invoice WHERE account_id = %s")
        self.assertIn("dapi…", safe_error(RuntimeError("rejected dapiSECRETVALUE")))


class AuthTests(unittest.TestCase):
    def test_cookie_round_trip(self):
        session = authenticate("operator", "fc-demo")
        self.assertEqual(session["role"], "operator")
        self.assertIsNone(authenticate("operator", "nope"))
        header = issue_cookie(session).split(";", 1)[0]
        parsed = parse_cookie(header)
        self.assertEqual(parsed["username"], "operator")
        self.assertIsNone(parse_cookie("fc_demo=tampered.sig"))
