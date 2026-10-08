"""Synthetic confectionery commercial warehouse: medallion tables and governed metrics.

Public Ferrara brand names are flavor only. Every figure is generated.
"""
from __future__ import annotations

import random
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "demo.db"

FAMILIES = [
    ("Nerds", 16.50, 0.61),
    ("Trolli", 15.25, 0.58),
    ("SweeTarts", 14.80, 0.60),
    ("Laffy Taffy", 13.40, 0.64),
    ("Butterfinger", 18.90, 0.55),
    ("Baby Ruth", 17.60, 0.57),
    ("Brach's", 12.75, 0.66),
    ("Lemonhead", 13.10, 0.63),
]

ACCOUNTS = [
    ("ACCT-0001", "Lakeshore Grocery", "Grocery", "Midwest"),
    ("ACCT-0002", "Prairie Basket", "Grocery", "Midwest"),
    ("ACCT-0003", "Harbor Market", "Grocery", "Northeast"),
    ("ACCT-0004", "Elm Street Grocers", "Grocery", "Northeast"),
    ("ACCT-0005", "Magnolia Foods", "Grocery", "South"),
    ("ACCT-0006", "Red Clay Market", "Grocery", "South"),
    ("ACCT-0007", "Cascade Foods", "Grocery", "West"),
    ("ACCT-0008", "Metro Mass Midwest", "Mass", "Midwest"),
    ("ACCT-0009", "Metro Mass East", "Mass", "Northeast"),
    ("ACCT-0010", "Metro Mass South", "Mass", "South"),
    ("ACCT-0011", "Metro Mass West", "Mass", "West"),
    ("ACCT-0012", "Corner Stop Chicago", "Convenience", "Midwest"),
    ("ACCT-0013", "Corner Stop Detroit", "Convenience", "Midwest"),
    ("ACCT-0014", "Pike Convenience", "Convenience", "Northeast"),
    ("ACCT-0015", "Bayou Stop", "Convenience", "South"),
    ("ACCT-0016", "PCH Stop", "Convenience", "West"),
    ("ACCT-0017", "Club North", "Club", "Midwest"),
    ("ACCT-0018", "Club Atlantic", "Club", "Northeast"),
    ("ACCT-0019", "Club Gulf", "Club", "South"),
    ("ACCT-0020", "Club Pacific", "Club", "West"),
    ("ACCT-0021", "Rx Lane Midwest", "Drug", "Midwest"),
    ("ACCT-0022", "Rx Lane East", "Drug", "Northeast"),
    ("ACCT-0023", "Rx Lane South", "Drug", "South"),
    ("ACCT-0024", "Rx Lane West", "Drug", "West"),
]

CHANNEL_UNITS = {
    "Grocery": 1600,
    "Mass": 2800,
    "Convenience": 520,
    "Club": 3600,
    "Drug": 740,
}
TRADE_RATE = {
    "Grocery": 0.18,
    "Mass": 0.22,
    "Convenience": 0.12,
    "Club": 0.29,
    "Drug": 0.16,
}
WIN_BIAS = {
    "Grocery": 0.46,
    "Mass": 0.38,
    "Convenience": 0.41,
    "Club": 0.28,
    "Drug": 0.36,
}
ACTIVITY_TYPES = ["Call", "Meeting", "Promo proposal", "Reset review", "QBR"]
OWNERS = ["A. Shah", "M. Ortiz", "J. Nguyen", "R. Patel", "C. Brooks", "L. Kim"]
HALLOWEEN = {"Nerds", "Trolli", "SweeTarts", "Laffy Taffy"}
CHOCOLATE = {"Butterfinger", "Baby Ruth"}

SCHEMA = """
CREATE TABLE account (
  account_id TEXT PRIMARY KEY,
  account_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  region TEXT NOT NULL
);
CREATE TABLE sku (
  sku_id TEXT PRIMARY KEY,
  family TEXT NOT NULL,
  sku_name TEXT NOT NULL,
  list_price_cents INTEGER NOT NULL
);
CREATE TABLE bronze_activity (
  activity_id TEXT PRIMARY KEY,
  account_id TEXT,
  activity_date TEXT,
  activity_type TEXT,
  owner TEXT
);
CREATE TABLE bronze_opportunity (
  opp_id TEXT PRIMARY KEY,
  account_id TEXT,
  family TEXT,
  stage TEXT,
  status TEXT,
  opened_date TEXT,
  expected_net_cents INTEGER,
  source_activity_id TEXT
);
CREATE TABLE bronze_invoice (
  invoice_id TEXT PRIMARY KEY,
  account_id TEXT,
  sku_id TEXT,
  opp_id TEXT,
  invoice_date TEXT,
  units INTEGER,
  gross_cents INTEGER,
  trade_cents INTEGER,
  reject_reason TEXT
);
CREATE TABLE quarantine (
  invoice_id TEXT PRIMARY KEY,
  reason TEXT NOT NULL
);
CREATE TABLE gold_activity (
  activity_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  account_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  region TEXT NOT NULL,
  activity_date TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  owner TEXT NOT NULL,
  opp_id TEXT
);
CREATE TABLE gold_opportunity (
  opp_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  account_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  region TEXT NOT NULL,
  family TEXT NOT NULL,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  opened_date TEXT NOT NULL,
  expected_net_cents INTEGER NOT NULL,
  source_activity_id TEXT
);
CREATE TABLE gold_invoice (
  invoice_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  account_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  region TEXT NOT NULL,
  sku_id TEXT NOT NULL,
  family TEXT NOT NULL,
  sku_name TEXT NOT NULL,
  opp_id TEXT,
  invoice_date TEXT NOT NULL,
  units INTEGER NOT NULL,
  gross_cents INTEGER NOT NULL,
  trade_cents INTEGER NOT NULL,
  net_cents INTEGER NOT NULL,
  cogs_cents INTEGER NOT NULL,
  margin_cents INTEGER NOT NULL
);
CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  username TEXT NOT NULL,
  account_scope TEXT NOT NULL,
  question TEXT NOT NULL,
  route TEXT NOT NULL,
  metric TEXT,
  row_count INTEGER NOT NULL
);
"""

