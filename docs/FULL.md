# Ferrara Commercial Analytics

Synthetic interview demo. Public Ferrara brand names, fictional accounts, generated dollars. This is not Ferrara Candy Company, not Ferrero, and not a production warehouse.

Public site: https://ferrara.datasharkbi.com

Local: `python3 -m app.server` then http://127.0.0.1:8772

Source: https://github.com/prendleman/ferrara-commercial-analytics

The demo author is reachable at 773.354.3532 and therendle@gmail.com. That contact is not Ferrara.

Short walkthrough: `docs/DEMO_SCRIPT.md`.

## What a visitor can say out loud

The synthetic banner stays on. Charts come from `/api/metric`. The assistant is an approved-metric router, not a model. It refuses Nielsen, Circana, NIQ, syndicated share, SAP IBP forecasts, and MDM or S/4 claims. Genie is a real Databricks space titled Bakehouse Sales Starter Space. That space is not this book, and the app does not invent a Genie answer when the space is absent. A refusal is not sent to Genie.

Published rows and the synthetic book stay in different tables. Filed private-peer cells stay empty. Orangeburg is an announcement, not current output. Named campaigns have no published spend, so none is scored.

## Sign-in

| User | Password | Scope |
|---|---|---|
| `operator` | `fc-demo` | Full book |
| `acct-0001` | `fc-demo` | Lakeshore Grocery, `ACCT-0001` |

An account login still sees the published record. Supply and vendor scorecards return empty on an account login, because receipts have no account.

## Lanes

One app. There is no warehouse switch.

- SQLite keeps the audit log and the published record (`public_context`).
- Snowflake serves the commercial book when it is configured and the connection warms. A failed query falls back to the local book for that request and says so in the header.
- Databricks answers Genie only. Book reads do not use the Databricks SQL warehouse. Databricks Gold is not this book and is not loaded by the app.

On the public host, with both warehouses configured and Snowflake connected, the header reads:

> SQLite keeps the audit and the public record. Snowflake serves the commercial book. Databricks answers Genie only, and that space is not this book.

Credentials live in the process environment, then a gitignored `.env`, then a local profile (`~/.databrickscfg` or `~/.snowflake/connections.toml`, profile `ferrara`). The browser status never returns a token. Fly secrets are not in the image. Do not commit `.env`, a PAT, or `TUNNEL_TOKEN`.

`/api/slices` and `public_landscape` read SQLite even when the book is Snowflake, so a plant question cites the local published record rather than a stale warehouse copy.

## The book

Seed `random.Random(20261007)`. Window is 84 months, 1 October 2019 through 1 September 2026. A fiscal year is October through September, FY2020 through FY2026. Each later year steps the book by 3.5% (`1 + 0.035 * (fiscal - 2020)`). That step is the generator. It is not Ferrara’s reported 3.8%.

46 fictional accounts. The first 24 are the US set across Grocery, Mass, Convenience, Club, and Drug. `ACCT-0025` through `ACCT-0046` are Grocery or Club only, in Canada, Europe, Latin America, and Asia Pacific.

Regions and subregions:

| Region | Subregions |
|---|---|
| North America | Midwest, Northeast, South, West, Canada |
| Europe | United Kingdom, DACH, France, Benelux |
| Latin America | Brazil, Mexico, Southern Cone |
| Asia Pacific | Australia, Japan, Southeast Asia |

Families, with a list price and a COGS ratio used only by the generator: Nerds, Trolli, SweeTarts, Laffy Taffy, Butterfinger, Baby Ruth, Brach's, Lemonhead.

Trade rates are generation rules: Grocery 18%, Mass 22%, Convenience 12%, Club 29%, Drug 16%. Win rate and margin are different measures. Margin is net minus COGS. It is not operating profit.

Open opportunities dated before 1 April 2026 are forced to Lost, so pipeline age as of 30 September 2026 stays recent.

Full-book figures from this seed, served by Snowflake:

