# Eight-minute walkthrough

Full reference: `docs/FULL.md`. The app opens on Brief. Start there, then Overview.

Local: `python3 -m app.server` → http://127.0.0.1:8772

## 0:00 Frame it

“This is a synthetic Ferrara-flavored commercial book. Public brand names, fictional accounts. It is the pattern I use for governed analytics: one definition from activity to invoice, and an assistant that can only call approved metrics.”

Point at the synthetic banner.

## 1:00 Sign in as operator

Password `fc-demo`. Full book.

## 1:30 Overview

Read net sales, gross margin (net minus COGS, not operating profit), trade rate, and open pipeline. The book is seven fiscal years, October 2019 through September 2026. The funnel is activities, opportunities, wins, and the incremental invoice dollars sitting inside total net. Channel bars are the same net, cut once.

The chips under the nav are the slicers: channel, region, subregion, family, and fiscal year. They hit the same metric SQL as these charts. Region is North America, Europe, Latin America, and Asia Pacific. Subregion is the country or US area inside it. Family changes invoices and opportunities. Activity counts stay on channel, region, subregion, and year. The line under the session names the lanes: SQLite keeps the audit and the public record, Snowflake serves this book, and Databricks answers Genie only.

## 3:00 Commercial

Pipeline by stage, win rate, activity conversion, gross-to-net realization. This is the commercial question: did CRM activity become an opportunity, did the opportunity win, and what did trade do to the invoice.

## 4:30 Analytics

Brand family, invoice month, margin, trade rate. September and October carry the Halloween families. Club should show the highest trade rate because the generator makes it so — say that the rate is a rule in the seed, then the metric just reports it.

## 5:00 Supply

Open Supply. The vendors are fictional. Gel & Bright is the low score. Butterfinger is the concentrated family, mostly Cocoa Lane. Ordered units equal the invoice book, and the units short are what did not arrive. Say the weights: 40% fill, 30% on-time, 20% accepted quality, 10% cost. This is not a forecast and not S/4.

## 5:15 Operations

Open Operations. Bellwood, Forest Park, Linares, and the “more than 30 facilities” line are published. Orangeburg is the announced $675 million plant, with first lines expected in Q1 2029, so it is not current output. The three named campaigns have no published spend, so they are not scored. Opportunities lists Orangeburg as the published announcement, then the synthetic book’s weakest vendor and tightest family. Those two rows are not Ferrara opportunities. The P&L under that is the synthetic book. Operating profit stays blank.

## 5:30 Market

Open Market. The published record is one table. Read Ferrara’s own FY2025 line: $2.2 billion net sales, up 3.8%. Hershey and Mondelēz are real and a different denominator, so there is no share bar. Turn on Europe. Where to press names a European subregion, and the brand arenas name that same close. The published table stays the same.

The guess panel is labeled. Haribo is a synthetic point of €3.0 billion inside a €2.0–3.2 billion band. Mars Wrigley confectionery is a band with no point. Perfetti is the company-stated floor, above €4 billion, not a guess. The published table under that still has empty filed cells for Mars, Haribo, and Perfetti. Point at the two workforce figures, 8,600 and more than 9,400, in the same release.

## 6:00 Scope

Log out. Sign in as `acct-0001`. Overview net sales drops to Lakeshore Grocery. Same screens, smaller book. Supply is empty on an account login.

## 6:30 Assistant

Stay on the account login or return to operator.

1. Today: `trade spend by channel` → inbox story, no query.
2. Proposed: `margin by brand` → insight, SQL, rows.
3. Select Club, then ask `win rate`. The answer shows `Slice: channel: Club`, and the params include Club. Clear the chip and the same question is the full book. Family on an activity question shows `Not applied: family`.
4. `what is our Nielsen share` refuses, with no SQL, even while a chip is on.
5. `SAP IBP forecast for Nerds` refuses.
6. Audit table shows the question, route, and scope.

If the account login is still active, point at `Params` including `ACCT-0001`.

## 7:30 Lab

Board brief chains the synthetic book. Run evals and read the pass rate. Evals do not inherit the page slicers. Scope pin shows operator net versus Lakeshore. A refusal is not sent to Genie. A metric question is. Genie’s space is Bakehouse, and the reply is not this book.

## 8:30 Close

“The router is not a model. A model can sit in front later and choose a metric id. It does not get to invent share, a forecast, or a margin the warehouse did not compute. Catalog shows the rejected invoices never reach Gold.”