METRICS = {
    "kpi_summary": {
        "description": "Book KPIs: net sales, margin, trade rate, open pipeline, win rate, activity conversion.",
        "sql": """
            SELECT
              (SELECT ROUND(SUM(net_cents)/100.0, 2) FROM gold_invoice WHERE 1=1 {scope}) AS net_sales,
              (SELECT ROUND(SUM(margin_cents)/100.0, 2) FROM gold_invoice WHERE 1=1 {scope}) AS margin,
              (SELECT ROUND(100.0 * SUM(margin_cents) / NULLIF(SUM(net_cents), 0), 1) FROM gold_invoice WHERE 1=1 {scope}) AS margin_pct,
              (SELECT ROUND(100.0 * SUM(trade_cents) / NULLIF(SUM(gross_cents), 0), 1) FROM gold_invoice WHERE 1=1 {scope}) AS trade_pct,
              (SELECT ROUND(SUM(expected_net_cents)/100.0, 2) FROM gold_opportunity WHERE status = 'Open'{scope}) AS open_pipeline,
              (SELECT ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) FROM gold_opportunity WHERE 1=1 {scope}) AS win_rate,
              (SELECT ROUND(100.0 * SUM(CASE WHEN opp_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) FROM gold_activity WHERE 1=1 {scope}) AS conversion_pct
        """,
    },
    "commercial_funnel": {
        "description": "Activity to opportunity to won to incremental invoice dollars, beside total net sales.",
        "sql": """
            SELECT
              (SELECT COUNT(*) FROM gold_activity WHERE 1=1 {scope}) AS activities,
              (SELECT COUNT(*) FROM gold_opportunity WHERE 1=1 {scope}) AS opportunities,
              (SELECT COUNT(*) FROM gold_opportunity WHERE status = 'Won'{scope}) AS won,
              (SELECT ROUND(SUM(net_cents)/100.0, 2) FROM gold_invoice WHERE opp_id IS NOT NULL{scope}) AS incremental_net,
              (SELECT ROUND(SUM(net_cents)/100.0, 2) FROM gold_invoice WHERE 1=1 {scope}) AS net_sales
        """,
    },
    "pipeline_by_stage": {
        "description": "Open opportunity count and expected net by stage.",
        "sql": """
            SELECT stage, COUNT(*) AS opportunities,
                   ROUND(SUM(expected_net_cents)/100.0, 2) AS expected_net
            FROM gold_opportunity
            WHERE status = 'Open'{scope}
            GROUP BY stage
            ORDER BY expected_net DESC
        """,
    },
    "win_rate_by_channel": {
        "description": "Won opportunities divided by all opportunities, by channel.",
        "sql": """
            SELECT channel, COUNT(*) AS opportunities,
                   SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) AS won,
                   ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
            FROM gold_opportunity
            WHERE 1=1 {scope}
            GROUP BY channel
            ORDER BY win_rate DESC
        """,
    },
    "activity_conversion": {
        "description": "Share of CRM activities that opened an opportunity, by channel.",
        "sql": """
            SELECT channel, COUNT(*) AS activities,
                   SUM(CASE WHEN opp_id IS NOT NULL THEN 1 ELSE 0 END) AS with_opportunity,
                   ROUND(100.0 * SUM(CASE WHEN opp_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS conversion_pct
            FROM gold_activity
            WHERE 1=1 {scope}
            GROUP BY channel
            ORDER BY conversion_pct DESC
        """,
    },
    "activity_mix": {
        "description": "CRM activity counts by type.",
        "sql": """
            SELECT activity_type, COUNT(*) AS activities
            FROM gold_activity
            WHERE 1=1 {scope}
            GROUP BY activity_type
            ORDER BY activities DESC
        """,
    },
    "realization_by_channel": {
        "description": "Gross sales, trade spend, net sales, and net divided by gross, by channel.",
        "sql": """
            SELECT channel,
                   ROUND(SUM(gross_cents)/100.0, 2) AS gross_sales,
                   ROUND(SUM(trade_cents)/100.0, 2) AS trade_spend,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   ROUND(100.0 * SUM(net_cents) / NULLIF(SUM(gross_cents), 0), 1) AS realization_pct
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY channel
            ORDER BY net_sales DESC
        """,
    },
    "trade_by_channel": {
        "description": "Trade spend as a percent of gross sales, by channel.",
        "sql": """
            SELECT channel,
                   ROUND(SUM(trade_cents)/100.0, 2) AS trade_spend,
                   ROUND(SUM(gross_cents)/100.0, 2) AS gross_sales,
                   ROUND(100.0 * SUM(trade_cents) / NULLIF(SUM(gross_cents), 0), 1) AS trade_pct
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY channel
            ORDER BY trade_pct DESC
        """,
    },
    "margin_by_family": {
        "description": "Margin dollars and margin percent of net sales, by brand family.",
        "sql": """
            SELECT family,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   ROUND(SUM(margin_cents)/100.0, 2) AS margin,
                   ROUND(100.0 * SUM(margin_cents) / NULLIF(SUM(net_cents), 0), 1) AS margin_pct
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY family
            ORDER BY margin DESC
        """,
    },
    "net_by_family": {
        "description": "Net sales by brand family.",
        "sql": """
            SELECT family, ROUND(SUM(net_cents)/100.0, 2) AS net_sales, SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY family
            ORDER BY net_sales DESC
        """,
    },
    "net_by_channel": {
        "description": "Net sales by channel.",
        "sql": """
            SELECT channel, ROUND(SUM(net_cents)/100.0, 2) AS net_sales, SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY channel
            ORDER BY net_sales DESC
        """,
    },
    "net_by_region": {
        "description": "Net sales by region.",
        "sql": """
            SELECT region, ROUND(SUM(net_cents)/100.0, 2) AS net_sales, SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY region
            ORDER BY net_sales DESC
        """,
    },
    "net_by_month": {
        "description": "Net sales by invoice month. Halloween families lift September and October.",
        "sql": """
            SELECT substr(invoice_date, 1, 7) AS month,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY substr(invoice_date, 1, 7)
            ORDER BY month
        """,
    },
    "top_accounts": {
        "description": "Accounts ranked by net sales.",
        "sql": """
            SELECT account_id, account_name, channel, region,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   ROUND(100.0 * SUM(margin_cents) / NULLIF(SUM(net_cents), 0), 1) AS margin_pct
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY account_id, account_name, channel, region
            ORDER BY net_sales DESC
            LIMIT 12
        """,
    },
    "waterfall_by_channel": {
        "description": "Gross, trade, net, COGS, and margin by channel.",
        "sql": """
            SELECT channel,
                   ROUND(SUM(gross_cents)/100.0, 2) AS gross_sales,
                   ROUND(SUM(trade_cents)/100.0, 2) AS trade_spend,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   ROUND(SUM(cogs_cents)/100.0, 2) AS cogs,
                   ROUND(SUM(margin_cents)/100.0, 2) AS margin
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY channel
            ORDER BY net_sales DESC
        """,
    },
    "waterfall_by_family": {
        "description": "Gross, trade, net, COGS, and margin by brand family.",
        "sql": """
            SELECT family,
                   ROUND(SUM(gross_cents)/100.0, 2) AS gross_sales,
                   ROUND(SUM(trade_cents)/100.0, 2) AS trade_spend,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   ROUND(SUM(cogs_cents)/100.0, 2) AS cogs,
                   ROUND(SUM(margin_cents)/100.0, 2) AS margin
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY family
            ORDER BY net_sales DESC
        """,
    },
    "waterfall_by_account": {
        "description": "Gross, trade, net, COGS, and margin for the largest accounts.",
        "sql": """
            SELECT account_name, channel,
                   ROUND(SUM(gross_cents)/100.0, 2) AS gross_sales,
                   ROUND(SUM(trade_cents)/100.0, 2) AS trade_spend,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   ROUND(SUM(cogs_cents)/100.0, 2) AS cogs,
                   ROUND(SUM(margin_cents)/100.0, 2) AS margin
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY account_name, channel
            ORDER BY net_sales DESC
            LIMIT 12
        """,
    },
    "season_index": {
        "description": "Invoice-month net sales indexed to January 2026.",
        "sql": """
            WITH monthly AS (
              SELECT substr(invoice_date, 1, 7) AS invoice_month, SUM(net_cents) AS net_cents
              FROM gold_invoice
              WHERE 1=1 {scope}
              GROUP BY substr(invoice_date, 1, 7)
            )
            SELECT invoice_month,
                   ROUND(net_cents/100.0, 2) AS net_sales,
                   ROUND(100.0 * net_cents / NULLIF((SELECT net_cents FROM monthly WHERE invoice_month = '2026-01'), 0), 1) AS index_vs_january
            FROM monthly
            ORDER BY invoice_month
        """,
    },
    "halloween_window": {
        "description": "Halloween-family net sales in September and October, beside the rest of the book.",
        "sql": """
            SELECT CASE
                     WHEN family IN ('Nerds', 'Trolli', 'SweeTarts', 'Laffy Taffy')
                      AND substr(invoice_date, 6, 2) IN ('09', '10')
                     THEN 'Halloween window'
                     ELSE 'Rest of book'
                   END AS season_window,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY 1
            ORDER BY net_sales DESC
        """,
    },
    "account_scorecard": {
        "description": "Account net sales, trade rate, win rate, open pipeline, and last activity.",
        "sql": """
            SELECT a.account_id, a.account_name, a.channel,
                   ROUND(COALESCE((SELECT SUM(net_cents) FROM gold_invoice i WHERE i.account_id = a.account_id), 0)/100.0, 2) AS net_sales,
                   ROUND(100.0 * (SELECT SUM(trade_cents) FROM gold_invoice i WHERE i.account_id = a.account_id)
                         / NULLIF((SELECT SUM(gross_cents) FROM gold_invoice i WHERE i.account_id = a.account_id), 0), 1) AS trade_pct,
                   ROUND(100.0 * (SELECT SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) FROM gold_opportunity o WHERE o.account_id = a.account_id)
                         / NULLIF((SELECT COUNT(*) FROM gold_opportunity o WHERE o.account_id = a.account_id), 0), 1) AS win_rate,
                   ROUND(COALESCE((SELECT SUM(expected_net_cents) FROM gold_opportunity o WHERE o.account_id = a.account_id AND o.status = 'Open'), 0)/100.0, 2) AS open_pipeline,
                   (SELECT MAX(activity_date) FROM gold_activity g WHERE g.account_id = a.account_id) AS last_activity
            FROM account a
            WHERE 1=1 {scope}
            ORDER BY net_sales DESC
        """,
    },
    "stage_conversion": {
        "description": "Opportunity count and share by stage.",
        "sql": """
            SELECT stage, COUNT(*) AS opportunities,
                   ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_pct
            FROM gold_opportunity
            WHERE 1=1 {scope}
            GROUP BY stage
            ORDER BY opportunities DESC
        """,
    },
    "pipeline_age": {
        "description": "Open pipeline age versus 30 September 2026.",
        "sql": """
            SELECT CASE
                     WHEN opened_date >= '2026-09-01' THEN 'Under 30 days'
                     WHEN opened_date >= '2026-07-01' THEN '30 to 90 days'
                     ELSE 'Over 90 days'
                   END AS age_band,
                   COUNT(*) AS opportunities,
                   ROUND(SUM(expected_net_cents)/100.0, 2) AS expected_net
            FROM gold_opportunity
            WHERE status = 'Open'{scope}
            GROUP BY 1
            ORDER BY expected_net DESC
        """,
    },
    "family_mix_by_quarter": {
        "description": "Brand-family share of net sales by fiscal quarter in the book.",
        "sql": """
            SELECT CASE
                     WHEN substr(invoice_date, 6, 2) IN ('10', '11', '12') THEN substr(invoice_date, 1, 4) || ' Q4'
                     WHEN substr(invoice_date, 6, 2) IN ('01', '02', '03') THEN substr(invoice_date, 1, 4) || ' Q1'
                     WHEN substr(invoice_date, 6, 2) IN ('04', '05', '06') THEN substr(invoice_date, 1, 4) || ' Q2'
                     ELSE substr(invoice_date, 1, 4) || ' Q3'
                   END AS quarter,
                   family,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY 1, family
            ORDER BY quarter, net_sales DESC
        """,
    },
    "region_by_channel": {
        "description": "Net sales by region and channel.",
        "sql": """
            SELECT region, channel, ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY region, channel
            ORDER BY region, net_sales DESC
        """,
    },
    "sku_rank": {
        "description": "SKU net sales ranked inside each brand family.",
        "sql": """
            SELECT family, sku_name,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}
            GROUP BY family, sku_name
            ORDER BY family, net_sales DESC
        """,
    },
    "quality": {
        "description": "Invoice rows kept out of Gold, by reject reason.",
        "sql": "SELECT reason, COUNT(*) AS rows FROM quarantine GROUP BY reason ORDER BY rows DESC",
        "unscoped": True,
        "hide_when_scoped": True,
    },
}