| | |
|---|---|
| Net sales | $923,988,481.45 |
| Win rate | 52.8% |
| Margin | 39.9% |
| Trade | about 24% of gross |
| Open pipeline | $4,639,544 |

Fiscal years, net sales: FY2020 $120,321,008.62, FY2021 $124,115,460.21, FY2022 $127,714,613.90, FY2023 $132,141,264.72, FY2024 $135,939,243.98, FY2025 $139,951,828.51, FY2026 $143,805,061.51.

Regions, net sales: North America $453,734,688.37, Europe $187,401,699.48, Latin America $141,649,466.94, Asia Pacific $141,202,626.66.

Europe FY2026 net sales in the UI: $29,037,218. Europe overview: $187,401,699.

Synthetic book P&L, full book, summed from the channel waterfall: Gross $1,215,961,318, Trade −$291,972,837, Net $923,988,481, COGS −$555,024,816, Margin $368,963,666. Operating profit is not published and is left blank.

Four planted bad invoices stay in quarantine and never reach Gold.

## Chips

Under the nav: channel, region, subregion, family, fiscal year. Unknown values return HTTP 400. A subregion that does not belong to the selected region is cleared.

Family filters invoices and opportunities. Activity has no brand, so activity counts stay on channel, region, subregion, and year. The assistant says `Not applied: family` in that case.

Changing a chip reloads the current tab. Changing tabs scrolls to the top. Lab and Catalog leave the chips idle.

## Screens

### Brief

The app opens here. One screen for the slice in view:

- Net sales, win rate, open pipeline, and trade rate, from `kpi_summary`.
- The first three accounts to call, and the largest open deal on the first, from `call_list`.
- The first Market plays for that same slice, from `/api/compete`.
- The supply miss: the family with the lowest fill, and the units ordered that did not arrive, from `supply_service`.
- The published lines that do not follow the chips.

On the full book the first three calls are Rx Lane East, Club Kanto, and Club Straits. The largest open deal on Rx Lane East is Trolli at Propose, $89,667 expected net. The supply miss is Trolli, fill 88.8%, 1,170,656 units short.

Europe moves the book. Net is $187,401,699. The first call is Club Alpine (DACH, $207,258 open pipeline, win rate 41.7% against a 49.1% median in that slice). Its largest open deal is Brach's at Qualify, $94,767 expected net. Then Club Scheldt and Club Thames. Trolli in Europe is still the miss, 242,467 units short. Orangeburg and the campaign count stay on the page unchanged.

An account login does not see a vendor scorecard. The brief says those rows stay on the operator book.

### Overview

Commercial funnel, net by channel, season index (January is 100), and the Halloween window. Halloween families are Nerds, Trolli, SweeTarts, and Laffy Taffy, in September and October.

### Commercial

Open pipeline by stage, win rate by channel, region, and subregion, activity conversion, gross to net, pipeline age from 30 September 2026, stage share, and activity mix.

Who to call sits above the account scorecard. The rule: open pipeline, and either a win rate below the median of this slice or no activity since 1 July 2026. Median is the lower middle of the win rates that exist. At most eight accounts, largest pipeline first. Each account shows up to three open deals, largest expected net first, honoring the family and year chips. This is the synthetic book. It is not a Ferrara call plan.

### Analytics

Net by family, fiscal year, margin by brand, trade rate by channel, the book price bridge, the channel waterfall, largest accounts, and region or subregion by channel.

Where each brand closes is win rate by family and channel (`close_by_family_channel`). The table shows each family’s weakest and strongest channel. Unscoped, Nerds wins 38.5% in Club (87 of 226) and 67.1% in Convenience. In Europe, Nerds is 44.4% in Club and 65.3% in Grocery. The sentence is this book, not a syndicated rank.

SKU rank sits inside each family. The heat map is net sales, not win rate.

### Supply

Fictional vendors only. They are not Ferrara’s suppliers. Ordered units match the invoice book. Score is 40% fill, 30% on-time, 20% accepted quality, 10% cost variance, lowest score first.

