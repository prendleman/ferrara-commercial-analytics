"""Snowflake wiring for the Ferrara commercial book.

Credentials resolve from the process environment, then the repo `.env`,
then the `ferrara` profile in `~/.snowflake/connections.toml`.
The token is never returned to the browser. This module does not read
SNOWFLAKE_SAMPLE_DATA and does not create Visual Comfort objects.
Audit rows stay in local SQLite.
"""
from __future__ import annotations

import os
import re
import threading
from pathlib import Path

from app.databricks_backend import TABLES

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql" / "snowflake"
IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TYPE_MAP = {"STRING": "VARCHAR", "BIGINT": "NUMBER", "DOUBLE": "FLOAT"}
PROFILE = "ferrara"


class ConfigError(RuntimeError):
    def __init__(self, payload):
        super().__init__(payload.get("error") or "Snowflake is not configured")
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
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            continue
        if current != profile or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().lower()] = value.strip().strip('"').strip("'")
    return values


def _check_ident(name, label):
    if name and not IDENT.match(name):
        raise ConfigError({"error": f"{label} must be a plain identifier."})
    return name


def resolve_config(environ=None, env_file=None, profile_file=None):
    environ = os.environ if environ is None else environ
    if env_file is None:
        env_file = ROOT / ".env"
    if profile_file is None:
        profile_file = Path(environ.get("SNOWFLAKE_CONNECTIONS_FILE") or Path.home() / ".snowflake" / "connections.toml")
    file_values = _parse_env_file(Path(env_file)) if env_file else {}
    profile = _parse_profile(Path(profile_file), PROFILE) if profile_file else {}

    def pick(env_key, profile_key):
        if environ.get(env_key):
            return environ[env_key], "environment"
        if file_values.get(env_key):
            return file_values[env_key], ".env"
        if profile.get(profile_key):
            return profile[profile_key], "connections.toml"
        return "", None

    account, account_source = pick("SNOWFLAKE_ACCOUNT", "account")
    user, user_source = pick("SNOWFLAKE_USER", "user")
    token, token_source = pick("SNOWFLAKE_PAT", "token")
    password, _password_source = pick("SNOWFLAKE_PASSWORD", "password")
    role, _ = pick("SNOWFLAKE_ROLE", "role")
    warehouse, _ = pick("SNOWFLAKE_WAREHOUSE", "warehouse")
    database, _ = pick("SNOWFLAKE_DATABASE", "database")
    schema, _ = pick("SNOWFLAKE_SCHEMA", "schema")
    role = role or "FERRARA_READER"
    warehouse = warehouse or "FERRARA_WH"
    database = database or "FERRARA_COMMERCIAL"
    schema = schema or "SERVING"
    for label, value in (
        ("SNOWFLAKE_ROLE", role),
        ("SNOWFLAKE_WAREHOUSE", warehouse),
        ("SNOWFLAKE_DATABASE", database),
        ("SNOWFLAKE_SCHEMA", schema),
    ):
        _check_ident(value, label)
    source = account_source or user_source or token_source
    missing = []
    if not account:
        missing.append("SNOWFLAKE_ACCOUNT")
    if not user:
        missing.append("SNOWFLAKE_USER")
    if not token and not password:
        missing.append("SNOWFLAKE_PAT")
    return {
        "configured": not missing,
        "missing": missing,
        "account": account or None,
        "user": user or None,
        "token": token or None,
        "password": password or None,
        "role": role,
        "warehouse": warehouse,
        "database": database,
        "schema": schema,
        "source": source,
        "sql_files": sorted(path.name for path in SQL_DIR.glob("*.sql")) if SQL_DIR.exists() else [],
        "loader": "python3 scripts/snowflake_load.py",
    }


def connection_status(config=None):
    config = config or resolve_config()
    return {
        "configured": config["configured"],
        "missing": config["missing"],
        "account": config["account"],
        "user": config["user"],
        "role": config["role"],
        "warehouse": config["warehouse"],
        "database": config["database"],
        "schema": config["schema"],
        "source": config["source"],
        "sql_files": config["sql_files"],
        "loader": config["loader"],
    }


def safe_error(exc, secret=None):
    text = f"{type(exc).__name__}: {exc}"
    if secret:
        text = text.replace(str(secret), "…")
    return text[:240]


def qmark_to_pyformat(sql):
    return sql.replace("?", "%s")


def qualified(config, table):
    _check_ident(table, "table")
    return f"{config['database']}.{config['schema']}.{table}"


def ddl_statements(config):
    statements = [
        f"CREATE DATABASE IF NOT EXISTS {config['database']}",
        f"CREATE SCHEMA IF NOT EXISTS {config['database']}.{config['schema']}",
    ]
    for table, columns in TABLES.items():
        body = ", ".join(f"{name} {TYPE_MAP[kind]}" for name, kind in columns)
        statements.append(f"DROP TABLE IF EXISTS {qualified(config, table)}")
        statements.append(f"CREATE TABLE {qualified(config, table)} ({body})")
    return statements