def _load_public_metrics():
    from app.public_context import PUBLIC_METRICS

    METRICS.update(PUBLIC_METRICS)


_load_public_metrics()

ROUTES = [
    ("public_landscape", ["competitive set", "competitor", "hershey", "mondelez", "mondelēz", "tootsie", "haribo", "perfetti", "mars wrigley", "public landscape", "affiliate"]),
    ("waterfall_by_family", ["waterfall by brand", "waterfall by family", "price waterfall by brand"]),
    ("waterfall_by_account", ["waterfall by account", "price waterfall by account"]),
    ("waterfall_by_channel", ["waterfall", "price waterfall"]),
    ("season_index", ["season index", "versus january", "vs january"]),
    ("halloween_window", ["halloween window"]),
    ("account_scorecard", ["scorecard"]),
    ("pipeline_age", ["pipeline age", "aging"]),
    ("stage_conversion", ["stage conversion"]),
    ("family_mix_by_quarter", ["family mix", "share of net", "mix by quarter"]),
    ("region_by_channel", ["region by channel", "region and channel"]),
    ("sku_rank", ["sku rank", "by sku"]),
    ("commercial_funnel", ["funnel", "activity to invoice", "activity through"]),
    ("pipeline_by_stage", ["pipeline", "open opportunit"]),
    ("win_rate_by_channel", ["win rate", "win-rate"]),
    ("activity_conversion", ["conversion", "activity to opp"]),
    ("activity_mix", ["activity mix", "call volume"]),
    ("realization_by_channel", ["realization", "gross to net", "gross-to-net"]),
    ("trade_by_channel", ["trade spend", "trade rate", "trade %"]),
    ("margin_by_family", ["margin"]),
    ("net_by_month", ["season", "by month", "monthly", "halloween"]),
    ("net_by_region", ["region"]),
    ("net_by_channel", ["by channel", "channel"]),
    ("net_by_family", ["brand", "family", "nerds", "trolli", "butterfinger"]),
    ("top_accounts", ["top account", "which customer", "biggest account"]),
    ("kpi_summary", ["net sales", "overview", "how are we", "kpi"]),
]

