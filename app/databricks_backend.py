"""Databricks SQL wiring for the commercial demo.

Credentials resolve from the process environment, then the repo `.env`,
then `~/.databrickscfg`. The token is never returned to the browser.
Audit rows stay in local SQLite. Metric reads use whichever backend the
session selected.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql" / "databricks"

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

TABLES = {
    "bronze_activity": (
        ("activity_id", "STRING"),
        ("account_id", "STRING"),
        ("activity_date", "STRING"),
        ("activity_type", "STRING"),
        ("owner", "STRING"),
    ),
    "bronze_opportunity": (
        ("opp_id", "STRING"),
        ("account_id", "STRING"),
        ("family", "STRING"),
        ("stage", "STRING"),
        ("status", "STRING"),
        ("opened_date", "STRING"),
        ("expected_net_cents", "BIGINT"),
        ("source_activity_id", "STRING"),
    ),
    "bronze_invoice": (
        ("invoice_id", "STRING"),
        ("account_id", "STRING"),
        ("sku_id", "STRING"),
        ("opp_id", "STRING"),
        ("invoice_date", "STRING"),
        ("units", "BIGINT"),
        ("gross_cents", "BIGINT"),
        ("trade_cents", "BIGINT"),
        ("reject_reason", "STRING"),
    ),
    "quarantine": (
        ("invoice_id", "STRING"),
        ("reason", "STRING"),
    ),
    "gold_activity": (
        ("activity_id", "STRING"),
        ("account_id", "STRING"),
        ("account_name", "STRING"),
        ("channel", "STRING"),
        ("region", "STRING"),
        ("subregion", "STRING"),
        ("activity_date", "STRING"),
        ("activity_type", "STRING"),
        ("owner", "STRING"),
        ("opp_id", "STRING"),
        ("fiscal_year", "STRING"),
    ),
    "gold_opportunity": (
        ("opp_id", "STRING"),
        ("account_id", "STRING"),
        ("account_name", "STRING"),
        ("channel", "STRING"),
        ("region", "STRING"),
        ("subregion", "STRING"),
        ("family", "STRING"),
        ("stage", "STRING"),
        ("status", "STRING"),
        ("opened_date", "STRING"),
        ("expected_net_cents", "BIGINT"),
        ("source_activity_id", "STRING"),
        ("fiscal_year", "STRING"),
    ),
    "gold_invoice": (
        ("invoice_id", "STRING"),
        ("account_id", "STRING"),
        ("account_name", "STRING"),
        ("channel", "STRING"),
        ("region", "STRING"),
        ("subregion", "STRING"),
        ("sku_id", "STRING"),
        ("family", "STRING"),
        ("sku_name", "STRING"),
        ("opp_id", "STRING"),
        ("invoice_date", "STRING"),
        ("units", "BIGINT"),
        ("gross_cents", "BIGINT"),
        ("trade_cents", "BIGINT"),
        ("net_cents", "BIGINT"),
        ("cogs_cents", "BIGINT"),
        ("margin_cents", "BIGINT"),
        ("fiscal_year", "STRING"),
    ),
    "gold_receipt": (
        ("receipt_id", "STRING"),
        ("vendor_id", "STRING"),
        ("vendor_name", "STRING"),
        ("vendor_role", "STRING"),
        ("family", "STRING"),
        ("channel", "STRING"),
        ("region", "STRING"),
        ("subregion", "STRING"),
        ("fiscal_year", "STRING"),
        ("receipts", "BIGINT"),
        ("on_time_receipts", "BIGINT"),
        ("units_ordered", "BIGINT"),
        ("units_received", "BIGINT"),
        ("reject_units", "BIGINT"),
        ("cost_cents", "BIGINT"),
        ("contract_cents", "BIGINT"),
    ),
    "public_context": (
        ("group_name", "STRING"),
        ("entity", "STRING"),
        ("relationship", "STRING"),
        ("metric", "STRING"),
        ("value_num", "DOUBLE"),
        ("unit", "STRING"),
        ("period", "STRING"),
        ("scope_note", "STRING"),
        ("source", "STRING"),
        ("source_url", "STRING"),
    ),
}


class ConfigError(RuntimeError):
    def __init__(self, payload):
        super().__init__(payload.get("error") or "Databricks is not configured")
        self.payload = payload


def _parse_env_file(path: Path):
    values = {}
    if not path or not path.exists():
        return values
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _parse_profile(path: Path, profile: str):
    if not path or not path.exists():
        return {}
    current = None
    values = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            continue
        if current != profile or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lower()] = value.strip().strip('"').strip("'")
    return values


def _hostname(value: str):
    host = (value or "").strip()
    host = re.sub(r"^https?://", "", host).strip("/")
    return host


def _check_ident(name, label):
    if name and not IDENT.match(name):
        raise ConfigError({"error": f"{label} must be a plain identifier."})
    return name


def resolve_config(environ=None, env_file=None, profile_file=None):
    environ = os.environ if environ is None else environ
    if env_file is None:
        env_file = ROOT / ".env"
    if profile_file is None:
        profile_file = Path(
            environ.get("DATABRICKS_CONFIG_FILE") or Path.home() / ".databrickscfg"
        )
    file_values = _parse_env_file(Path(env_file)) if env_file else {}
    profile_name = environ.get("DATABRICKS_CONFIG_PROFILE") or file_values.get("DATABRICKS_CONFIG_PROFILE") or "DEFAULT"
    profile = _parse_profile(Path(profile_file), profile_name) if profile_file else {}

    def pick(*keys, profile_key=None):
        for key in keys:
            if environ.get(key):
                return environ[key], "environment"
            if file_values.get(key):
                return file_values[key], ".env"
        if profile_key and profile.get(profile_key):
            return profile[profile_key], "databrickscfg"
        return "", None

    host, host_source = pick("DATABRICKS_SERVER_HOSTNAME", profile_key="host")
    token, token_source = pick("DATABRICKS_TOKEN", profile_key="token")
    http_path, path_source = pick("DATABRICKS_HTTP_PATH")
    warehouse_id, warehouse_source = pick("DATABRICKS_WAREHOUSE_ID", profile_key="warehouse_id")
    if not http_path and warehouse_id:
        http_path = f"/sql/1.0/warehouses/{warehouse_id}"
        path_source = warehouse_source
    catalog, _ = pick("DATABRICKS_CATALOG")
    schema, _ = pick("DATABRICKS_SCHEMA")
    schema = schema or "ferrara_commercial"
    _check_ident(catalog, "DATABRICKS_CATALOG")
    _check_ident(schema, "DATABRICKS_SCHEMA")
    source = host_source or token_source or path_source
    missing = []
    if not host:
        missing.append("DATABRICKS_SERVER_HOSTNAME")
    if not token:
        missing.append("DATABRICKS_TOKEN")
    if not http_path:
        missing.append("DATABRICKS_HTTP_PATH or DATABRICKS_WAREHOUSE_ID")
    return {
        "configured": not missing,
        "missing": missing,
        "hostname": _hostname(host) or None,
        "http_path": http_path or None,
        "token": token or None,
        "catalog": catalog or None,
        "schema": schema,
        "source": source,
        "sql_files": sorted(path.name for path in SQL_DIR.glob("*.sql")) if SQL_DIR.exists() else [],
        "loader": "python3 scripts/databricks_load.py",
    }


def connection_status(config=None):
    config = config or resolve_config()
    return {
        "configured": config["configured"],
        "missing": config["missing"],
        "catalog": config["catalog"] or "(workspace default)",
        "schema": config["schema"],
        "hostname": config["hostname"],
        "http_path": config["http_path"],
        "source": config["source"],
        "sql_files": config["sql_files"],
        "loader": config["loader"],
    }


def genie_space_id(environ=None, env_file=None):
    if environ is None:
        environ = os.environ
    if environ.get("DATABRICKS_GENIE_SPACE_ID"):
        return environ["DATABRICKS_GENIE_SPACE_ID"].strip()
    if environ is not os.environ and env_file is None:
        return ""
    if env_file is None:
        env_file = ROOT / ".env"
    return (_parse_env_file(Path(env_file)).get("DATABRICKS_GENIE_SPACE_ID") or "").strip()


def genie_status(environ=None, env_file=None):
    space = genie_space_id(environ, env_file)
    if not space:
        return {
            "ok": False,
            "called": False,
            "error": "Databricks Genie is not configured. Set DATABRICKS_GENIE_SPACE_ID only after a real space exists. This demo will not invent a Genie answer.",
        }
    return {
        "ok": False,
        "called": False,
        "space_id": space,
        "error": "A Genie space id is configured. A compare sends the question. A status check does not.",
    }


def genie_answer_text(message):
    parts = []
    queries = []
    for attachment in message.get("attachments") or []:
        content = ((attachment.get("text") or {}).get("content") or "").strip()
        if content:
            parts.append(content)
        query = ((attachment.get("query") or {}).get("query") or "").strip()
        if query:
            queries.append(query)
    return "\n\n".join(parts), "\n\n".join(queries)


def _genie_http(method, url, token, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:180]
        raise RuntimeError(f"Genie HTTP {exc.code}: {detail}") from None
    return json.loads(raw or "{}")


def ask_genie(question, environ=None, env_file=None):
    """Send one question to a real Genie space. Never invents a reply."""
    space = genie_space_id(environ, env_file)
    if not space:
        return genie_status(environ, env_file)
    config = resolve_config(environ=environ, env_file=env_file)
    if not config["configured"]:
        return {
            "ok": False,
            "called": False,
            "space_id": space,
            "error": "Databricks is not configured, so Genie was not called.",
        }
    host = config["hostname"]
    token = config["token"]
    try:
        listing = _genie_http("GET", f"https://{host}/api/2.0/genie/spaces", token)
        title = ""
        for item in listing.get("spaces") or []:
            if item.get("space_id") == space:
                title = item.get("title") or ""
                break
        started = _genie_http(
            "POST",
            f"https://{host}/api/2.0/genie/spaces/{space}/start-conversation",
            token,
            {"content": (question or "").strip()[:500]},
        )
        message = started.get("message") if isinstance(started.get("message"), dict) else started
        conversation = started.get("conversation") if isinstance(started.get("conversation"), dict) else {}
        conversation_id = conversation.get("id") or started.get("conversation_id")
        message_id = message.get("id") or message.get("message_id") or started.get("message_id")
        if not conversation_id or not message_id:
            return {
                "ok": False,
                "called": True,
                "space_id": space,
                "space_title": title,
                "error": "Genie started a conversation without an id to poll.",
            }
        poll = f"https://{host}/api/2.0/genie/spaces/{space}/conversations/{conversation_id}/messages/{message_id}"
        status = (message.get("status") or "").upper()
        for _ in range(20):
            if status in {"COMPLETED", "FAILED", "CANCELLED"}:
                break
            time.sleep(2)
            payload = _genie_http("GET", poll, token)
            message = payload.get("message") if isinstance(payload.get("message"), dict) else payload
            status = (message.get("status") or "").upper()
        text, sql = genie_answer_text(message)
        if status != "COMPLETED" or not text:
            error = message.get("error") or f"Genie status {status or 'UNKNOWN'}."
            return {
                "ok": False,
                "called": True,
                "space_id": space,
                "space_title": title,
                "status": status,
                "error": str(error)[:240],
            }
        return {
            "ok": True,
            "called": True,
            "space_id": space,
            "space_title": title,
            "status": status,
            "answer": text,
            "sql": sql,
        }
    except Exception as exc:
        return {
            "ok": False,
            "called": True,
            "space_id": space,
            "error": safe_error(exc),
        }


def safe_error(exc):
    text = f"{type(exc).__name__}: {exc}"
    text = re.sub(r"dapi[A-Za-z0-9]+", "dapi…", text)
    return text[:240]


def qmark_to_pyformat(sql):
    return sql.replace("?", "%s")


def qualified(config, table):
    _check_ident(table, "table")
    schema = config["schema"]
    if config.get("catalog"):
        return f"{config['catalog']}.{schema}.{table}"
    return f"{schema}.{table}"


def ddl_statements(config):
    statements = []
    if config.get("catalog"):
        statements.append(f"CREATE CATALOG IF NOT EXISTS {config['catalog']}")
        statements.append(f"USE CATALOG {config['catalog']}")
    statements.append(f"CREATE SCHEMA IF NOT EXISTS {config['schema']}")
    statements.append(f"USE SCHEMA {config['schema']}")
    for table, columns in TABLES.items():
        body = ", ".join(f"{name} {kind}" for name, kind in columns)
        statements.append(f"CREATE TABLE IF NOT EXISTS {qualified(config, table)} ({body})")
    return statements


def connect(config=None):
    config = config or resolve_config()
    if not config["configured"]:
        raise ConfigError(
            {
                "error": "Databricks is not configured.",
                "missing": config["missing"],
                "loader": config["loader"],
            }
        )
    from databricks import sql

    return sql.connect(
        server_hostname=config["hostname"],
        http_path=config["http_path"],
        access_token=config["token"],
        use_inline_params=True,
    )


class Result:
    def __init__(self, rows):
        self._rows = rows
        self._index = 0

    def __iter__(self):
        return iter(self._rows)

    def fetchone(self):
        if self._index >= len(self._rows):
            return None
        row = self._rows[self._index]
        self._index += 1
        return row

    def fetchall(self):
        return list(self._rows)


class DatabricksStore:
    """One SQL-warehouse session. Metric SQL is the same text as SQLite, with ? rebound as %s."""

    def __init__(self, config=None):
        self.config = config or resolve_config()
        self._conn = None
        self._ready = False
        self._lock = threading.Lock()

    def _cursor(self):
        if not self.config["configured"]:
            raise ConfigError(
                {
                    "error": "Databricks is not configured.",
                    "missing": self.config["missing"],
                    "loader": self.config["loader"],
                }
            )
        with self._lock:
            if self._conn is None:
                self._conn = connect(self.config)
            cursor = self._conn.cursor()
            if not self._ready:
                if self.config.get("catalog"):
                    cursor.execute(f"USE CATALOG {self.config['catalog']}")
                cursor.execute(f"USE SCHEMA {self.config['schema']}")
                self._ready = True
            return cursor

    def execute(self, sql, params=()):
        cursor = self._cursor()
        adapted = qmark_to_pyformat(sql)
        cursor.execute(adapted, list(params) if params else None)
        if not cursor.description:
            return Result([])
        columns = [col[0].lower() for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return Result(rows)

    def commit(self):
        return None

    def close(self):
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
                self._ready = False


def load_tables(cursor, local_conn, config):
    for statement in ddl_statements(config):
        cursor.execute(statement)
    for table, columns in TABLES.items():
        names = [name for name, _kind in columns]
        target = qualified(config, table)
        cursor.execute(f"DELETE FROM {target}")
        if table == "public_context":
            from app.public_context import FACTS

            rows = list(FACTS)
        else:
            selected = ", ".join(names)
            rows = [tuple(row) for row in local_conn.execute(f"SELECT {selected} FROM {table}")]
        if not rows:
            continue
        width = len(names)
        columns = ", ".join(names)
        for start in range(0, len(rows), 200):
            batch = rows[start:start + 200]
            tuple_sql = "(" + ", ".join(["%s"] * width) + ")"
            values = ", ".join([tuple_sql] * len(batch))
            flat = [cell for row in batch for cell in row]
            cursor.execute(f"INSERT INTO {target} ({columns}) VALUES {values}", flat)
    return {table: "loaded" for table in TABLES}
