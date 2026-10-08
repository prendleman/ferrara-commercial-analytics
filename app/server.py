"""Local HTTP app for the Ferrara commercial analytics demo."""
from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app import demo_auth
from app import lab
from app.databricks_backend import ConfigError as DatabricksConfigError
from app.databricks_backend import DatabricksStore
from app.databricks_backend import connection_status as databricks_status
from app.databricks_backend import resolve_config as databricks_config
from app.databricks_backend import safe_error as databricks_safe_error
from app.snowflake_backend import ConfigError as SnowflakeConfigError
from app.snowflake_backend import SnowflakeStore
from app.snowflake_backend import connection_status as snowflake_status
from app.snowflake_backend import resolve_config as snowflake_config
from app.snowflake_backend import safe_error as snowflake_safe_error
from app.core import (
    DB,
    EXAMPLES,
    METRICS,
    answer,
    catalog,
    connect,
    recent_audit,
    run_metric,
    seed,
    today_answer,
)

STATIC = {
    "/": "marketing.html",
    "/login": "login.html",
    "/app": "index.html",
    "/app.js": "app.js",
    "/style.css": "style.css",
}
CTYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}
BACKEND_COOKIE = "fc_backend"


class Store:
    def __init__(self, path):
        self.path = path

    def connection(self):
        return connect(self.path)


@contextmanager
def use_connection(store):
    conn = store.connection()
    try:
        yield conn
    finally:
        conn.close()