REFUSALS = [
    (
        ["nielsen", "iri", "circana", "syndicated", "market share", "acv"],
        "Syndicated retail measurement is not in this warehouse. I will not estimate a current share, ACV, or a rank. Published company figures live on the Market tab, with their year and scope.",
    ),
    (
        ["ibp", "demand forecast", "demand plan", "sap apo"],
        "Demand-planning platform forecasts are not in this model. I will not invent a shipment or consumption forecast.",
    ),
    (
        ["s/4", "s4hana", "mdm", "master data management"],
        "Enterprise MDM and SAP S/4 scope are outside this demo. I will not describe a program this warehouse does not contain.",
    ),
]

EXAMPLES = [
    "show the commercial funnel",
    "open pipeline",
    "win rate by channel",
    "trade spend by channel",
    "margin by brand",
    "net sales by channel",
    "halloween season",
    "price waterfall",
    "account scorecard",
    "pipeline age",
    "show the public competitive set",
    "what is our Nielsen share",
    "SAP IBP forecast for Nerds",
]


def connect(path=None):
    conn = sqlite3.connect(path or DB)
    conn.row_factory = sqlite3.Row
    return conn


def _months():
    start = date(2025, 10, 1)
    months = []
    year, month = start.year, start.month
    for _ in range(12):
        months.append(date(year, month, 1))
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def _season(family, month):
    if family in HALLOWEEN and month in (9, 10):
        return 1.85 if month == 10 else 1.55
    if family in CHOCOLATE and month == 12:
        return 1.28
    if month in (1, 2):
        return 0.86
    return 1.0