def connect(config=None):
    config = config or resolve_config()
    if not config["configured"]:
        raise ConfigError(
            {
                "error": "Snowflake is not configured.",
                "missing": config["missing"],
                "loader": config["loader"],
            }
        )
    import snowflake.connector

    kwargs = {
        "account": config["account"],
        "user": config["user"],
        "role": config["role"],
        "warehouse": config["warehouse"],
        "session_parameters": {"QUERY_TAG": "ferrara-commercial-demo"},
        "client_session_keep_alive": True,
        "login_timeout": 20,
        "network_timeout": 180,
    }
    if config.get("token"):
        kwargs["authenticator"] = "PROGRAMMATIC_ACCESS_TOKEN"
        kwargs["token"] = config["token"]
    else:
        kwargs["password"] = config["password"]
    return snowflake.connector.connect(**kwargs)


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


POOL_SIZE = 4


class SnowflakeStore:
    """A small pool of Snowflake sessions. Metric SQL matches SQLite, with ? rebound as %s."""

    def __init__(self, config=None):
        self.config = config or resolve_config()
        self._idle = []
        self._lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(POOL_SIZE)

    def _open(self):
        if not self.config["configured"]:
            raise ConfigError(
                {
                    "error": "Snowflake is not configured.",
                    "missing": self.config["missing"],
                    "loader": self.config["loader"],
                }
            )
        conn = connect(self.config)
        cursor = conn.cursor()
        try:
            cursor.execute(f"USE DATABASE {self.config['database']}")
            cursor.execute(f"USE SCHEMA {self.config['schema']}")
        finally:
            cursor.close()
        return conn

    def warm(self, count=POOL_SIZE):
        opened = []
        try:
            for _ in range(count):
                opened.append(self._open())
        except Exception:
            for conn in opened:
                try:
                    conn.close()
                except Exception:
                    pass
            raise
        for conn in opened:
            self._release(conn)

    def _borrow(self):
        with self._lock:
            if self._idle:
                return self._idle.pop()
        return self._open()

    def _release(self, conn):
        with self._lock:
            if len(self._idle) < POOL_SIZE:
                self._idle.append(conn)
                return
        conn.close()

    def execute(self, sql, params=()):
        self._slots.acquire()
        conn = None
        try:
            conn = self._borrow()
            cursor = conn.cursor()
            try:
                cursor.execute(qmark_to_pyformat(sql), list(params) if params else None)
                if not cursor.description:
                    return Result([])
                columns = [col[0].lower() for col in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return Result(rows)
            finally:
                cursor.close()
        except Exception:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
            raise
        finally:
            if conn is not None:
                self._release(conn)
            self._slots.release()

    def commit(self):
        return None

    def close(self):
        with self._lock:
            idle = self._idle
            self._idle = []
        for conn in idle:
            try:
                conn.close()
            except Exception:
                pass


def load_table(cursor, local_conn, config, table):
    """Create and fill one serving table. Other tables stay in place."""
    columns = TABLES[table]
    names = [name for name, _kind in columns]
    body = ", ".join(f"{name} {TYPE_MAP[kind]}" for name, kind in columns)
    target = qualified(config, table)
    cursor.execute(f"CREATE OR REPLACE TABLE {target} ({body})")
    selected = ", ".join(names)
    rows = [tuple(row) for row in local_conn.execute(f"SELECT {selected} FROM {table}")]
    if not rows:
        return 0
    placeholders = ", ".join(["%s"] * len(names))
    statement = f"INSERT INTO {target} ({', '.join(names)}) VALUES ({placeholders})"
    for start in range(0, len(rows), 2000):
        cursor.executemany(statement, rows[start:start + 2000])
    return len(rows)


def load_tables(cursor, local_conn, config):
    for statement in ddl_statements(config):
        cursor.execute(statement)
    cursor.execute(f"USE DATABASE {config['database']}")
    cursor.execute(f"USE SCHEMA {config['schema']}")
    for table, columns in TABLES.items():
        names = [name for name, _kind in columns]
        target = qualified(config, table)
        cursor.execute(f"DELETE FROM {target}")
        if table == "public_context":
            from app.public_context import FACTS

            rows = [tuple(row) for row in FACTS]
        else:
            selected = ", ".join(names)
            rows = [tuple(row) for row in local_conn.execute(f"SELECT {selected} FROM {table}")]
        if not rows:
            continue
        placeholders = ", ".join(["%s"] * len(names))
        statement = f"INSERT INTO {target} ({', '.join(names)}) VALUES ({placeholders})"
        for start in range(0, len(rows), 2000):
            cursor.executemany(statement, rows[start:start + 2000])
    return {table: "loaded" for table in TABLES}