Full book: Gel & Bright 88.4 (fill 88, on time 81), Harbor Batch 91.4, Orchard Pectin 93.2, Cinder Sugar 96.2, Cocoa Lane 96.9, Northmill Co-Man 97.0, Carton North 97.8.

Concentration: Butterfinger 91% Cocoa Lane, Baby Ruth 88% Cocoa Lane, Trolli 74% Gel & Bright. This is not a forecast.

### Operations

Published facilities and campaigns come from `public_context`. The synthetic P&L under them follows the chips. Operating profit stays blank.

Opportunities on this tab mix two kinds of row, and the page says which is which. A published row is an announcement. A synthetic row is a gap in this book. The chips change only the synthetic rows.

### Market

One published table. Those rows do not share a denominator, so there is no share bar. Labeled guesses live only in `app/compete.py` and are never inserted into `public_context`.

Where to press builds plays from the approved win-rate, trade, and net queries for the slice: the weak channel, the strong channel, then region, subregion, and year when the slice has more than one of each. A single channel drops the second channel play. The year play says “largest year in this book” when nothing is sliced and “in this slice” when a chip is on.

Brand arenas start from that same close, then name a move and a hold. Holds that stay: Skittles share is not a target, Airheads and Mentos overlap is not a dollar target, do not out-scale Hershey, and the 20.1% sugar-confection share stays in 2023. On Market the arena fact can point at the guess band above it. The assistant cards do not repeat that “above” wording, because the band is not above them there.

Europe, as a check: Club wins 41.9% (193 of 461) and trade is 29.0% of gross. Grocery wins 62.9% (285 of 453). Benelux wins 44.8% (103 of 230). France wins 58.7% (132 of 225). FY2026 is the largest year in that slice.

### Assistant

Left is an illustrative inbox. It does not query the warehouse. Right is the router. The chips apply. The answer shows the route, the metric, the SQL, the parameters, and the rows. `call_list` renders tables, not a JSON dump of nested deals. `plays` renders play cards, then arena cards.

Example chips include the commercial questions, “who should we call,” “vendor scorecard,” “where should we press,” “where does nerds lose the close,” the public competitive set, a Nielsen refusal, and an IBP refusal.

Hear the answer speaks only text the server already produced. The key never goes to the browser. Voice is optional and is not required for the public book.

### Lab

Board brief chains funnel, trade, win rate, margin, and month. Golden evals grade the router with no page chips. Scope pin shows operator net above Lakeshore net. Compare sends a metric question to Genie and does not send a refusal or a plays question. The 90-day plan is a Ferrara-flavored plan, not a description of their stack.

Golden cases: funnel, pipeline, win rate, trade, margin, Halloween season, waterfall, season index, scorecard, pipeline age, family mix, SKU rank, net by channel, public competitive set, where to press, who to call, Orangeburg, vendor scorecard, where Nerds loses the close, Nielsen, IBP, MDM, and an empty question. The last four refuse. Evals must all pass.

### Catalog

Bronze, quarantine, Gold. The rejected invoices are visible and are not in the commercial metrics.

## Assistant routes worth remembering

Refusals win first. A question that says both “press” and “Nielsen” is refused.

Then, in order that matters:

- “where should we press,” “where to press,” “how do we compete,” “competitive play,” and “crush” return Market plays. They do not hit the public-landscape table.
- “lose the close,” “family by channel,” and “close by family” return `close_by_family_channel`, before a bare “Nerds” or “win rate” question can claim the sentence.
- “who should we call,” “who to call,” and “call list” return `call_list`, before “scorecard.”
- “vendor scorecard” returns the vendor metric, before “account scorecard.”
- “subregion” is matched before “region.”
- A plant or campaign question (Orangeburg, Bellwood, Forest Park, Linares, Big Game, Shaboozey, Andy Cohen, U.S. Soccer) returns the matching published rows, not the whole landscape, and not a synthetic dollar.

## Published record