def seed(path=None, force=False):
    path = Path(path or DB)
    if path.exists() and not force:
        from app.public_context import ensure_public

        ensure_public(path)
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    rng = random.Random(20261007)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO account VALUES (?, ?, ?, ?)", ACCOUNTS)
    skus = []
    family_cogs = {}
    for family, price, cogs_ratio in FAMILIES:
        family_cogs[family] = cogs_ratio
        for pack in ("Theater", "Share"):
            sku_id = f"SKU-{family[:4].upper()}-{pack[:2].upper()}"
            skus.append((sku_id, family, f"{family} {pack}", int(round(price * 100))))
    conn.executemany("INSERT INTO sku VALUES (?, ?, ?, ?)", skus)
    sku_by_family = {}
    for sku_id, family, name, price in skus:
        sku_by_family.setdefault(family, []).append((sku_id, price))

    activities = []
    opportunities = []
    invoices = []
    act_n = 0
    opp_n = 0
    inv_n = 0
    for account_id, _name, channel, _region in ACCOUNTS:
        for month_start in _months():
            n_act = 3 + (act_n + month_start.month) % 3
            for _ in range(n_act):
                act_n += 1
                activity_id = f"ACT-{act_n:05d}"
                day = 1 + rng.randrange(27)
                activity_date = date(month_start.year, month_start.month, day).isoformat()
                activities.append(
                    (
                        activity_id,
                        account_id,
                        activity_date,
                        ACTIVITY_TYPES[act_n % len(ACTIVITY_TYPES)],
                        OWNERS[act_n % len(OWNERS)],
                    )
                )
                if rng.random() >= 0.40:
                    continue
                opp_n += 1
                family = FAMILIES[(opp_n + month_start.month) % len(FAMILIES)][0]
                roll = rng.random()
                if roll < WIN_BIAS[channel]:
                    status, stage = "Won", "Won"
                elif roll < WIN_BIAS[channel] + 0.22:
                    status, stage = "Lost", "Lost"
                else:
                    status, stage = "Open", ("Qualify", "Propose", "Negotiate")[opp_n % 3]
                expected = int(rng.randrange(18_000, 95_000) * 100)
                opp_id = f"OPP-{opp_n:05d}"
                opportunities.append(
                    (opp_id, account_id, family, stage, status, activity_date, expected, activity_id)
                )
                if status != "Won":
                    continue
                sku_id, price = sku_by_family[family][opp_n % 2]
                units = 400 + rng.randrange(200, 1800)
                gross = units * price
                trade = int(gross * TRADE_RATE[channel] * (0.92 + rng.random() * 0.1))
                inv_n += 1
                invoices.append(
                    (f"INV-{inv_n:05d}", account_id, sku_id, opp_id, activity_date, units, gross, trade, None)
                )

    for account_id, _name, channel, _region in ACCOUNTS:
        for family, _price, _cogs in FAMILIES:
            for month_start in _months():
                sku_id, price = sku_by_family[family][0 if month_start.month % 2 == 0 else 1]
                jitter = 0.82 + (sum(ord(char) for char in account_id + family) % 30) / 100
                units = int(CHANNEL_UNITS[channel] * _season(family, month_start.month) * jitter)
                units = max(units, 40)
                gross = units * price
                trade = int(gross * TRADE_RATE[channel])
                inv_n += 1
                invoices.append(
                    (
                        f"INV-{inv_n:05d}",
                        account_id,
                        sku_id,
                        None,
                        month_start.isoformat(),
                        units,
                        gross,
                        trade,
                        None,
                    )
                )

    invoices.append(("INV-BAD-01", None, "SKU-NERD-TH", None, "2026-01-15", 10, 1000, 100, "missing_account"))
    invoices.append(("INV-BAD-02", "ACCT-0001", "SKU-NERD-TH", None, "2026-02-01", 5, -500, 0, "negative_gross"))
    invoices.append(("INV-BAD-03", "ACCT-0099", "SKU-TROL-TH", None, "2026-03-01", 8, 2000, 100, "unknown_account"))
    invoices.append(("INV-BAD-04", "ACCT-0001", "SKU-NONE", None, "2026-04-01", 8, 2000, 100, "unknown_sku"))

    conn.executemany("INSERT INTO bronze_activity VALUES (?, ?, ?, ?, ?)", activities)
    conn.executemany(
        "INSERT INTO bronze_opportunity VALUES (?, ?, ?, ?, ?, ?, ?, ?)", opportunities
    )
    conn.executemany(
        "INSERT INTO bronze_invoice VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", invoices
    )
    conn.execute(
        "INSERT INTO quarantine (invoice_id, reason) SELECT invoice_id, reject_reason "
        "FROM bronze_invoice WHERE reject_reason IS NOT NULL"
    )
    conn.execute(
        """
        INSERT INTO gold_activity
        SELECT b.activity_id, b.account_id, a.account_name, a.channel, a.region,
               b.activity_date, b.activity_type, b.owner, o.opp_id
        FROM bronze_activity b
        JOIN account a ON a.account_id = b.account_id
        LEFT JOIN bronze_opportunity o ON o.source_activity_id = b.activity_id
        """
    )
    conn.execute(
        """
        INSERT INTO gold_opportunity
        SELECT o.opp_id, o.account_id, a.account_name, a.channel, a.region, o.family,
               o.stage, o.status, o.opened_date, o.expected_net_cents, o.source_activity_id
        FROM bronze_opportunity o
        JOIN account a ON a.account_id = o.account_id
        """
    )
    conn.execute(
        """
        INSERT INTO gold_invoice
        SELECT i.invoice_id, i.account_id, a.account_name, a.channel, a.region,
               i.sku_id, s.family, s.sku_name, i.opp_id, i.invoice_date, i.units,
               i.gross_cents, i.trade_cents, i.gross_cents - i.trade_cents,
               CAST(ROUND((i.gross_cents - i.trade_cents) * CASE s.family
                 WHEN 'Nerds' THEN 0.61 WHEN 'Trolli' THEN 0.58 WHEN 'SweeTarts' THEN 0.60
                 WHEN 'Laffy Taffy' THEN 0.64 WHEN 'Butterfinger' THEN 0.55
                 WHEN 'Baby Ruth' THEN 0.57 WHEN 'Brach''s' THEN 0.66 WHEN 'Lemonhead' THEN 0.63
                 ELSE 0.60 END) AS INTEGER),
               (i.gross_cents - i.trade_cents) - CAST(ROUND((i.gross_cents - i.trade_cents) * CASE s.family
                 WHEN 'Nerds' THEN 0.61 WHEN 'Trolli' THEN 0.58 WHEN 'SweeTarts' THEN 0.60
                 WHEN 'Laffy Taffy' THEN 0.64 WHEN 'Butterfinger' THEN 0.55
                 WHEN 'Baby Ruth' THEN 0.57 WHEN 'Brach''s' THEN 0.66 WHEN 'Lemonhead' THEN 0.63
                 ELSE 0.60 END) AS INTEGER)
        FROM bronze_invoice i
        JOIN account a ON a.account_id = i.account_id
        JOIN sku s ON s.sku_id = i.sku_id
        WHERE i.reject_reason IS NULL
        """
    )
    conn.commit()
    conn.close()
    from app.public_context import ensure_public

    ensure_public(path)
    return path


