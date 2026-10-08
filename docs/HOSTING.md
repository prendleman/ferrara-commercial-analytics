# Public host

The demo is a public synthetic Ferrara site on datasharkbi.

| Surface | Address |
|---|---|
| Hostname | https://ferrara.datasharkbi.com |
| Answers for citation | https://ferrara.datasharkbi.com/aeo |
| Answer-engine brief | https://ferrara.datasharkbi.com/llms.txt |
| Fly app | `ferrara-commercial-analytics` |
| GitHub | https://github.com/prendleman/ferrara-commercial-analytics |

`datasharkbi` is the Cloudflare zone, not a GitHub account. The repository is https://github.com/prendleman/ferrara-commercial-analytics.

Login stays the published demo pair (`operator` / `fc-demo`). Snowflake serves the hosted commercial book. Databricks answers Genie only, and that space is not this book. The secrets live on the Fly app. They are not in the image.

Redeploy after a code change:

```sh
git push
~/.fly/bin/flyctl deploy
```

The tunnel token is a Fly secret (`TUNNEL_TOKEN`). Do not commit it.
