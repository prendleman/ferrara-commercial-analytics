"""Create the demo schema in Databricks SQL and copy the local book.

Reads the same credentials as the app. Prints row counts, never the token.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core import DB, connect, seed
from app.databricks_backend import connect as dbx_connect
from app.databricks_backend import connection_status, load_tables, resolve_config, safe_error


def main():
    config = resolve_config()
    status = connection_status(config)
    print(f"source={status['source'] or 'none'} catalog={status['catalog']} schema={status['schema']}")
    if not config["configured"]:
        print("Databricks is not configured. Missing:", ", ".join(status["missing"]))
        print("Set them in .env or ~/.databrickscfg, then rerun.")
        return 0
    seed(DB)
    local = connect(DB)
    remote = dbx_connect(config)
    try:
        cursor = remote.cursor()
        load_tables(cursor, local, config)
        for table in ("gold_invoice", "gold_activity", "public_context", "quarantine"):
            name = f"{config['schema']}.{table}" if not config.get("catalog") else f"{config['catalog']}.{config['schema']}.{table}"
            cursor.execute(f"SELECT COUNT(*) AS n FROM {name}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count}")
        print("Load finished.")
    except Exception as exc:
        print(safe_error(exc))
        return 1
    finally:
        local.close()
        remote.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
