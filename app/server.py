"""Local HTTP app for the Ferrara commercial analytics demo."""
from __future__ import annotations

import argparse
import json
import threading
from datetime import date, datetime
from decimal import Decimal
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app import demo_auth
from app import lab
from app.databricks_backend import DatabricksStore
from app.databricks_backend import connection_status as databricks_status
from app.databricks_backend import resolve_config as databricks_config
from app.snowflake_backend import SnowflakeStore
from app.snowflake_backend import connection_status as snowflake_status
from app.snowflake_backend import resolve_config as snowflake_config
from app.snowflake_backend import safe_error as snowflake_safe_error
from app.voice import VoiceError, speak
from app.compete import compete_brief
from app.core import (
    DB,
    EXAMPLES,
    METRICS,
    SliceError,
    answer,
    catalog,
    connect,
    recent_audit,
    run_metric,
    seed,
    slice_options,
    today_answer,
)

STATIC = {
    "/": "marketing.html",
    "/login": "login.html",
    "/app": "index.html",
    "/aeo": "aeo.html",
    "/llms.txt": "llms.txt",
    "/robots.txt": "robots.txt",
    "/app.js": "app.js",
    "/marks.js": "marks.js",
    "/style.css": "style.css",
}
CTYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}
BACKEND_COOKIE = "fc_backend"


def _json_ready(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} is not JSON serializable")


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

    def _request_filters(self, body):
        return {key: body.get(key) or "" for key in ("channel", "region", "subregion", "family", "year")}

    def _backend_name(self):
        return "integrated"

    def _lane_note(self):
        if self.snowflake is None:
            book = "The local book is serving because Snowflake is not configured."
        elif getattr(Handler, "snowflake_ok", None) is False:
            book = "Snowflake did not connect, so the local book is serving."
        else:
            book = "Snowflake serves the commercial book."
        if self.databricks is None:
            genie = "Databricks is not configured, so Genie stays off."
        else:
            genie = "Databricks answers Genie only, and that space is not this book."
        return f"SQLite keeps the audit and the public record. {book} {genie}"

    def _tag(self, payload):
        payload["backend"] = self._backend_name()
        lane = getattr(self, "_lane", None) or {}
        if lane.get("served_by"):
            payload["served_by"] = lane["served_by"]
        if lane.get("note"):
            payload["lane_note"] = lane["note"]
        return payload

    def _integrated(self, fn):
        self._lane = {"served_by": "local"}
        with use_connection(self.store) as local:
            remote = self.snowflake
            if remote is None:
                self._lane["note"] = "Snowflake is not configured. The local book is serving."
                return fn(local, local)
            try:
                if not getattr(Handler, "snowflake_ok", False):
                    remote.execute("SELECT 1 AS ok")
                    Handler.snowflake_ok = True
            except Exception as exc:
                secret = remote.config.get("token") or remote.config.get("password")
                Handler.snowflake_ok = False
                self._lane["note"] = "Snowflake did not connect. The local book is serving. " + snowflake_safe_error(exc, secret)
                return fn(local, local)
            self._lane["served_by"] = "snowflake"
            try:
                return fn(remote, local)
            except Exception as exc:
                secret = remote.config.get("token") or remote.config.get("password")
                self._lane = {
                    "served_by": "local",
                    "note": "Snowflake did not serve this query. The local book did. " + snowflake_safe_error(exc, secret),
                }
                return fn(local, local)

    def _with_reads(self, fn):
        return self._integrated(fn)

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
        self._send(status, json.dumps(payload, default=_json_ready), "application/json", extra_headers)

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
                    "backend": "integrated",
                    "lane_note": self._lane_note(),
                }
            self._json(200, payload, [("Set-Cookie", f"{BACKEND_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")])
            return
        sess = self._session()
        if not sess:
            self._json(401, {"error": "Sign in required."})
            return
        account_id = sess.get("account_id")
        if path == "/api/catalog":
            def _catalog(read, _audit):
                body = catalog(read)
                self._json(200, self._tag(body))
            self._with_reads(_catalog)
            return
        if path == "/api/slices":
            with use_connection(self.store) as local:
                self._json(200, slice_options(local))
            return
        if path == "/api/metric":
            query = parse_qs(parsed.query)
            name = query.get("name", [""])[0]
            if name not in METRICS:
                self._json(400, {"error": "Unknown metric."})
                return
            filters = {key: query.get(key, [""])[0] for key in ("channel", "region", "subregion", "family", "year")}
            def _metric(read, audit):
                source = audit if name == "public_landscape" else read
                try:
                    rows = run_metric(source, name, account_id, filters)
                except SliceError:
                    self._json(400, {"error": "Unknown slicer value."})
                    return
                self._json(200, self._tag({
                    "metric": name,
                    "description": METRICS[name]["description"],
                    "rows": rows,
                    "filters": {key: value for key, value in filters.items() if value},
                }))
            self._with_reads(_metric)
            return
        if path == "/api/compete":
            query = parse_qs(parsed.query)
            filters = {key: query.get(key, [""])[0] for key in ("channel", "region", "subregion", "family", "year")}
            def _compete(read, audit):
                try:
                    body = compete_brief(read, audit, account_id, filters)
                except SliceError:
                    self._json(400, {"error": "Unknown slicer value."})
                    return
                self._json(200, self._tag(body))
            self._with_reads(_compete)
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
                try:
                    payload = answer(
                        read,
                        question,
                        sess["username"],
                        sess.get("account_id"),
                        audit_conn=audit,
                        filters=self._request_filters(body),
                    )
                except SliceError:
                    self._json(400, {"error": "Unknown slicer value."})
                    return
                self._json(200, self._tag(payload))
            self._with_reads(_ask)
            return
        if path == "/api/speak":
            question = (body.get("question") or "").strip()
            source = body.get("source") or "answer"

            def _speak(read, _audit):
                if source == "board":
                    text = lab.board_brief(read, sess.get("account_id"))["narrative"]
                else:
                    try:
                        payload = answer(
                            read,
                            question,
                            sess["username"],
                            sess.get("account_id"),
                            filters=self._request_filters(body),
                        )
                    except SliceError:
                        self._json(400, {"error": "Unknown slicer value."})
                        return
                    text = payload.get("answer") or ""
                try:
                    audio = speak(text)
                except VoiceError as exc:
                    self._json(409, {"error": str(exc)})
                    return
                self._send(200, audio, "audio/mpeg")

            self._with_reads(_speak)
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
                self._json(200, self._tag(payload))
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

    def _warm_snowflake():
        if Handler.snowflake is None:
            return
        try:
            Handler.snowflake.warm()
            Handler.snowflake_ok = True
        except Exception:
            Handler.snowflake_ok = False

    threading.Thread(target=_warm_snowflake, name="snowflake-warm", daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Ferrara commercial demo at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