def _scope(account_id):
    if account_id:
        return " AND account_id = ?", (account_id,)
    return "", ()


def metric_sql(name, account_id=None):
    spec = METRICS[name]
    if spec.get("unscoped"):
        return spec["sql"], ()
    clause, params = _scope(account_id)
    sql = spec["sql"].format(scope=clause)
    return sql, params * sql.count("?")


def run_metric(conn, name, account_id=None):
    if name not in METRICS:
        raise KeyError(name)
    spec = METRICS[name]
    if spec.get("hide_when_scoped") and account_id:
        return []
    sql, params = metric_sql(name, None if spec.get("unscoped") else account_id)
    return [dict(row) for row in conn.execute(sql, params)]


def catalog(conn):
    layers = []
    for table, layer, note in (
        ("bronze_activity", "Bronze", "CRM activity events as received"),
        ("bronze_opportunity", "Bronze", "Opportunities opened from a subset of activities"),
        ("bronze_invoice", "Bronze", "Shipment invoices, including rejected rows"),
        ("quarantine", "Quarantine", "Invoices kept out of Gold"),
        ("gold_activity", "Gold", "Activities conformed to account, channel, and region"),
        ("gold_opportunity", "Gold", "Opportunities with commercial status and expected net"),
        ("gold_invoice", "Gold", "Invoices with gross, trade, net, COGS, and margin"),
    ):
        count = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        layers.append({"table": table, "layer": layer, "rows": count, "note": note})
    return {
        "layers": layers,
        "metrics": {name: spec["description"] for name, spec in METRICS.items()},
        "families": [family for family, _price, _cogs in FAMILIES],
        "window": "2025-10 through 2026-09",
    }


