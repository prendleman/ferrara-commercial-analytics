"""Published figures and named peers. Not the synthetic commercial book.

Every row names the page it came from. Private companies stay on the list
with no invented revenue. Dollar scopes are not comparable, so this table
is not a share model.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

# group, entity, relationship, metric, value_num, unit, period, scope_note, source, source_url
FACTS = [
    (
        "Ferrara published",
        "Ferrara Candy Company",
        "Subject of this demo's flavor",
        "Net sales",
        2200,
        "USD millions",
        "FY2025 (Sep 2024–Aug 2025)",
        "Company release says $2.2 billion, up 3.8% versus the prior year. Not the synthetic book.",
        "Ferrara FY2025 performance release, Chicago, Feb 23, 2026",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Ferrara published",
        "Ferrara Candy Company",
        "Subject of this demo's flavor",
        "Capital expenditures",
        156,
        "USD millions, more than",
        "FY2025",
        "Release says continued investments of more than $156 million.",
        "Ferrara FY2025 performance release",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Ferrara published",
        "Ferrara Candy Company",
        "Subject of this demo's flavor",
        "Workforce, financial narrative",
        8600,
        "people",
        "FY2025 vs 8,000 in 2023",
        "Same release later says more than 9,400 employees in the boilerplate. Both figures are stored. They are not reconciled here.",
        "Ferrara FY2025 performance release",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Ferrara published",
        "Ferrara Candy Company",
        "Subject of this demo's flavor",
        "Workforce, about boilerplate",
        9400,
        "people, more than",
        "Stated on the FY2025 release about section",
        "Conflicts with the 8,600 figure in the same document. Shown as a source conflict, not averaged.",
        "Ferrara FY2025 performance release, about section",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Ferrara published",
        "NERDS",
        "Brand called out by the company",
        "Sales growth",
        9,
        "percent, more than",
        "FY2025 vs prior year",
        "No dollar sales figure in the FY2025 release. A FY2023 release cited $500 million; that older dollar figure is not reused as current.",
        "Ferrara FY2025 performance release",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Ferrara published",
        "Ferrara sugar confections",
        "Historical company claim",
        "Stated category share",
        20.1,
        "percent",
        "Claimed for 2023, not restated in the FY2025 release",
        "Not a Nielsen or Circana extract in this warehouse. The assistant still refuses a current syndicated share.",
        "Ferrara FY2023 performance release",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2023-performance",
    ),
    (
        "Affiliate structure",
        "CTH Invest Group",
        "Ferrero-affiliated holding company that includes Ferrara",
        "Consolidated revenue",
        3250,
        "EUR millions",
        "Year ended Aug 31, 2025",
        "Includes Ferrara, Fine Biscuits, and Fox's Burton's. Not Ferrara-only sales.",
        "CTH Invest Group release via PR Newswire, Feb 25, 2026",
        "https://www.prnewswire.co.uk/news-releases/cth-invest-group-reports-consolidated-financial-statements-for-the-20242025-financial-year-302694968.html",
    ),
    (
        "Affiliate structure",
        "3F's Holding",
        "Ultimate parent of Ferrero Group and CTH Invest",
        "Consolidated revenue",
        22300,
        "EUR millions",
        "Year ended Aug 31, 2025",
        "Group revenue across chocolate, sugar, biscuits, ice cream, and snacks. Ferrara is inside CTH, not this whole number.",
        "3F's Holding release via PR Newswire, Mar 30, 2026",
        "https://www.prnewswire.com/news-releases/3fs-holding-sa-reports-consolidated-financial-statements-for-the-20242025-financial-year-302728011.html",
    ),
    (
        "Public-company peer",
        "The Hershey Company",
        "Competes in confectionery; also salty snacks",
        "Consolidated net sales",
        11692.6,
        "USD millions",
        "Calendar 2025",
        "Total company. North America Confectionery was $9,479.7 million of that. Not a sugar-only figure.",
        "Hershey full-year 2025 results",
        "https://hershey.gcs-web.com/news-releases/news-release-details/hershey-reports-fourth-quarter-and-full-year-2025-financial",
    ),
    (
        "Public-company peer",
        "Mondelēz International",
        "Competes in candy in places; global snacking company",
        "Net revenues",
        38537,
        "USD millions",
        "Calendar 2025",
        "Global biscuits and chocolate portfolio. Not a U.S. sugar-confectionery share base.",
        "Mondelēz FY 2025 results",
        "https://ir.mondelezinternational.com/news-releases/news-release-details/mondelez-international-reports-q4-and-fy-2025-results",
    ),
    (
        "Public-company peer",
        "Tootsie Roll Industries",
        "Public confectionery peer, much narrower than Hershey or Mondelēz",
        "Net product sales",
        724.675,
        "USD millions",
        "Calendar 2025",
        "Filed product sales. Closest public pure-play on this list, still a different company and mix.",
        "Tootsie Roll 2025 Form 10-K",
        "https://www.sec.gov/Archives/edgar/data/98677/000110465926021621/tr-20251231x10k.htm",
    ),
    (
        "Private peer",
        "Mars / Mars Wrigley",
        "Named category competitor",
        "Filed net sales",
        None,
        "not used",
        "n/a",
        "Private. Overlap brands include Skittles, Starburst, and M&M's. No estimated revenue is loaded.",
        "Named in public category commentary; no company filing used",
        "https://www.ferrara.com/us/en",
    ),
    (
        "Private peer",
        "Perfetti Van Melle",
        "Named category competitor",
        "Filed net sales",
        None,
        "not used",
        "n/a",
        "Private. Overlap brands include Airheads and Mentos. No estimated revenue is loaded.",
        "Named peer; no company filing used",
        "https://www.ferrara.com/us/en",
    ),
    (
        "Private peer",
        "Haribo",
        "Named category competitor",
        "Filed net sales",
        None,
        "not used",
        "n/a",
        "Private. Gummy overlap, including Goldbears. No estimated revenue is loaded.",
        "Named peer; no company filing used",
        "https://www.ferrara.com/us/en",
    ),
    (
        "Public site, not in this book",
        "Jelly Belly, Black Forest, Dori, Carambar, Spree",
        "Observed on ferrara.com or the FY2025 release",
        "In synthetic warehouse",
        0,
        "families",
        "Observed Oct 8, 2026",
        "Homepage brands also include NERDS, Lemonhead, Laffy Taffy, Trolli, Brach's, and SweeTARTS, which are in the synthetic book. These five are not.",
        "ferrara.com US homepage and FY2025 release",
        "https://www.ferrara.com/us/en",
    ),
]

PUBLIC_METRICS = {
    "public_landscape": {
        "description": "Published Ferrara, affiliate, and peer figures with scope notes. Not a share model and not the synthetic book.",
        "sql": """
            SELECT group_name, entity, relationship, metric, value_num, unit, period, scope_note, source, source_url
            FROM public_context
            ORDER BY
              CASE group_name
                WHEN 'Ferrara published' THEN 1
                WHEN 'Affiliate structure' THEN 2
                WHEN 'Public-company peer' THEN 3
                WHEN 'Private peer' THEN 4
                ELSE 5
              END,
              entity, metric
        """,
        "unscoped": True,
    },
}


def ensure_public(path):
    path = Path(path)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS public_context (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          group_name TEXT NOT NULL,
          entity TEXT NOT NULL,
          relationship TEXT NOT NULL,
          metric TEXT NOT NULL,
          value_num REAL,
          unit TEXT NOT NULL,
          period TEXT NOT NULL,
          scope_note TEXT NOT NULL,
          source TEXT NOT NULL,
          source_url TEXT NOT NULL
        )
        """
    )
    conn.execute("DELETE FROM public_context")
    conn.executemany(
        """
        INSERT INTO public_context (
          group_name, entity, relationship, metric, value_num, unit, period, scope_note, source, source_url
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        FACTS,
    )
    conn.commit()
    conn.close()
