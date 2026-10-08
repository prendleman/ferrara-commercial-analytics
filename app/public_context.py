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
        "Private. No 10-K in this table. Overlap brands include Skittles, Starburst, and M&M's. A prospectus total for the whole company is a separate row. The candy band is a synthetic guess, not this cell.",
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
        "Private. No audited group filing in this table. Overlap brands include Airheads and Mentos. The company site states a 2025 floor on a separate row. No brand split is guessed.",
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
        "Private. Gummy overlap, including Goldbears. No company revenue is filed here. The Market guess panel holds a labeled synthetic figure.",
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
    (
        "Published report",
        "Mars Inc.",
        "Whole company, including pet care and food, not Mars Wrigley alone",
        "Reported net sales",
        54600,
        "USD millions",
        "2024",
        "Bloomberg, March 5, 2025, reported a bond prospectus figure of $54.6 billion net sales, up 4.6%. That is the whole company. It is not a confectionery split and not a 10-K.",
        "Bloomberg, Candy Maker Mars Paid $1.5 Billion to Family Shareholders in 2024",
        "https://www.bloomberg.com/news/articles/2025-03-05/candymaker-mars-paid-1-5-billion-to-family-shareholders-in-2024",
    ),
    (
        "Published report",
        "Perfetti Van Melle",
        "Company-stated group floor",
        "Company-stated net revenue",
        4000,
        "EUR millions, more than",
        "2025",
        "The company site says net revenue sales were above €4 billion in 2025. No Airheads, Mentos, or country split is stated.",
        "Perfetti Van Melle, At a glance",
        "https://www.perfettivanmelle.com/who-we-are/at-a-glance/",
    ),
    (
        "Published facility",
        "Bellwood, Illinois",
        "Manufacturing plant",
        "Purchase disclosed",
        None,
        "not disclosed",
        "FY2025",
        "The FY2025 release says the company purchased a Ferrara manufacturing plant in Bellwood, Illinois. No size, output, cost, or P&L is stated.",
        "Ferrara FY2025 performance release",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Published facility",
        "Forest Park, Illinois",
        "Manufacturing plant at 7301 Harrison St",
        "Reported floor area",
        258000,
        "square feet, about",
        "Lease through at least 2031",
        "Forest Park Review, June 19, 2026, reports about 258,000 square feet. Ferrara said a sale of the property will not affect manufacturing and the lease remains through at least 2031. Not output and not a P&L.",
        "Forest Park Review",
        "https://www.forestparkreview.com/2026/06/19/ferrara-candy-company-selling-factory/",
    ),
    (
        "Published facility",
        "Linares, Nuevo León",
        "Manufacturing plant",
        "New production mogul",
        None,
        "not disclosed",
        "FY2025",
        "The FY2025 release says a new production mogul was installed in Linares. No capacity or cost is stated.",
        "Ferrara FY2025 performance release",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Published facility",
        "Orangeburg County, South Carolina",
        "Announced plant, not yet producing",
        "Announced investment",
        675,
        "USD millions",
        "Announced Apr 22, 2026; first lines expected Q1 2029",
        "Company release: $675 million, 750,000 square feet, and 1,000 jobs over 10 years. First production lines are expected in the first quarter of 2029. This is not current output or a current P&L.",
        "Ferrara Orangeburg announcement",
        "https://www.ferrara.com/us/en/ferrara-candy-company-selects-orangeburg-county-new-manufacturing-site",
    ),
    (
        "Published facility",
        "Ferrara network",
        "Manufacturing, distribution, sales, and R&D",
        "Facilities",
        30,
        "facilities, more than",
        "FY2025 about boilerplate",
        "The FY2025 about section says more than 30 facilities worldwide. It is not a plant-by-plant list, and it is not a capacity figure.",
        "Ferrara FY2025 performance release, about section",
        "https://www.ferrara.com/us/en/ferrara-candy-company-announces-fy-2025-performance",
    ),
    (
        "Published campaign",
        "NERDS Big Game 2025",
        "Named brand campaign",
        "Media spend",
        None,
        "not disclosed",
        "Feb 4, 2025",
        "Company release: a 30-second spot, Wonderful World of NERDS, with Shaboozey, for NERDS Gummy Clusters. No spend and no sales result are stated, so this demo does not score it.",
        "Ferrara NERDS Big Game 2025 release",
        "https://www.ferrara.com/index.php/us/en/nerdsr-returns-big-game-exciting-new-ad-unleash-senses-featuring-singer-songwriter-shaboozey",
    ),
    (
        "Published campaign",
        "NERDS Big Game 2026",
        "Named brand campaign",
        "Media spend",
        None,
        "not disclosed",
        "Feb 4, 2026",
        "Company release: a 30-second spot, Taste Buds, with Andy Cohen, introducing NERDS Juicy Gummy Clusters. No spend and no sales result are stated, so this demo does not score it.",
        "Ferrara NERDS Big Game 2026 release",
        "https://www.ferrara.com/us/en/nerdsr-brings-its-gummy-character-and-its-taste-bud-andy-cohen-together-introduce-nerdsr-juicy",
    ),
    (
        "Published campaign",
        "U.S. Soccer packs",
        "Named brand partnership",
        "Media spend",
        None,
        "not disclosed",
        "Mar 2, 2026",
        "Company release: limited-edition SweeTARTS, NERDS, and Trolli packs for a multi-year U.S. Soccer partnership. No spend and no sales result are stated, so this demo does not score it.",
        "Ferrara U.S. Soccer release",
        "https://www.ferrara.com/us/en/sweetartsr-nerdsr-and-trollir-introduce-limited-edition-packs-celebrate-us-soccer-partnership",
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
                WHEN 'Published facility' THEN 2
                WHEN 'Published campaign' THEN 3
                WHEN 'Affiliate structure' THEN 4
                WHEN 'Public-company peer' THEN 5
                WHEN 'Published report' THEN 6
                WHEN 'Private peer' THEN 7
                ELSE 8
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
