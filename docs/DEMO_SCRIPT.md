# Eight-minute walkthrough

Local: `python3 -m app.server` → http://127.0.0.1:8772

## 0:00 Frame it

“This is a synthetic Ferrara-flavored commercial book. Public brand names, fictional accounts. It is the pattern I use for governed analytics: one definition from activity to invoice, and an assistant that can only call approved metrics.”

Point at the synthetic banner.

## 1:00 Sign in as operator

Password `fc-demo`. Full book.

## 1:30 Overview

Read net sales, gross margin (net minus COGS, not operating profit), trade rate, and open pipeline. The funnel is activities, opportunities, wins, and the incremental invoice dollars sitting inside total net. Channel bars are the same net, cut once.

## 3:00 Commercial

Pipeline by stage, win rate, activity conversion, gross-to-net realization. This is the commercial question: did CRM activity become an opportunity, did the opportunity win, and what did trade do to the invoice.

## 4:30 Analytics

Brand family, invoice month, margin, trade rate. September and October carry the Halloween families. Club should show the highest trade rate because the generator makes it so — say that the rate is a rule in the seed, then the metric just reports it.

## 5:30 Market

Open Market. Read Ferrara’s own FY2025 line: $2.2 billion net sales, up 3.8%. Then say the Hershey and Mondelēz numbers are real and not the same scope, so there is no share bar. Mars, Haribo, and Perfetti are named with no estimated sales. Point at the two workforce figures, 8,600 and more than 9,400, in the same release.

## 6:00 Scope

Log out. Sign in as `acct-0001`. Overview net sales drops to Lakeshore Grocery. Same screens, smaller book.

## 6:30 Assistant

Stay on the account login or return to operator.

1. Today: `trade spend by channel` → inbox story, no query.
2. Proposed: `margin by brand` → insight, SQL, rows.
3. Proposed: `what is our Nielsen share` → refusal, no SQL.
4. Proposed: `SAP IBP forecast for Nerds` → refusal.
5. Audit table shows the question, route, and scope.

If the account login is still active, point at `Params: ["ACCT-0001"]`.

## 7:30 Lab

Board brief chains the synthetic book. Run evals and read the pass rate. Scope pin shows operator net versus Lakeshore. Governed vs Genie must say Genie was not called. The header says Databricks SQL is staged until the three env vars exist.

## 8:30 Close

“The router is not a model. A model can sit in front later and choose a metric id. It does not get to invent share, a forecast, or a margin the warehouse did not compute. Catalog shows the rejected invoices never reach Gold.”
