# Public context

Collected October 8, 2026 from pages Ferrara and the peer companies publish. This is not a scrape of a private portal, and it is not a syndicated share model.

## What went into the Market tab

- Ferrara FY2025 release: $2.2 billion net sales, +3.8%, more than $156 million of capital spending, NERDS sales up more than 9% with no dollar figure. https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance
- The same release says the workforce grew to 8,600 and, in the about section, more than 9,400. Both are stored.
- Ferrara FY2023 release: a stated 20.1% sugar-confectionery share. Not restated in the FY2025 release, so it stays labeled 2023.
- CTH Invest: €3.25 billion consolidated revenue for the year ended August 31, 2025. Ferrara is one company inside that group.
- 3F's Holding: €22.3 billion consolidated revenue for the same year. That is Ferrero plus CTH, not Ferrara.
- Hershey calendar 2025 consolidated net sales $11,692.6 million. North America Confectionery was $9,479.7 million of that.
- Mondelēz calendar 2025 net revenues $38,537 million, global snacking.
- Tootsie Roll calendar 2025 net product sales $724.675 million.
- Mars, Perfetti Van Melle, and Haribo are named as category peers. No revenue estimate is loaded.

## Site language used in the UI

Observed on https://www.ferrara.com/us/en: script wordmark, the line “Inspiring Sweetness,” and the color tokens in the public stylesheet (`#DC1A41`, `#F8F3F0`, `#FCE8EC`, `#333333`, `#424242`). The site’s font files (Sharp Sans, Centra No2, Cambon) are not copied. Outfit and Great Vibes stand in for the geometric sans and the script.

Homepage brands not in the synthetic book: Jelly Belly, Black Forest, Dori, Carambar, and Spree.

## Databricks

`sql/databricks/01_commercial.sql` is the warehouse shape. `python3 scripts/databricks_load.py` copies the local book only when `DATABRICKS_SERVER_HOSTNAME`, `DATABRICKS_HTTP_PATH`, and `DATABRICKS_TOKEN` are set. Genie is not called.