Cite these. Do not turn them into a synthetic result, and do not average conflicting figures.

Ferrara FY2025 performance release, 23 February 2026:

- Net sales $2.2 billion, up 3.8%. That is not this book’s net.
- Capital expenditures more than $156 million.
- Workforce 8,600 in the financial narrative, and more than 9,400 in the boilerplate of the same release. Both are stored. They are not averaged.
- NERDS sales growth more than 9%, with no dollar sales in that release. An older $500 million figure is not reused as current.

Ferrara sugar confections, 20.1% stated category share, is 2023. It stays in that year.

Mars Inc. $54.6 billion is a whole-company prospectus figure, not a confectionery P&L for this table. Perfetti is above €4 billion, a company-stated floor, not a guess. Filed cells for Mars Wrigley confectionery, Haribo, and Perfetti revenue stay empty. Guesses, when shown, are labeled and live only on the compete panel. Haribo’s labeled guess is a point of €3.0 billion inside a €2.0–3.2 billion band. Mars Wrigley confectionery is a band with no point.

Facilities:

- Bellwood, Illinois. Purchase called out for FY2025. No purchase price in the release.
- Forest Park, Illinois. About 258,000 square feet, 7301 Harrison Street, lease through at least 2031. Forest Park Review, 19 June 2026.
- Linares, Nuevo León. New production line called out for FY2025. No dollar figure.
- Orangeburg County, South Carolina. Announced investment $675 million, 750,000 square feet, 1,000 jobs over 10 years. Announced 22 April 2026. First production lines expected in the first quarter of 2029. This is not current output and not a current P&L.
- Ferrara’s network is more than 30 facilities. That sentence is not a plant list. Bolingbrook is not in this table.

Campaigns, metric “Media spend,” value empty:

- NERDS Big Game 2025, “Wonderful World of NERDS,” Shaboozey, 4 February 2025.
- NERDS Big Game 2026, “Taste Buds,” Andy Cohen, 4 February 2026.
- U.S. Soccer packs, 2 March 2026, SweeTARTS, NERDS, and Trolli.

No spend and no sales result, so none is scored. The app does not invent ROAS, a plant P&L, or current Orangeburg output.

## Public pages

No login:

- `/` marketing page. Canonical host, contact, and a WebSite description that points at `/aeo`.
- `/login`
- `/aeo` answers written for citation, with FAQPage structured data.
- `/llms.txt` the same boundaries in plain text.
- `/robots.txt` allows `/`, `/aeo`, and `/llms.txt`, and disallows `/app` and `/api/`.

`/app` requires a session. The signed-in app is the book. The crawlable homepage does not claim to be ferrara.com and does not quote synthetic dollars as Ferrara sales.

## Hosting

Fly app `ferrara-commercial-analytics`, primary region `ord`, internal port 8772, one machine, auto-stop off. The image installs `snowflake-connector-python`. Databricks SQL is not used for book reads. Genie uses HTTPS.

Redeploy the local working tree:

```sh
~/.fly/bin/flyctl deploy --ha=false
```

`flyctl deploy` ships the working tree. It does not require a commit. Cloudflare rejects the default Python agent with 403, so check https://ferrara.datasharkbi.com with a browser user agent.

Do not print tokens. Do not start a row-by-row Databricks Gold load.

## Tests

```sh
python3 -m unittest tests.test_core -q
```

The suite covers the warehouse metrics, the public citation for Orangeburg, Europe press plays, the call list and its open deals, the family-by-channel close, auth scope, and a golden set with zero failures.

## What this demo will not do

- Treat synthetic net, margin, trade, win rate, or units short as Ferrara results.
- Put a Nielsen, Circana, or NIQ rank on the page.
- Score a campaign, print a plant P&L, or treat Orangeburg as already producing.
- Fill a filed private-peer revenue cell with a guess. Guesses stay labeled and outside `public_context`.
- Present Genie, or the Bakehouse space, as this book.
- Send a message, write back to a source system, or claim MDM or S/4.
