import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.core import SliceError, answer, connect, run_metric, seed, today_answer
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
        from app.core import metric_sql

        bronze = self.conn.execute("SELECT COUNT(*) AS n FROM bronze_invoice").fetchone()["n"]
        gold = self.conn.execute("SELECT COUNT(*) AS n FROM gold_invoice").fetchone()["n"]
        quarantine = self.conn.execute("SELECT COUNT(*) AS n FROM quarantine").fetchone()["n"]
        self.assertEqual(bronze, gold + quarantine)
        rejected = run_metric(self.conn, "quality")
        self.assertEqual(sum(row["rejected"] for row in rejected), quarantine)
        self.assertNotIn(" as rows", metric_sql("quality")[0].lower())
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

    def test_slicers_narrow_the_book_and_skip_activity_family(self):
        from app.core import metric_sql

        full = self._sum("net_by_channel", "net_sales")
        grocery = run_metric(self.conn, "net_by_channel", None, {"channel": "Grocery"})
        grocery_net = round(sum(row["net_sales"] for row in grocery), 2)
        self.assertLess(grocery_net, full)
        self.assertTrue(all(row["channel"] == "Grocery" for row in grocery))
        nerds = run_metric(self.conn, "net_by_family", None, {"family": "Nerds", "subregion": "Midwest"})
        self.assertEqual(len(nerds), 1)
        self.assertEqual(nerds[0]["family"], "Nerds")
        europe = run_metric(self.conn, "net_by_region", None, {"region": "Europe"})
        self.assertEqual([row["region"] for row in europe], ["Europe"])
        self.assertLess(europe[0]["net_sales"], full)
        years = run_metric(self.conn, "net_by_year")
        self.assertEqual([row["year"] for row in years], [f"FY{year}" for year in range(2020, 2027)])
        latest = run_metric(self.conn, "kpi_summary", None, {"year": "FY2026"})[0]["net_sales"]
        self.assertLess(latest, full)
        with self.assertRaises(Exception):
            run_metric(self.conn, "net_by_channel", None, {"region": "Europe", "subregion": "Midwest"})
        sql, params = metric_sql("activity_mix", None, {"family": "Nerds", "channel": "Club"})
        self.assertNotIn("family", sql)
        self.assertEqual(params, ("Club",))
        with self.assertRaises(Exception):
            metric_sql("net_by_channel", None, {"channel": "Internet"})
        score_sql, _params = metric_sql("account_scorecard")
        self.assertNotIn("from account", score_sql.lower())
        scorecard = run_metric(self.conn, "account_scorecard")
        self.assertEqual(len(scorecard), self.conn.execute("SELECT COUNT(*) AS n FROM account").fetchone()["n"])
        self.assertAlmostEqual(round(sum(row["net_sales"] for row in scorecard), 2), full, places=1)

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

    def test_assistant_applies_slicers_and_refusals_skip_them(self):
        full = answer(self.conn, "win rate by channel", "operator", None)
        grocery = answer(
            self.conn,
            "win rate by channel",
            "operator",
            None,
            filters={"channel": "Grocery", "family": "Nerds"},
        )
        self.assertLess(len(grocery["rows"]), len(full["rows"]))
        self.assertEqual(grocery["filters"]["channel"], "Grocery")
        self.assertEqual(grocery["filters"]["family"], "Nerds")
        self.assertTrue(all(row["channel"] == "Grocery" for row in grocery["rows"]))
        self.assertIn("Grocery", grocery["params"])
        self.assertIn("Nerds", grocery["params"])

        activity = answer(
            self.conn,
            "activity mix",
            "operator",
            None,
            filters={"channel": "Club", "family": "Nerds"},
        )
        self.assertEqual(activity["filters"], {"channel": "Club"})
        self.assertEqual(activity["skipped"], ["family"])
        self.assertNotIn("family", activity["sql"])

        refused = answer(
            self.conn,
            "what is our Nielsen share",
            "operator",
            None,
            filters={"channel": "Grocery"},
        )
        self.assertEqual(refused["route"], "refuse")
        self.assertIsNone(refused["sql"])
        self.assertEqual(refused["params"], [])
        self.assertEqual(refused["filters"], {})
        with self.assertRaises(SliceError):
            answer(self.conn, "win rate", "operator", None, filters={"channel": "Internet"})

    def test_snowflake_pool_reuses_sessions(self):
        from app.snowflake_backend import SnowflakeStore

        opened = []

        class FakeCursor:
            description = [("ok",)]

            def execute(self, *_args, **_kwargs):
                return None

            def fetchall(self):
                return [(1,)]

            def close(self):
                return None

        class FakeConn:
            def cursor(self):
                return FakeCursor()

            def close(self):
                self.closed = True

        store = SnowflakeStore(
            {
                "configured": True,
                "database": "FERRARA_COMMERCIAL",
                "schema": "SERVING",
                "token": "not-a-real-token",
            }
        )

        def opener():
            conn = FakeConn()
            opened.append(conn)
            return conn

        store._open = opener
        store.warm(2)
        store.execute("SELECT 1")
        store.execute("SELECT 1")
        self.assertEqual(len(opened), 2)
        self.assertEqual(len(store._idle), 2)

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

    def test_waterfall_season_scorecard_and_mix(self):
        channel = self._sum("net_by_channel", "net_sales")
        waterfall = self._sum("waterfall_by_channel", "net_sales")
        self.assertAlmostEqual(channel, waterfall, places=2)
        for row in run_metric(self.conn, "waterfall_by_channel"):
            self.assertAlmostEqual(row["gross_sales"] - row["trade_spend"], row["net_sales"], places=1)
            self.assertAlmostEqual(row["net_sales"] - row["cogs"], row["margin"], places=1)
        season = {row["invoice_month"]: row["index_vs_january"] for row in run_metric(self.conn, "season_index")}
        self.assertEqual(season["Jan"], 100.0)
        self.assertGreater(season["Oct"], season["Jan"])
        windows = {row["season_window"]: row["net_sales"] for row in run_metric(self.conn, "halloween_window")}
        self.assertIn("Halloween window", windows)
        self.assertGreater(windows["Rest of book"], windows["Halloween window"])
        scorecard = run_metric(self.conn, "account_scorecard", "ACCT-0001")
        self.assertEqual(len(scorecard), 1)
        self.assertEqual(scorecard[0]["account_name"], "Lakeshore Grocery")
        self.assertIsNotNone(scorecard[0]["last_activity"])
        open_pipeline = self._sum("pipeline_by_stage", "opportunities")
        aged = self._sum("pipeline_age", "opportunities")
        self.assertEqual(open_pipeline, aged)
        mix = run_metric(self.conn, "family_mix_by_quarter")
        self.assertIn("FY2026", {row["quarter"] for row in mix})
        skus = run_metric(self.conn, "sku_rank")
        self.assertEqual(len(skus), 16)
        self.assertEqual(answer(self.conn, "pipeline age", "operator")["metric"], "pipeline_age")
        self.assertEqual(answer(self.conn, "price waterfall by channel", "operator")["metric"], "waterfall_by_channel")
        cells = self._sum("region_by_channel", "net_sales")
        self.assertAlmostEqual(cells, channel, places=2)

    def test_call_list_is_open_pipeline_with_a_reason(self):
        rows = run_metric(self.conn, "call_list")
        self.assertTrue(rows)
        self.assertLessEqual(len(rows), 8)
        self.assertEqual(rows, sorted(rows, key=lambda row: row["open_pipeline"], reverse=True))
        for row in rows:
            self.assertGreater(row["open_pipeline"], 0)
            self.assertTrue(row["reason"])
            self.assertTrue(row["deals"])
            self.assertLessEqual(len(row["deals"]), 3)
            self.assertEqual(
                [deal["expected_net"] for deal in row["deals"]],
                sorted((deal["expected_net"] for deal in row["deals"]), reverse=True),
            )
        nerds = run_metric(self.conn, "call_list", None, {"family": "Nerds"})
        self.assertTrue(nerds)
        self.assertTrue(all(deal["family"] == "Nerds" for row in nerds for deal in row["deals"]))
        europe = run_metric(self.conn, "call_list", None, {"region": "Europe"})
        self.assertTrue(europe)
        self.assertTrue(all(row["region"] == "Europe" for row in europe))
        asked = answer(self.conn, "who should we call", "operator", None)
        self.assertEqual(asked["metric"], "call_list")
        self.assertIn("not a Ferrara call plan", asked["answer"])
        self.assertIn("expected net", asked["answer"])
        self.assertIn(asked["rows"][0]["deals"][0]["family"], asked["answer"])
        self.assertIn("gold_opportunity", asked["sql"])
        scoped = answer(self.conn, "who should we call", "operator", None, filters={"region": "Europe"})
        self.assertEqual(scoped["filters"].get("region"), "Europe")
        self.assertTrue(all(row["region"] == "Europe" for row in scoped["rows"]))

    def test_family_channel_close_names_the_gap(self):
        rows = run_metric(self.conn, "close_by_family_channel", None, {"family": "Nerds"})
        self.assertTrue(rows)
        self.assertTrue(all(row["family"] == "Nerds" for row in rows))
        weak = min(rows, key=lambda row: row["win_rate"])
        asked = answer(self.conn, "where does nerds lose the close", "operator", None, filters={"family": "Nerds"})
        self.assertEqual(asked["metric"], "close_by_family_channel")
        self.assertIn("Nerds", asked["answer"])
        self.assertIn(weak["channel"], asked["answer"])
        self.assertIn("not a syndicated rank", asked["answer"])
        europe = run_metric(self.conn, "close_by_family_channel", None, {"region": "Europe", "family": "Nerds"})
        self.assertTrue(europe)
        self.assertLess(sum(row["opportunities"] for row in europe), sum(row["opportunities"] for row in rows))


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
        mars = next(row for row in by_entity["Mars / Mars Wrigley"] if row["metric"] == "Filed net sales")
        self.assertIsNone(mars["value_num"])
        prospectus = next(row for row in rows if row["entity"] == "Mars Inc.")
        self.assertEqual(prospectus["value_num"], 54600)
        floor = next(row for row in rows if row["metric"] == "Company-stated net revenue")
        self.assertEqual(floor["value_num"], 4000)
        workforce = [row["value_num"] for row in by_entity["Ferrara Candy Company"] if "Workforce" in row["metric"]]
        self.assertEqual(sorted(workforce), [8600, 9400])
        orangeburg = next(row for row in rows if row["entity"] == "Orangeburg County, South Carolina")
        self.assertEqual(orangeburg["value_num"], 675)
        self.assertIn("Q1 2029", orangeburg["period"])
        bellwood = next(row for row in rows if row["entity"] == "Bellwood, Illinois")
        self.assertIsNone(bellwood["value_num"])
        campaign = next(row for row in rows if row["entity"] == "NERDS Big Game 2025")
        self.assertIsNone(campaign["value_num"])
        self.assertIn("Shaboozey", campaign["scope_note"])
        soccer = next(row for row in rows if row["entity"] == "U.S. Soccer packs")
        self.assertIsNone(soccer["value_num"])
        plant = answer(self.conn, "what do we know about the orangeburg plant", "operator", None)
        self.assertEqual(plant["metric"], "public_landscape")
        self.assertIsNotNone(plant["sql"])
        self.assertEqual([row["entity"] for row in plant["rows"]], ["Orangeburg County, South Carolina"])
        self.assertIn("675", plant["answer"])
        self.assertIn("Q1 2029", plant["answer"])
        book = sqlite3.connect(":memory:")
        book.row_factory = sqlite3.Row
        book.execute(
            "CREATE TABLE public_context (group_name, entity, relationship, metric, value_num, unit, period, scope_note, source, source_url)"
        )
        cited = answer(book, "what do we know about the orangeburg plant", "operator", None, audit_conn=self.conn)
        book.close()
        self.assertIn("675", cited["answer"])
        game = answer(self.conn, "what was the nerds big game spend", "operator", None)
        self.assertEqual(game["metric"], "public_landscape")
        self.assertIn("not published", game["answer"])
        self.assertTrue(game["rows"])
        self.assertTrue(all(row["value_num"] is None for row in game["rows"] if row["metric"] == "Media spend"))
        payload = answer(self.conn, "show the public competitive set", "operator", None)
        self.assertEqual(payload["metric"], "public_landscape")
        refused = answer(self.conn, "what is our Nielsen share", "operator", None)
        self.assertEqual(refused["route"], "refuse")
        self.assertIsNone(refused["sql"])
        pressed = answer(self.conn, "where should we press", "operator", None)
        self.assertEqual(pressed["route"], "plays")
        self.assertIsNone(pressed["sql"])
        self.assertIn("Stop paying for misses", pressed["answer"])
        self.assertIn("not Ferrara results", pressed["answer"])
        self.assertIn("20.1%", pressed["answer"])
        europe = answer(self.conn, "where should we press", "operator", None, filters={"region": "Europe"})
        self.assertEqual(europe["filters"].get("region"), "Europe")
        europe_subs = run_metric(self.conn, "win_rate_by_subregion", None, {"region": "Europe"})
        weak_sub = min(europe_subs, key=lambda row: row["win_rate"])["subregion"]
        self.assertIn(weak_sub, europe["answer"])
        self.assertNotIn("Asia Pacific", europe["answer"])
        self.assertNotIn("Canada", europe["answer"])
        self.assertIn("Skittles share", europe["answer"])
        europe_wins = run_metric(self.conn, "win_rate_by_channel", None, {"region": "Europe"})
        strong = max(europe_wins, key=lambda row: row["win_rate"])["channel"]
        self.assertTrue(any(arena["name"] == "Chewy fruit" and strong in arena["press"] for arena in europe["arenas"]))
        self.assertTrue(any("2023" in arena["press"] for arena in europe["arenas"]))

    def test_compete_brief_keeps_private_revenue_empty(self):
        from app.compete import compete_brief

        brief = compete_brief(self.conn, self.conn)
        private = {row["entity"]: row["value_num"] for row in brief["private"]}
        self.assertIsNone(private["Mars / Mars Wrigley"])
        self.assertIsNone(private["Haribo"])
        self.assertIsNone(private["Perfetti Van Melle"])
        wins = run_metric(self.conn, "win_rate_by_channel")
        weak = min(wins, key=lambda row: row["win_rate"])
        strong = max(wins, key=lambda row: row["win_rate"])
        self.assertIn(weak["channel"], brief["plays"][0]["title"])
        self.assertIn(strong["channel"], brief["plays"][1]["title"])
        chewy = next(arena for arena in brief["arenas"] if arena["name"] == "Chewy fruit")
        self.assertIn(strong["channel"], chewy["press"])
        self.assertIn("Skittles share", chewy["press"])
        self.assertIn("candy band above", chewy["fact"])
        seasonal = next(arena for arena in brief["arenas"] if arena["name"] == "Seasonal sugar")
        self.assertIn("2023", seasonal["press"])
        self.assertIn("20.1%", seasonal["fact"])
        region_wins = run_metric(self.conn, "win_rate_by_region")
        weak_region = min(region_wins, key=lambda row: row["win_rate"])["region"]
        titles = " ".join(play["title"] for play in brief["plays"])
        self.assertIn(weak_region, titles)
        self.assertIn("FY2026", titles)
        self.assertNotIn("24-account", brief["book_label"])
        joined = " ".join(play["detail"] for play in brief["plays"])
        self.assertIn("11,692.6", joined)
        self.assertIn("labeled synthetic guess", joined)
        haribo = next(row for row in brief["guesses"] if row["entity"] == "Haribo")
        self.assertEqual(haribo["kind"], "synthetic")
        self.assertEqual(haribo["point"], 3.0)
        mars_band = next(row for row in brief["guesses"] if row["entity"] == "Mars Wrigley confectionery")
        self.assertIsNone(mars_band["point"])
        self.assertIn("Not a filing", mars_band["method"])
        self.assertIn("Nielsen", brief["boundary"])
        self.assertEqual(len(brief["roles"]), 3)
        europe = compete_brief(self.conn, self.conn, filters={"region": "Europe"})
        self.assertIn("region Europe", europe["book_label"])
        self.assertIsNone(next(row["value_num"] for row in europe["private"] if row["entity"] == "Haribo"))
        europe_titles = " ".join(play["title"] for play in europe["plays"])
        self.assertNotIn("Asia Pacific", europe_titles)
        subs = run_metric(self.conn, "win_rate_by_subregion", filters={"region": "Europe"})
        weak_sub = min(subs, key=lambda row: (row["win_rate"], -row["opportunities"]))["subregion"]
        strong_sub = max(subs, key=lambda row: (row["win_rate"], row["opportunities"]))["subregion"]
        self.assertIn(weak_sub, europe_titles)
        europe_chewy = next(arena for arena in europe["arenas"] if arena["name"] == "Chewy fruit")
        self.assertIn(strong_sub, europe_chewy["press"])
        self.assertNotIn("Canada", europe_chewy["press"])
        self.assertIn("Skittles share", europe_chewy["press"])
        one_year = compete_brief(self.conn, self.conn, filters={"year": "FY2020"})
        self.assertIn("year FY2020", one_year["book_label"])
        self.assertNotIn("FY2026", " ".join(play["title"] for play in one_year["plays"]))
        self.assertTrue(any(row["entity"] == "The Hershey Company" for row in one_year["scale"]))

    def test_supply_receipts_match_the_invoice_book(self):
        ordered = self.conn.execute("SELECT SUM(units_ordered) AS n FROM gold_receipt").fetchone()["n"]
        invoiced = self.conn.execute("SELECT SUM(units) AS n FROM gold_invoice").fetchone()["n"]
        self.assertEqual(ordered, invoiced)
        score = run_metric(self.conn, "vendor_scorecard")
        self.assertEqual(score[0]["vendor_name"], "Gel & Bright")
        self.assertLess(score[0]["score"], score[-1]["score"])
        risk = run_metric(self.conn, "supply_risk")
        butter = next(row for row in risk if row["family"] == "Butterfinger")
        self.assertEqual(butter["vendor_name"], "Cocoa Lane")
        self.assertGreaterEqual(butter["share_pct"], 85)
        service = run_metric(self.conn, "supply_service")
        self.assertEqual(service[0]["family"], "Trolli")
        self.assertGreater(service[0]["units_short"], 0)
        europe = run_metric(self.conn, "supply_service", filters={"region": "Europe"})
        self.assertLess(sum(row["units_ordered"] for row in europe), ordered)
        self.assertEqual(run_metric(self.conn, "vendor_scorecard", "ACCT-0001"), [])
        pressed = answer(self.conn, "vendor scorecard", "operator", None)
        self.assertEqual(pressed["metric"], "vendor_scorecard")
        self.assertIn("Gel & Bright", pressed["answer"])
        account_card = answer(self.conn, "account scorecard", "operator", None)
        self.assertEqual(account_card["metric"], "account_scorecard")

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
        self.assertFalse(genie_status(environ={}, env_file=Path("/no/such.env"))["called"])
        from app.databricks_backend import ask_genie, genie_answer_text

        dark = ask_genie("margin by brand", environ={}, env_file=Path("/no/such.env"))
        self.assertFalse(dark["called"])
        text, sql = genie_answer_text(
            {
                "attachments": [
                    {"text": {"content": "Margin is 12."}},
                    {"query": {"query": "SELECT 1"}},
                ]
            }
        )
        self.assertEqual(text, "Margin is 12.")
        self.assertEqual(sql, "SELECT 1")

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

    def test_snowflake_is_ferrara_and_dark_without_credentials(self):
        from app.snowflake_backend import connection_status, ddl_statements, resolve_config, safe_error

        status = connection_status(resolve_config(environ={}, env_file=Path("/no/such.env"), profile_file=Path("/no/such.toml")))
        self.assertFalse(status["configured"])
        self.assertIn("SNOWFLAKE_PAT", status["missing"])
        self.assertIn("01_commercial.sql", status["sql_files"])
        self.assertEqual(status["database"], "FERRARA_COMMERCIAL")
        profile = Path(self.tmp.name) / "connections.toml"
        profile.write_text(
            "[aq_vc_reader]\naccount = OLD\nuser = VC\ntoken = vcSECRET\n\n"
            "[ferrara]\naccount = ORG-ACCOUNT\nuser = FERRARA_READER_USER\ntoken = patSECRETVALUE\n"
        )
        config = resolve_config(environ={}, env_file=Path("/no/such.env"), profile_file=profile)
        self.assertTrue(config["configured"])
        self.assertEqual(config["account"], "ORG-ACCOUNT")
        self.assertEqual(config["database"], "FERRARA_COMMERCIAL")
        self.assertEqual(config["source"], "connections.toml")
        public = connection_status(config)
        self.assertNotIn("patSECRETVALUE", str(public))
        ddl = "\n".join(ddl_statements(config))
        self.assertIn("CREATE DATABASE IF NOT EXISTS FERRARA_COMMERCIAL", ddl)
        self.assertNotIn("VC_RETAIL", ddl)
        self.assertNotIn("SNOWFLAKE_SAMPLE_DATA", ddl)
        self.assertIn("…", safe_error(RuntimeError("rejected patSECRETVALUE"), "patSECRETVALUE"))

    def test_voice_stays_dark_without_a_key(self):
        from app.voice import VoiceError, speak

        with self.assertRaises(VoiceError):
            speak("Net sales are a governed metric.", environ={}, env_file=Path("/no/such.env"))


class AuthTests(unittest.TestCase):
    def test_cookie_round_trip(self):
        session = authenticate("operator", "fc-demo")
        self.assertEqual(session["role"], "operator")
        self.assertIsNone(authenticate("operator", "nope"))
        header = issue_cookie(session).split(";", 1)[0]
        parsed = parse_cookie(header)
        self.assertEqual(parsed["username"], "operator")
        self.assertIsNone(parse_cookie("fc_demo=tampered.sig"))
