# Public host

The demo is a public synthetic Ferrara site on datasharkbi.

| Surface | Address |
|---|---|
| Hostname | https://ferrara.datasharkbi.com |
| Fly app | `ferrara-commercial-analytics` |
| GitHub | https://github.com/prendleman/ferrara-commercial-analytics |

`datasharkbi` is the Cloudflare zone, not a GitHub account. The repository is https://github.com/prendleman/ferrara-commercial-analytics.

Login stays the published demo pair (`operator` / `fc-demo`). Warehouse credentials are not deployed. The hosted switch stays on SQLite until a Databricks or Snowflake secret is set on that machine on purpose.

Redeploy after a code change:

```sh
git push
~/.fly/bin/flyctl deploy
```

The tunnel token is a Fly secret (`TUNNEL_TOKEN`). Do not commit it.
