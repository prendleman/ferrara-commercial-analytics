# Databricks wiring

The header switch chooses where metric SQL runs.

| Backend | What it reads | What it writes |
|---|---|---|
| SQLite | `data/demo.db` | Audit log in the same file |
| Databricks | The schema below, after the loader has copied the book | Audit log still in SQLite |

Both paths use the metric text in `app/core.py`. The Databricks driver binds `?` as `%s`. Account scope stays a parameter.

## Credentials

First match wins for each field: process environment, then `.env` (see `.env.example`), then `~/.databrickscfg` profile `DEFAULT`.

Required: server hostname, access token, and either `DATABRICKS_HTTP_PATH` or `DATABRICKS_WAREHOUSE_ID`. A `host` value may include `https://`. The warehouse id becomes `/sql/1.0/warehouses/<id>`.

`DATABRICKS_CATALOG` is optional. Leave it empty to create `ferrara_commercial` in the warehouse's current catalog. Set it only when the principal can create or use that catalog.

The browser status never includes the token.

## Load

```sh
python3 scripts/databricks_load.py
```

Then use the Databricks control in the app header. The switch probes `SELECT` through `USE SCHEMA` before it sticks. If the schema is missing, run the loader first.

A compare sends the question to Genie only when `DATABRICKS_GENIE_SPACE_ID` is set and the router accepted a metric. The reply is labeled with the space title. It is not treated as this book. A refusal is not sent.
