# Public host

The demo is a public synthetic site, same pattern as Visual Comfort on datasharkbi.

| Surface | Address |
|---|---|
| Hostname | https://ferrara.datasharkbi.com |
| Fly app | `ferrara-commercial-analytics` |
| GitHub | https://github.com/prendleman/ferrara-commercial-analytics |

`datasharkbi` is the Cloudflare zone, not a GitHub account. The repository lives on the `prendleman` account, next to `vc-retail-analytics`.

Login stays the published demo pair (`operator` / `fc-demo`). Databricks credentials are not deployed. The hosted switch stays on SQLite until a warehouse is configured on that machine.

Redeploy after a code change:

```sh
git push
~/.fly/bin/flyctl deploy
```

The tunnel token is a Fly secret (`TUNNEL_TOKEN`). Do not commit it.