def insight(metric, rows):
    if not rows:
        return "No rows in this scope."
    top = rows[0]
    if metric == "kpi_summary":
        return (
            f"Net sales ${top['net_sales']:,.0f} at {top['margin_pct']}% margin. "
            f"Trade is {top['trade_pct']}% of gross. Open pipeline ${top['open_pipeline']:,.0f}."
        )
    if metric == "commercial_funnel":
        return (
            f"{top['activities']:,} activities opened {top['opportunities']:,} opportunities; "
            f"{top['won']:,} won. Incremental invoice net is ${top['incremental_net']:,.0f} "
            f"inside ${top['net_sales']:,.0f} total net."
        )
    if metric == "pipeline_by_stage":
        dollars = sum(row["expected_net"] for row in rows)
        return f"Open pipeline is ${dollars:,.0f} across {sum(row['opportunities'] for row in rows)} opportunities."
    if metric == "win_rate_by_channel":
        return f"{top['channel']} leads win rate at {top['win_rate']}% ({top['won']} of {top['opportunities']})."
    if metric == "activity_conversion":
        return f"{top['channel']} converts {top['conversion_pct']}% of activities into an opportunity."
    if metric == "activity_mix":
        return f"{top['activity_type']} is the largest activity type at {top['activities']:,} events."
    if metric == "realization_by_channel":
        return f"{top['channel']} is the largest net-sales channel at ${top['net_sales']:,.0f}, realizing {top['realization_pct']}% of gross."
    if metric == "trade_by_channel":
        return f"{top['channel']} carries the highest trade rate at {top['trade_pct']}% of gross."
    if metric == "margin_by_family":
        return f"{top['family']} contributes the most margin dollars at ${top['margin']:,.0f} ({top['margin_pct']}% of its net)."
    if metric == "net_by_family":
        return f"{top['family']} leads brand-family net sales at ${top['net_sales']:,.0f}."
    if metric == "net_by_channel":
        return f"{top['channel']} leads channel net sales at ${top['net_sales']:,.0f}."
    if metric == "net_by_region":
        return f"{top['region']} leads regional net sales at ${top['net_sales']:,.0f}."
    if metric == "net_by_month":
        peak = max(rows, key=lambda row: row["net_sales"])
        return f"Peak invoice month is {peak['month']} at ${peak['net_sales']:,.0f}. September and October include the Halloween family lift."
    if metric == "top_accounts":
        return f"{top['account_name']} is the largest account in this scope at ${top['net_sales']:,.0f} net."
    if metric in ("waterfall_by_channel", "waterfall_by_family", "waterfall_by_account"):
        label = top.get("channel") or top.get("family") or top.get("account_name")
        return f"{label} nets ${top['net_sales']:,.0f} after ${top['trade_spend']:,.0f} trade, with ${top['margin']:,.0f} margin."
    if metric == "season_index":
        january = next(row for row in rows if row["invoice_month"] == "2026-01")
        peak = max(rows, key=lambda row: row["net_sales"])
        return f"January 2026 is the index base at ${january['net_sales']:,.0f}. Peak month {peak['invoice_month']} indexes at {peak['index_vs_january']}."
    if metric == "halloween_window":
        window = next(row for row in rows if row["season_window"] == "Halloween window")
        return f"The Halloween window is ${window['net_sales']:,.0f} net on Nerds, Trolli, SweeTarts, and Laffy Taffy in September and October."
    if metric == "account_scorecard":
        return f"{top['account_name']} nets ${top['net_sales']:,.0f} at a {top['trade_pct']}% trade rate. Last activity {top['last_activity']}."
    if metric == "stage_conversion":
        return f"{top['stage']} holds {top['opportunities']} opportunities, {top['share_pct']}% of the book."
    if metric == "pipeline_age":
        dollars = sum(row["expected_net"] for row in rows)
        return f"Open pipeline ${dollars:,.0f} split across age bands measured from 30 September 2026. Largest band: {top['age_band']}."
    if metric == "family_mix_by_quarter":
        return f"{top['quarter']} is led by {top['family']} at ${top['net_sales']:,.0f} net."
    if metric == "region_by_channel":
        return f"{top['region']} {top['channel']} is the largest region-channel cell at ${top['net_sales']:,.0f} net."
    if metric == "sku_rank":
        return f"{top['sku_name']} leads {top['family']} at ${top['net_sales']:,.0f} net."
    if metric == "public_landscape":
        return (
            "Published figures and named peers. A Ferrara sugar-confectionery release, an affiliate holding-company total, "
            "and a global snacking company are not one share denominator."
        )
    if metric == "quality":
        total = sum(row["rows"] for row in rows)
        return f"{total} invoice rows are quarantined and absent from every commercial metric."
    return METRICS[metric]["description"]