class Handler(BaseHTTPRequestHandler):
    store = None
    databricks = None
    snowflake = None

    def _remote(self, name):
        if name == "databricks":
            return self.databricks
        if name == "snowflake":
            return self.snowflake
        return None

    def _backend_name(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            key, _, value = part.strip().partition("=")
            if key == BACKEND_COOKIE and value in ("local", "databricks", "snowflake"):
                if value != "local" and self._remote(value) is None:
                    return "local"
                return value
        return "local"

    def _backend_cookie(self, name):
        return f"{BACKEND_COOKIE}={name}; Path=/; HttpOnly; SameSite=Lax"

    def _with_reads(self, fn):
        backend = self._backend_name()
        remote = self._remote(backend)
        try:
            if remote is None:
                with use_connection(self.store) as conn:
                    return fn(conn, conn)
            with use_connection(self.store) as audit:
                return fn(remote, audit)
        except (DatabricksConfigError, SnowflakeConfigError) as exc:
            self._json(409, exc.payload)
            return None
        except Exception as exc:
            cleaner = snowflake_safe_error if backend == "snowflake" else databricks_safe_error
            secret = None
            if backend == "snowflake" and self.snowflake is not None:
                secret = self.snowflake.config.get("token") or self.snowflake.config.get("password")
            self._json(502, {"error": cleaner(exc, secret) if backend == "snowflake" else cleaner(exc), "backend": backend})
            return None

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def _session(self):
        return demo_auth.parse_cookie(self.headers.get("Cookie"))

    def _send(self, status, body, content_type, extra_headers=None):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for key, value in extra_headers or []:
            self.send_header(key, value)
        self.end_headers()
        if not getattr(self, "_head_only", False):
            self.wfile.write(data)

    def do_HEAD(self):
        self._head_only = True
        try:
            self.do_GET()
        finally:
            self._head_only = False

    def _json(self, status, payload, extra_headers=None):
        self._send(status, json.dumps(payload), "application/json", extra_headers)

    def _redirect(self, location, extra_headers=None):
        self.send_response(302)
        self.send_header("Location", location)
        for key, value in extra_headers or []:
            self.send_header(key, value)
        self.end_headers()

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > 8000:
            return None
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return None

    def _static(self, name):
        path = DB.parent.parent / "app" / "static" / name
        if not path.exists():
            self._send(404, "missing", "text/plain; charset=utf-8")
            return
        ext = path.suffix
        self._send(200, path.read_bytes(), CTYPES.get(ext, "application/octet-stream"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in STATIC:
            if path == "/app" and not self._session():
                self._redirect("/login")
                return
            self._static(STATIC[path])
            return
        if path == "/api/session":
            sess = self._session()
            payload = {"user": None}
            if sess:
                payload = {
                    "user": sess,
                    "examples": EXAMPLES,
                    "databricks": databricks_status(),
                    "snowflake": snowflake_status(),
                    "backend": self._backend_name(),
                }
            self._json(200, payload)
            return
        sess = self._session()
        if not sess:
            self._json(401, {"error": "Sign in required."})
            return
        account_id = sess.get("account_id")
        if path == "/api/catalog":
            def _catalog(read, _audit):
                body = catalog(read)
                body["backend"] = self._backend_name()
                self._json(200, body)
            self._with_reads(_catalog)
            return
        if path == "/api/metric":
            name = parse_qs(parsed.query).get("name", [""])[0]
            if name not in METRICS:
                self._json(400, {"error": "Unknown metric."})
                return
            def _metric(read, _audit):
                rows = run_metric(read, name, account_id)
                self._json(200, {
                    "metric": name,
                    "description": METRICS[name]["description"],
                    "rows": rows,
                    "backend": self._backend_name(),
                })
            self._with_reads(_metric)
            return
        if path == "/api/lab/plan":
            self._json(200, lab.plan())
            return
        if path == "/api/audit":
            with use_connection(self.store) as conn:
                username = None if sess.get("role") == "operator" else sess["username"]
                rows = recent_audit(conn, username)
            self._json(200, {"rows": rows})
            return
        self._json(404, {"error": "Not found."})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()
        if body is None:
            self._json(400, {"error": "Invalid JSON."})
            return
        if path == "/api/login":
            sess = demo_auth.authenticate(body.get("username"), body.get("password"))
            if not sess:
                self._json(401, {"error": "Unknown demo user or password."})
                return
            self._json(200, {"user": sess}, [("Set-Cookie", demo_auth.issue_cookie(sess))])
            return
        if path == "/api/logout":
            self._json(200, {"ok": True}, [("Set-Cookie", demo_auth.clear_cookie())])
            return
        sess = self._session()
        if not sess:
            self._json(401, {"error": "Sign in required."})
            return
        if path == "/api/ask":
            question = body.get("question") or ""
            mode = body.get("mode") or "proposed"
            if mode == "today":
                self._json(200, {"route": "today", "answer": today_answer(question), "engine": "illustrative inbox"})
                return
            def _ask(read, audit):
                payload = answer(read, question, sess["username"], sess.get("account_id"), audit_conn=audit)
                payload["backend"] = self._backend_name()
                self._json(200, payload)
            self._with_reads(_ask)
            return
        if path == "/api/backend":
            choice = body.get("backend")
            if choice not in ("local", "databricks", "snowflake"):
                self._json(400, {"error": "Backend must be local, databricks, or snowflake."})
                return
            if choice in ("databricks", "snowflake"):
                remote = self._remote(choice)
                status = databricks_status() if choice == "databricks" else snowflake_status()
                label = "Databricks" if choice == "databricks" else "Snowflake"
                if remote is None:
                    self._json(409, {
                        "error": f"{label} is not configured.",
                        "missing": status["missing"],
                        "loader": status["loader"],
                    })
                    return
                try:
                    remote.execute("SELECT 1 AS ok")
                except Exception as exc:
                    if choice == "snowflake":
                        secret = remote.config.get("token") or remote.config.get("password")
                        message = snowflake_safe_error(exc, secret)
                    else:
                        message = databricks_safe_error(exc)
                    self._json(502, {"error": message, "backend": choice})
                    return
            self._json(200, {"backend": choice}, [("Set-Cookie", self._backend_cookie(choice))])
            return
        if path in {"/api/lab/board", "/api/lab/evals", "/api/lab/compare", "/api/lab/scope"}:
            def _lab(read, audit):
                if path.endswith("/board"):
                    payload = lab.board_brief(read, sess.get("account_id"))
                elif path.endswith("/evals"):
                    payload = lab.run_evals(read, sess["username"], sess.get("account_id"), audit_conn=audit)
                elif path.endswith("/compare"):
                    payload = lab.compare(
                        read,
                        body.get("question") or "margin by brand",
                        sess["username"],
                        sess.get("account_id"),
                        audit_conn=audit,
                    )
                else:
                    payload = lab.scope_pin(read, body.get("metric") or "net_by_channel")
                payload["backend"] = self._backend_name()
                self._json(200, payload)
            self._with_reads(_lab)
            return
        self._json(404, {"error": "Not found."})


def main():
    parser = argparse.ArgumentParser(description="Ferrara commercial analytics demo")
    parser.add_argument("--port", type=int, default=8772)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    seed(DB)
    Handler.store = Store(DB)
    dbx = databricks_config()
    snow = snowflake_config()
    Handler.databricks = DatabricksStore(dbx) if dbx["configured"] else None
    Handler.snowflake = SnowflakeStore(snow) if snow["configured"] else None
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Ferrara commercial demo at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
