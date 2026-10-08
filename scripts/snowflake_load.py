"""Create FERRARA_COMMERCIAL in Snowflake and copy the local book.

Reads the same credentials as the app. Prints row counts, never the token.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core import DB, connect, seed
from app.snowflake_backend import connect as sf_connect
from app.snowflake_backend import connection_status, load_tables, resolve_config, safe_error


def main():
    config = resolve_config()
    status = connection_status(config)
    print(
        f"source={status['source'] or 'none'} database={status['database']} "
        f"schema={status['schema']} warehouse={status['warehouse']}"
    )
    if not config["configured"]:
        print("Snowflake is not configured. Missing:", ", ".join(status["missing"]))
        print("Set them in .env or ~/.snowflake/connections.toml profile ferrara, then rerun.")
        return 0
    seed(DB)
    local = connect(DB)
    remote = sf_connect(config)
    try:
        cursor = remote.cursor()
        load_tables(cursor, local, config)
        for table in ("gold_invoice", "gold_activity", "public_context", "quarantine"):
            cursor.execute(f"SELECT COUNT(*) AS n FROM {config['database']}.{config['schema']}.{table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count}")
        print("Load finished.")
    except Exception as exc:
        print(safe_error(exc, config.get("token") or config.get("password")))
        return 1
    finally:
        local.close()
        remote.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
