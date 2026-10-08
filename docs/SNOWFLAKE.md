# Snowflake wiring

The header switch can read the same metric SQL from Snowflake. The database is `FERRARA_COMMERCIAL`, schema `SERVING`. It holds the synthetic commercial book: bronze activity, opportunity, and invoice, quarantine, gold, and the public-context table.

This path does not scan `SNOWFLAKE_SAMPLE_DATA`. It does not create or read a Visual Comfort database.

Audit writes stay in SQLite. The browser status never includes the token.

## Credentials

First match wins for each field: process environment, then `.env`, then the `ferrara` profile in `~/.snowflake/connections.toml`.

Required: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, and `SNOWFLAKE_PAT` (or a password on the profile).

Optional, with these defaults:

| Field | Default |
|---|---|
| `SNOWFLAKE_ROLE` | `FERRARA_READER` |
| `SNOWFLAKE_WAREHOUSE` | `FERRARA_WH` |
| `SNOWFLAKE_DATABASE` | `FERRARA_COMMERCIAL` |
| `SNOWFLAKE_SCHEMA` | `SERVING` |

The reader role needs usage on the warehouse and on `FERRARA_COMMERCIAL.SERVING`. The loader needs rights to create that database, schema, and tables.

## Load

```sh
python3 -m pip install -r requirements-snowflake.txt
python3 scripts/snowflake_load.py
```

Then use the Snowflake control in the app header. The switch probes `SELECT 1` before the cookie sticks. If the tables are missing, run the loader first.

`sql/snowflake/01_commercial.sql` is the reference shape. The loader is the executable path.

The hosted site stays on SQLite until these values are set as secrets on purpose.
