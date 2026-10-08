# Ferrara Commercial Analytics

Synthetic interview demo for a Ferrara-flavored commercial book: CRM activity, opportunity, invoice, trade, and margin, plus a governed assistant.

Public Ferrara brand names are flavor only. Accounts, people, and dollars are generated. This is not Ferrara or Ferrero production data, and it is not commissioned client work.

Sibling of `vc-retail-analytics`. Local SQLite only. Python 3.9+ standard library.

## Start

```sh
python3 -m app.server
```

Open http://127.0.0.1:8772

Public site: https://ferrara.datasharkbi.com

Source: https://github.com/prendleman/ferrara-commercial-analytics

| User | Password | Scope |
|---|---|---|
| `operator` | `fc-demo` | Full book |
| `acct-0001` | `fc-demo` | Lakeshore Grocery only |

## What it shows

- One definition of net sales from Bronze invoices through Gold
- Funnel from activity to opportunity to won to incremental invoice dollars
- Channel, brand, region, month, trade rate, and margin cuts that reconcile
- Account scope on every commercial metric
- Proposed assistant: approved-metric router with SQL, parameters, and an audit row
- Refusals for syndicated share, demand-planning forecasts, and MDM / S/4 claims
- Market tab: published Ferrara, affiliate, and peer figures with sources. Private peers have no invented revenue
- Lab: board brief, golden evals, scope pin, governed-vs-Genie compare, 90-day plan
- Header switch runs the same metric SQL on SQLite or Databricks. See `docs/DATABRICKS.md`. Audit stays local. Credentials come from the environment, `.env`, or `~/.databrickscfg`
- Today panel: an illustrative analyst inbox, not a claim about Ferrara’s internal tools

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Walkthrough: `docs/DEMO_SCRIPT.md`.