def match_refusal(question):
    for needles, message in REFUSALS:
        if any(needle in question for needle in needles):
            return message
    return None


def match_metric(question):
    for metric, needles in ROUTES:
        if any(needle in question for needle in needles):
            return metric
    return None


def answer(conn, question, username, account_id=None, audit_conn=None):
    text = (question or "").strip()
    folded = text.lower()
    metric = None
    if not folded:
        route = "refuse"
        message = "Ask for an approved commercial metric. I do not answer an empty question."
        rows = []
        sql = None
        params = []
    else:
        message = match_refusal(folded)
        if message:
            route = "refuse"
            rows = []
            sql = None
            params = []
        else:
            metric = match_metric(folded)
            if not metric:
                route = "refuse"
                message = (
                    "I only answer approved commercial metrics. "
                    "Try funnel, pipeline, win rate, trade spend, margin, or net sales by brand."
                )
                rows = []
                sql = None
                params = []
            else:
                route = "metric"
                sql, params = metric_sql(metric, account_id)
                rows = run_metric(conn, metric, account_id)
                message = insight(metric, rows)
    audit = audit_conn or conn
    audit.execute(
        "INSERT INTO audit_log (ts, username, account_scope, question, route, metric, row_count) "
        "VALUES (datetime('now'), ?, ?, ?, ?, ?, ?)",
        (
            username,
            account_id or "*",
            text[:500],
            route,
            metric,
            len(rows),
        ),
    )
    audit.commit()
    return {
        "route": route,
        "metric": metric,
        "description": METRICS[metric]["description"] if metric else None,
        "answer": message,
        "sql": " ".join(sql.split()) if sql else None,
        "params": list(params),
        "rows": rows,
        "engine": "approved-metric router",
    }


def today_answer(question):
    folded = (question or "").strip().lower()
    if not folded:
        return "Today an empty ask sits in the analyst's inbox until someone rebuilds the export."
    if any(needle in folded for needle in ("nielsen", "iri", "syndicated", "ibp", "forecast", "mdm", "s/4")):
        return (
            "Today this still becomes an email thread. Someone may paste an outside number into a slide. "
            "Nothing records that the warehouse cannot support the claim."
        )
    if any(needle in folded for needle in ("pipeline", "win", "margin", "trade", "sales", "funnel", "brand", "channel")):
        return (
            "Today this is a one-off export. Channel, brand, and account definitions depend on who pulled the file. "
            "There is no approved query, no role scope, and no audit of the answer."
        )
    return (
        "Today this waits on a person. The commercial book is reachable only through dashboards and spreadsheets "
        "that do not share one definition of activity, opportunity, invoice, and margin."
    )


def recent_audit(conn, username=None, limit=12):
    if username:
        query = (
            "SELECT ts, username, account_scope, question, route, metric, row_count "
            "FROM audit_log WHERE username = ? ORDER BY id DESC LIMIT ?"
        )
        params = (username, limit)
    else:
        query = (
            "SELECT ts, username, account_scope, question, route, metric, row_count "
            "FROM audit_log ORDER BY id DESC LIMIT ?"
        )
        params = (limit,)
    return [dict(row) for row in conn.execute(query, params)]
