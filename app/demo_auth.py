"""Synthetic demo users. Not Ferrara or Ferrero credentials."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

DEMO_PASSWORD = "fc-demo"
SECRET = os.environ.get("FC_DEMO_COOKIE_SECRET", "ferrara-commercial-demo-local-secret").encode()

ACCOUNTS = {
    "operator": {
        "account_id": None,
        "role": "operator",
        "label": "Commercial analyst (full book)",
    },
    "acct-0001": {
        "account_id": "ACCT-0001",
        "role": "account",
        "label": "Lakeshore Grocery only",
    },
}


def public_accounts():
    return [
        {
            "username": username,
            "label": meta["label"],
            "account_id": meta["account_id"],
            "role": meta["role"],
        }
        for username, meta in ACCOUNTS.items()
    ]


def authenticate(username, password):
    user = (username or "").strip().lower()
    if user not in ACCOUNTS or password != DEMO_PASSWORD:
        return None
    meta = ACCOUNTS[user]
    return {
        "username": user,
        "account_id": meta["account_id"],
        "role": meta["role"],
        "label": meta["label"],
        "iat": int(time.time()),
    }


def _sign(payload: bytes) -> str:
    return hmac.new(SECRET, payload, hashlib.sha256).hexdigest()


def issue_cookie(sess: dict) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(sess, separators=(",", ":")).encode()).decode()
    return f"fc_demo={raw}.{_sign(raw.encode())}; Path=/; HttpOnly; SameSite=Lax"


def clear_cookie() -> str:
    return "fc_demo=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"


def parse_cookie(header: str | None):
    if not header:
        return None
    for part in header.split(";"):
        part = part.strip()
        if not part.startswith("fc_demo="):
            continue
        value = part.split("=", 1)[1]
        if "." not in value:
            return None
        raw, sig = value.rsplit(".", 1)
        if not hmac.compare_digest(sig, _sign(raw.encode())):
            return None
        try:
            return json.loads(base64.urlsafe_b64decode(raw.encode()))
        except Exception:
            return None
    return None
