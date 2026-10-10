"""Synthetic confectionery commercial warehouse: medallion tables and governed metrics.

Public Ferrara brand names are flavor only. Every figure is generated.
"""
from __future__ import annotations

import random
import re
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

# Fictional suppliers. fill, on-time, reject rate, and cost variance are generation rules.
VENDORS = (
    ("VEN-01", "Northmill Co-Man", "Co-manufacturer", 0.97, 0.95, 0.008, 0.01),
    ("VEN-02", "Harbor Batch", "Co-manufacturer", 0.91, 0.86, 0.018, 0.04),
    ("VEN-03", "Cocoa Lane", "Ingredient", 0.98, 0.93, 0.006, -0.01),
    ("VEN-04", "Gel & Bright", "Ingredient", 0.88, 0.81, 0.027, 0.06),
    ("VEN-05", "Cinder Sugar", "Ingredient", 0.96, 0.94, 0.011, 0.02),
    ("VEN-06", "Orchard Pectin", "Ingredient", 0.93, 0.90, 0.034, 0.03),
    ("VEN-07", "Carton North", "Packaging", 0.99, 0.97, 0.004, 0.08),
)
FAMILY_SUPPLY = {
    "Nerds": (("VEN-01", 0.68), ("VEN-02", 0.32)),
    "SweeTarts": (("VEN-01", 0.64), ("VEN-02", 0.36)),
    "Trolli": (("VEN-04", 0.74), ("VEN-02", 0.26)),
    "Laffy Taffy": (("VEN-01", 0.55), ("VEN-07", 0.45)),
    "Butterfinger": (("VEN-03", 0.91), ("VEN-02", 0.09)),
    "Baby Ruth": (("VEN-03", 0.88), ("VEN-02", 0.12)),
    "Brach's": (("VEN-05", 0.62), ("VEN-06", 0.38)),
    "Lemonhead": (("VEN-06", 0.58), ("VEN-05", 0.42)),
}

REGIONS = {
    "North America": ("Midwest", "Northeast", "South", "West", "Canada"),
    "Europe": ("United Kingdom", "DACH", "France", "Benelux"),
    "Latin America": ("Brazil", "Mexico", "Southern Cone"),
    "Asia Pacific": ("Australia", "Japan", "Southeast Asia"),
}
SUBREGION_OF = {subregion: region for region, subregions in REGIONS.items() for subregion in subregions}
FISCAL_YEARS = tuple(f"FY{year}" for year in range(2020, 2027))

ACCOUNTS = [
    ("ACCT-0001", "Lakeshore Grocery", "Grocery", "North America", "Midwest"),
    ("ACCT-0002", "Prairie Basket", "Grocery", "North America", "Midwest"),
    ("ACCT-0003", "Harbor Market", "Grocery", "North America", "Northeast"),
    ("ACCT-0004", "Elm Street Grocers", "Grocery", "North America", "Northeast"),
    ("ACCT-0005", "Magnolia Foods", "Grocery", "North America", "South"),
    ("ACCT-0006", "Red Clay Market", "Grocery", "North America", "South"),
    ("ACCT-0007", "Cascade Foods", "Grocery", "North America", "West"),
    ("ACCT-0008", "Metro Mass Midwest", "Mass", "North America", "Midwest"),
    ("ACCT-0009", "Metro Mass East", "Mass", "North America", "Northeast"),
    ("ACCT-0010", "Metro Mass South", "Mass", "North America", "South"),
    ("ACCT-0011", "Metro Mass West", "Mass", "North America", "West"),
    ("ACCT-0012", "Corner Stop Chicago", "Convenience", "North America", "Midwest"),
    ("ACCT-0013", "Corner Stop Detroit", "Convenience", "North America", "Midwest"),
    ("ACCT-0014", "Pike Convenience", "Convenience", "North America", "Northeast"),
    ("ACCT-0015", "Bayou Stop", "Convenience", "North America", "South"),
    ("ACCT-0016", "PCH Stop", "Convenience", "North America", "West"),
    ("ACCT-0017", "Club North", "Club", "North America", "Midwest"),
    ("ACCT-0018", "Club Atlantic", "Club", "North America", "Northeast"),
    ("ACCT-0019", "Club Gulf", "Club", "North America", "South"),
    ("ACCT-0020", "Club Pacific", "Club", "North America", "West"),
    ("ACCT-0021", "Rx Lane Midwest", "Drug", "North America", "Midwest"),
    ("ACCT-0022", "Rx Lane East", "Drug", "North America", "Northeast"),
    ("ACCT-0023", "Rx Lane South", "Drug", "North America", "South"),
    ("ACCT-0024", "Rx Lane West", "Drug", "North America", "West"),
    ("ACCT-0025", "Harbour Grocery", "Grocery", "North America", "Canada"),
    ("ACCT-0026", "Club Laurentian", "Club", "North America", "Canada"),
    ("ACCT-0027", "Thames Grocery", "Grocery", "Europe", "United Kingdom"),
    ("ACCT-0028", "Club Thames", "Club", "Europe", "United Kingdom"),
    ("ACCT-0029", "Rhine Market", "Grocery", "Europe", "DACH"),
    ("ACCT-0030", "Club Alpine", "Club", "Europe", "DACH"),
    ("ACCT-0031", "Seine Foods", "Grocery", "Europe", "France"),
    ("ACCT-0032", "Club Loire", "Club", "Europe", "France"),
    ("ACCT-0033", "Canal Grocers", "Grocery", "Europe", "Benelux"),
    ("ACCT-0034", "Club Scheldt", "Club", "Europe", "Benelux"),
    ("ACCT-0035", "Atlantic Grocery", "Grocery", "Latin America", "Brazil"),
    ("ACCT-0036", "Club Cerrado", "Club", "Latin America", "Brazil"),
    ("ACCT-0037", "Mesa Foods", "Grocery", "Latin America", "Mexico"),
    ("ACCT-0038", "Club Altiplano", "Club", "Latin America", "Mexico"),
    ("ACCT-0039", "Pampas Market", "Grocery", "Latin America", "Southern Cone"),
    ("ACCT-0040", "Club Andes", "Club", "Latin America", "Southern Cone"),
    ("ACCT-0041", "Coral Grocery", "Grocery", "Asia Pacific", "Australia"),
    ("ACCT-0042", "Club Tasman", "Club", "Asia Pacific", "Australia"),
    ("ACCT-0043", "Kanto Market", "Grocery", "Asia Pacific", "Japan"),
    ("ACCT-0044", "Club Kanto", "Club", "Asia Pacific", "Japan"),
    ("ACCT-0045", "Straits Grocery", "Grocery", "Asia Pacific", "Southeast Asia"),
    ("ACCT-0046", "Club Straits", "Club", "Asia Pacific", "Southeast Asia"),
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
    "Grocery": 0.62,
    "Mass": 0.54,
    "Convenience": 0.57,
    "Club": 0.44,
    "Drug": 0.52,
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
  region TEXT NOT NULL,
  subregion TEXT NOT NULL
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
  subregion TEXT NOT NULL,
  activity_date TEXT NOT NULL,
  activity_type TEXT NOT NULL,
  owner TEXT NOT NULL,
  opp_id TEXT,
  fiscal_year TEXT NOT NULL
);
CREATE TABLE gold_opportunity (
  opp_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  account_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  region TEXT NOT NULL,
  subregion TEXT NOT NULL,
  family TEXT NOT NULL,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  opened_date TEXT NOT NULL,
  expected_net_cents INTEGER NOT NULL,
  source_activity_id TEXT,
  fiscal_year TEXT NOT NULL
);
CREATE TABLE gold_invoice (
  invoice_id TEXT PRIMARY KEY,
  account_id TEXT NOT NULL,
  account_name TEXT NOT NULL,
  channel TEXT NOT NULL,
  region TEXT NOT NULL,
  subregion TEXT NOT NULL,
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
  margin_cents INTEGER NOT NULL,
  fiscal_year TEXT NOT NULL
);
CREATE TABLE gold_receipt (
  receipt_id TEXT PRIMARY KEY,
  vendor_id TEXT NOT NULL,
  vendor_name TEXT NOT NULL,
  vendor_role TEXT NOT NULL,
  family TEXT NOT NULL,
  channel TEXT NOT NULL,
  region TEXT NOT NULL,
  subregion TEXT NOT NULL,
  fiscal_year TEXT NOT NULL,
  receipts INTEGER NOT NULL,
  on_time_receipts INTEGER NOT NULL,
  units_ordered INTEGER NOT NULL,
  units_received INTEGER NOT NULL,
  reject_units INTEGER NOT NULL,
  cost_cents INTEGER NOT NULL,
  contract_cents INTEGER NOT NULL
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
              (SELECT ROUND(SUM(net_cents)/100.0, 2) FROM gold_invoice WHERE 1=1 {scope}{year}{family}) AS net_sales,
              (SELECT ROUND(SUM(margin_cents)/100.0, 2) FROM gold_invoice WHERE 1=1 {scope}{year}{family}) AS margin,
              (SELECT ROUND(100.0 * SUM(margin_cents) / NULLIF(SUM(net_cents), 0), 1) FROM gold_invoice WHERE 1=1 {scope}{year}{family}) AS margin_pct,
              (SELECT ROUND(100.0 * SUM(trade_cents) / NULLIF(SUM(gross_cents), 0), 1) FROM gold_invoice WHERE 1=1 {scope}{year}{family}) AS trade_pct,
              (SELECT ROUND(SUM(expected_net_cents)/100.0, 2) FROM gold_opportunity WHERE status = 'Open'{scope}{year}{family}) AS open_pipeline,
              (SELECT ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) FROM gold_opportunity WHERE 1=1 {scope}{year}{family}) AS win_rate,
              (SELECT ROUND(100.0 * SUM(CASE WHEN opp_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) FROM gold_activity WHERE 1=1 {scope}{year}) AS conversion_pct
        """,
    },
    "commercial_funnel": {
        "description": "Activity to opportunity to won to incremental invoice dollars, beside total net sales.",
        "sql": """
            SELECT
              (SELECT COUNT(*) FROM gold_activity WHERE 1=1 {scope}{year}) AS activities,
              (SELECT COUNT(*) FROM gold_opportunity WHERE 1=1 {scope}{year}{family}) AS opportunities,
              (SELECT COUNT(*) FROM gold_opportunity WHERE status = 'Won'{scope}{year}{family}) AS won,
              (SELECT ROUND(SUM(net_cents)/100.0, 2) FROM gold_invoice WHERE opp_id IS NOT NULL{scope}{year}{family}) AS incremental_net,
              (SELECT ROUND(SUM(net_cents)/100.0, 2) FROM gold_invoice WHERE 1=1 {scope}{year}{family}) AS net_sales
        """,
    },
    "pipeline_by_stage": {
        "description": "Open opportunity count and expected net by stage.",
        "sql": """
            SELECT stage, COUNT(*) AS opportunities,
                   ROUND(SUM(expected_net_cents)/100.0, 2) AS expected_net
            FROM gold_opportunity
            WHERE status = 'Open'{scope}{year}{family}
            GROUP BY stage
            ORDER BY expected_net DESC
        """,
    },
    "close_by_family_channel": {
        "description": "Win rate by brand family and channel. The gap is inside this book, not a syndicated rank.",
        "sql": """
            SELECT family, channel, COUNT(*) AS opportunities,
                   SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) AS won,
                   ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
            FROM gold_opportunity
            WHERE 1=1 {scope}{year}{family}
            GROUP BY family, channel
            ORDER BY family, win_rate
        """,
    },
    "win_rate_by_channel": {
        "description": "Won opportunities divided by all opportunities, by channel.",
        "sql": """
            SELECT channel, COUNT(*) AS opportunities,
                   SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) AS won,
                   ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
            FROM gold_opportunity
            WHERE 1=1 {scope}{year}{family}
            GROUP BY channel
            ORDER BY win_rate DESC
        """,
    },
    "win_rate_by_region": {
        "description": "Won opportunities divided by all opportunities, by region.",
        "sql": """
            SELECT region, COUNT(*) AS opportunities,
                   SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) AS won,
                   ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
            FROM gold_opportunity
            WHERE 1=1 {scope}{year}{family}
            GROUP BY region
            ORDER BY win_rate DESC
        """,
    },
    "win_rate_by_subregion": {
        "description": "Won opportunities divided by all opportunities, by subregion.",
        "sql": """
            SELECT subregion, region, COUNT(*) AS opportunities,
                   SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) AS won,
                   ROUND(100.0 * SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_rate
            FROM gold_opportunity
            WHERE 1=1 {scope}{year}{family}
            GROUP BY subregion, region
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
            WHERE 1=1 {scope}{year}
            GROUP BY channel
            ORDER BY conversion_pct DESC
        """,
    },
    "activity_mix": {
        "description": "CRM activity counts by type.",
        "sql": """
            SELECT activity_type, COUNT(*) AS activities
            FROM gold_activity
            WHERE 1=1 {scope}{year}
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
            WHERE 1=1 {scope}{year}{family}
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
            WHERE 1=1 {scope}{year}{family}
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
            WHERE 1=1 {scope}{year}{family}
            GROUP BY family
            ORDER BY margin DESC
        """,
    },
    "net_by_family": {
        "description": "Net sales by brand family.",
        "sql": """
            SELECT family, ROUND(SUM(net_cents)/100.0, 2) AS net_sales, SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY family
            ORDER BY net_sales DESC
        """,
    },
    "net_by_channel": {
        "description": "Net sales by channel.",
        "sql": """
            SELECT channel, ROUND(SUM(net_cents)/100.0, 2) AS net_sales, SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY channel
            ORDER BY net_sales DESC
        """,
    },
    "net_by_region": {
        "description": "Net sales by international region.",
        "sql": """
            SELECT region, ROUND(SUM(net_cents)/100.0, 2) AS net_sales, SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY region
            ORDER BY net_sales DESC
        """,
    },
    "net_by_subregion": {
        "description": "Net sales by subregion.",
        "sql": """
            SELECT subregion, region, ROUND(SUM(net_cents)/100.0, 2) AS net_sales, SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY subregion, region
            ORDER BY net_sales DESC
        """,
    },
    "net_by_year": {
        "description": "Net sales by fiscal year, October through September.",
        "sql": """
            SELECT fiscal_year AS year, ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY fiscal_year
            ORDER BY fiscal_year
        """,
    },
    "net_by_month": {
        "description": "Net sales by invoice month. Halloween families lift September and October.",
        "sql": """
            SELECT substr(invoice_date, 1, 7) AS month,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
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
            WHERE 1=1 {scope}{year}{family}
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
            WHERE 1=1 {scope}{year}{family}
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
            WHERE 1=1 {scope}{year}{family}
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
            WHERE 1=1 {scope}{year}{family}
            GROUP BY account_name, channel
            ORDER BY net_sales DESC
            LIMIT 12
        """,
    },
    "season_index": {
        "description": "Calendar-month net sales indexed to January.",
        "sql": """
            WITH monthly AS (
              SELECT substr(invoice_date, 6, 2) AS month_num, SUM(net_cents) AS net_cents
              FROM gold_invoice
              WHERE 1=1 {scope}{year}{family}
              GROUP BY substr(invoice_date, 6, 2)
            )
            SELECT CASE month_num
                     WHEN '01' THEN 'Jan' WHEN '02' THEN 'Feb' WHEN '03' THEN 'Mar'
                     WHEN '04' THEN 'Apr' WHEN '05' THEN 'May' WHEN '06' THEN 'Jun'
                     WHEN '07' THEN 'Jul' WHEN '08' THEN 'Aug' WHEN '09' THEN 'Sep'
                     WHEN '10' THEN 'Oct' WHEN '11' THEN 'Nov' ELSE 'Dec'
                   END AS invoice_month,
                   ROUND(net_cents/100.0, 2) AS net_sales,
                   ROUND(100.0 * net_cents / NULLIF((SELECT net_cents FROM monthly WHERE month_num = '01'), 0), 1) AS index_vs_january
            FROM monthly
            ORDER BY month_num
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
            WHERE 1=1 {scope}{year}{family}
            GROUP BY 1
            ORDER BY net_sales DESC
        """,
    },
    "call_list": {
        "description": "Accounts with open pipeline and either a below-median win rate or no activity since 1 July 2026. Taken from the account scorecard. Not a forecast.",
        "source_metric": "account_scorecard",
        "sql": "",
    },
    "account_scorecard": {
        "description": "Account net sales, trade rate, win rate, open pipeline, and last activity.",
        "sql": """
            SELECT a.account_id, a.account_name, a.channel, a.region, a.subregion,
                   ROUND(COALESCE((SELECT SUM(net_cents) FROM gold_invoice i WHERE i.account_id = a.account_id{ifamily}{iyear}), 0)/100.0, 2) AS net_sales,
                   ROUND(100.0 * (SELECT SUM(trade_cents) FROM gold_invoice i WHERE i.account_id = a.account_id{ifamily}{iyear})
                         / NULLIF((SELECT SUM(gross_cents) FROM gold_invoice i WHERE i.account_id = a.account_id{ifamily}{iyear}), 0), 1) AS trade_pct,
                   ROUND(100.0 * (SELECT SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) FROM gold_opportunity o WHERE o.account_id = a.account_id{ofamily}{oyear})
                         / NULLIF((SELECT COUNT(*) FROM gold_opportunity o WHERE o.account_id = a.account_id{ofamily}{oyear}), 0), 1) AS win_rate,
                   ROUND(COALESCE((SELECT SUM(expected_net_cents) FROM gold_opportunity o WHERE o.account_id = a.account_id AND o.status = 'Open'{ofamily}{oyear}), 0)/100.0, 2) AS open_pipeline,
                   (SELECT MAX(activity_date) FROM gold_activity g WHERE g.account_id = a.account_id{gyear}) AS last_activity
            FROM (
                SELECT account_id, account_name, channel, region, subregion FROM gold_invoice
                UNION
                SELECT account_id, account_name, channel, region, subregion FROM gold_opportunity
                UNION
                SELECT account_id, account_name, channel, region, subregion FROM gold_activity
            ) a
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
            WHERE 1=1 {scope}{year}{family}
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
            WHERE status = 'Open'{scope}{year}{family}
            GROUP BY 1
            ORDER BY expected_net DESC
        """,
    },
    "family_mix_by_quarter": {
        "description": "Brand-family share of net sales by fiscal year.",
        "sql": """
            SELECT fiscal_year AS quarter, family,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY fiscal_year, family
            ORDER BY fiscal_year, net_sales DESC
        """,
    },
    "region_by_channel": {
        "description": "Net sales by region and channel.",
        "sql": """
            SELECT region, channel, ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY region, channel
            ORDER BY region, net_sales DESC
        """,
    },
    "subregion_by_channel": {
        "description": "Net sales by subregion and channel.",
        "sql": """
            SELECT subregion AS region, channel, ROUND(SUM(net_cents)/100.0, 2) AS net_sales
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY subregion, channel
            ORDER BY subregion, net_sales DESC
        """,
    },
    "sku_rank": {
        "description": "SKU net sales ranked inside each brand family.",
        "sql": """
            SELECT family, sku_name,
                   ROUND(SUM(net_cents)/100.0, 2) AS net_sales,
                   SUM(units) AS units
            FROM gold_invoice
            WHERE 1=1 {scope}{year}{family}
            GROUP BY family, sku_name
            ORDER BY family, net_sales DESC
        """,
    },
    "quality": {
        "description": "Invoice rows kept out of Gold, by reject reason.",
        "sql": "SELECT reason, COUNT(*) AS rejected FROM quarantine GROUP BY reason ORDER BY rejected DESC",
        "unscoped": True,
        "hide_when_scoped": True,
    },
    "vendor_scorecard": {
        "description": "Fictional vendor score: 40% fill, 30% on-time, 20% accepted quality, 10% cost. Not a supplier master.",
        "hide_when_scoped": True,
        "sql": """
            SELECT vendor_name, vendor_role,
                   SUM(receipts) AS receipts,
                   SUM(units_ordered) AS units_ordered,
                   SUM(units_received) AS units_received,
                   ROUND(100.0 * SUM(units_received) / NULLIF(SUM(units_ordered), 0), 1) AS fill_pct,
                   ROUND(100.0 * SUM(on_time_receipts) / NULLIF(SUM(receipts), 0), 1) AS on_time_pct,
                   ROUND(100.0 * SUM(reject_units) / NULLIF(SUM(units_received), 0), 1) AS reject_pct,
                   ROUND(100.0 * (SUM(cost_cents) - SUM(contract_cents)) / NULLIF(SUM(contract_cents), 0), 1) AS cost_var_pct,
                   ROUND(
                     0.40 * (100.0 * SUM(units_received) / NULLIF(SUM(units_ordered), 0))
                     + 0.30 * (100.0 * SUM(on_time_receipts) / NULLIF(SUM(receipts), 0))
                     + 0.20 * (100.0 - (100.0 * SUM(reject_units) / NULLIF(SUM(units_received), 0)))
                     + 0.10 * (100.0 - ABS(100.0 * (SUM(cost_cents) - SUM(contract_cents)) / NULLIF(SUM(contract_cents), 0))),
                   1) AS score
            FROM gold_receipt
            WHERE 1=1 {scope}{year}{family}
            GROUP BY vendor_name, vendor_role
            ORDER BY score ASC
        """,
    },
    "supply_service": {
        "description": "Fill and units short, by family. Ordered units match the invoice book. Not a forecast.",
        "hide_when_scoped": True,
        "sql": """
            SELECT family,
                   SUM(units_ordered) AS units_ordered,
                   SUM(units_received) AS units_received,
                   SUM(units_ordered) - SUM(units_received) AS units_short,
                   ROUND(100.0 * SUM(units_received) / NULLIF(SUM(units_ordered), 0), 1) AS fill_pct,
                   ROUND(100.0 * SUM(on_time_receipts) / NULLIF(SUM(receipts), 0), 1) AS on_time_pct
            FROM gold_receipt
            WHERE 1=1 {scope}{year}{family}
            GROUP BY family
            ORDER BY fill_pct ASC
        """,
    },
    "supply_risk": {
        "description": "Largest vendor share inside each family. Concentration in this synthetic book, not a filing.",
        "hide_when_scoped": True,
        "sql": """
            WITH vendor_family AS (
              SELECT family, vendor_name,
                     SUM(units_ordered) AS units_ordered,
                     SUM(units_received) AS units_received,
                     SUM(on_time_receipts) AS on_time_receipts,
                     SUM(receipts) AS receipts
              FROM gold_receipt
              WHERE 1=1 {scope}{year}{family}
              GROUP BY family, vendor_name
            ),
            ranked AS (
              SELECT vendor_family.*,
                     SUM(units_ordered) OVER (PARTITION BY family) AS family_units,
                     ROW_NUMBER() OVER (PARTITION BY family ORDER BY units_ordered DESC) AS vendor_rank
              FROM vendor_family
            )
            SELECT family, vendor_name,
                   ROUND(100.0 * units_ordered / NULLIF(family_units, 0), 1) AS share_pct,
                   ROUND(100.0 * units_received / NULLIF(units_ordered, 0), 1) AS fill_pct,
                   ROUND(100.0 * on_time_receipts / NULLIF(receipts, 0), 1) AS on_time_pct
            FROM ranked
            WHERE vendor_rank = 1
            ORDER BY share_pct DESC
        """,
    },
}


def _load_public_metrics():
    from app.public_context import PUBLIC_METRICS

    METRICS.update(PUBLIC_METRICS)


_load_public_metrics()

ROUTES = [
    ("close_by_family_channel", ["lose the close", "loses the close", "family by channel", "brand by channel", "close by family", "close by brand"]),
    ("public_landscape", ["competitive set", "competitor", "hershey", "mondelez", "mondelēz", "tootsie", "haribo", "perfetti", "mars wrigley", "public landscape", "affiliate", "orangeburg", "bellwood", "forest park", "linares", "manufacturing plant", "big game", "shaboozey", "andy cohen", "u.s. soccer", "campaign spend"]),
    ("waterfall_by_family", ["waterfall by brand", "waterfall by family", "price waterfall by brand"]),
    ("waterfall_by_account", ["waterfall by account", "price waterfall by account"]),
    ("waterfall_by_channel", ["waterfall", "price waterfall"]),
    ("season_index", ["season index", "versus january", "vs january"]),
    ("halloween_window", ["halloween window"]),
    ("vendor_scorecard", ["vendor scorecard", "vendor score", "supplier score"]),
    ("supply_risk", ["supply risk", "single source", "vendor concentration", "concentration"]),
    ("supply_service", ["fill rate", "on-time", "on time", "supply chain", "units short"]),
    ("call_list", ["who should we call", "who to call", "call list"]),
    ("account_scorecard", ["scorecard"]),
    ("pipeline_age", ["pipeline age", "aging"]),
    ("stage_conversion", ["stage conversion"]),
    ("family_mix_by_quarter", ["family mix", "share of net", "mix by quarter"]),
    ("subregion_by_channel", ["subregion by channel", "sub-region by channel"]),
    ("region_by_channel", ["region by channel", "region and channel"]),
    ("sku_rank", ["sku rank", "by sku"]),
    ("commercial_funnel", ["funnel", "activity to invoice", "activity through"]),
    ("pipeline_by_stage", ["pipeline", "open opportunit"]),
    ("win_rate_by_subregion", ["win rate by subregion", "subregion win"]),
    ("win_rate_by_region", ["win rate by region", "region win"]),
    ("win_rate_by_channel", ["win rate", "win-rate"]),
    ("activity_conversion", ["conversion", "activity to opp"]),
    ("activity_mix", ["activity mix", "call volume"]),
    ("realization_by_channel", ["realization", "gross to net", "gross-to-net"]),
    ("trade_by_channel", ["trade spend", "trade rate", "trade %"]),
    ("margin_by_family", ["margin"]),
    ("net_by_year", ["fiscal year", "by year"]),
    ("net_by_month", ["season", "by month", "monthly", "halloween"]),
    ("net_by_subregion", ["subregion", "sub-region"]),
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
    "activity mix",
    "net sales by channel",
    "halloween season",
    "price waterfall",
    "account scorecard",
    "who should we call",
    "vendor scorecard",
    "pipeline age",
    "where should we press",
    "where does nerds lose the close",
    "show the public competitive set",
    "what is our Nielsen share",
    "SAP IBP forecast for Nerds",
]


def connect(path=None):
    conn = sqlite3.connect(path or DB)
    conn.row_factory = sqlite3.Row
    return conn


def _months():
    start = date(2019, 10, 1)
    months = []
    year, month = start.year, start.month
    for _ in range(84):
        months.append(date(year, month, 1))
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


def _year_factor(month_start):
    fiscal = month_start.year + 1 if month_start.month >= 10 else month_start.year
    return 1 + 0.035 * (fiscal - 2020)


def _season(family, month):
    if family in HALLOWEEN and month in (9, 10):
        return 1.85 if month == 10 else 1.55
    if family in CHOCOLATE and month == 12:
        return 1.28
    if month in (1, 2):
        return 0.86
    return 1.0


def _current_book(path):
    conn = sqlite3.connect(path)
    try:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "gold_receipt" not in names:
            return False
        cols = {row[1] for row in conn.execute("PRAGMA table_info(gold_invoice)")}
        if "subregion" not in cols or "fiscal_year" not in cols:
            return False
        years = conn.execute("SELECT COUNT(DISTINCT fiscal_year) FROM gold_invoice").fetchone()[0]
        regions = conn.execute("SELECT COUNT(DISTINCT region) FROM account").fetchone()[0]
        return years >= 7 and regions >= 4
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def _load_supply(conn):
    vendors = {row[0]: row for row in VENDORS}
    price = {name: list_price for name, list_price, _margin in FAMILIES}
    groups = conn.execute(
        """
        SELECT family, channel, region, subregion, fiscal_year, SUM(units) AS units
        FROM gold_invoice
        GROUP BY family, channel, region, subregion, fiscal_year
        """
    ).fetchall()
    rows = []
    receipt_n = 0
    for family, channel, region, subregion, fiscal_year, units in groups:
        units = int(units)
        if units <= 0:
            continue
        remaining = units
        splits = FAMILY_SUPPLY[family]
        for index, (vendor_id, share) in enumerate(splits):
            if index == len(splits) - 1:
                qty = remaining
            else:
                qty = min(int(round(units * share)), remaining)
                remaining -= qty
            if qty <= 0:
                continue
            _vendor_id, name, role, fill, on_time, reject, cost_var = vendors[vendor_id]
            received = int(round(qty * fill))
            lots = 200
            on_time_lots = int(round(lots * on_time))
            rejected = int(round(received * reject))
            unit_cents = int(round(price[family] * 40))
            contract = qty * unit_cents
            cost = int(round(contract * (1 + cost_var)))
            receipt_n += 1
            rows.append(
                (
                    f"RCP-{receipt_n:05d}",
                    vendor_id,
                    name,
                    role,
                    family,
                    channel,
                    region,
                    subregion,
                    fiscal_year,
                    lots,
                    on_time_lots,
                    qty,
                    received,
                    rejected,
                    cost,
                    contract,
                )
            )
    conn.executemany("INSERT INTO gold_receipt VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)


def seed(path=None, force=False):
    path = Path(path or DB)
    if path.exists() and not force:
        if not _current_book(path):
            force = True
        else:
            from app.public_context import ensure_public

            ensure_public(path)
            return path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    rng = random.Random(20261007)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO account VALUES (?, ?, ?, ?, ?)", ACCOUNTS)
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
    for account_id, _name, channel, _region, _subregion in ACCOUNTS:
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
                if status == "Open" and activity_date < "2026-04-01":
                    status, stage = "Lost", "Lost"
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

    for account_id, _name, channel, _region, _subregion in ACCOUNTS:
        for family, _price, _cogs in FAMILIES:
            for month_start in _months():
                sku_id, price = sku_by_family[family][0 if month_start.month % 2 == 0 else 1]
                jitter = 0.82 + (sum(ord(char) for char in account_id + family) % 30) / 100
                units = int(CHANNEL_UNITS[channel] * _season(family, month_start.month) * _year_factor(month_start) * jitter)
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
        SELECT b.activity_id, b.account_id, a.account_name, a.channel, a.region, a.subregion,
               b.activity_date, b.activity_type, b.owner, o.opp_id,
               CASE WHEN CAST(substr(b.activity_date, 6, 2) AS INTEGER) >= 10
                    THEN 'FY' || CAST(CAST(substr(b.activity_date, 1, 4) AS INTEGER) + 1 AS TEXT)
                    ELSE 'FY' || substr(b.activity_date, 1, 4) END
        FROM bronze_activity b
        JOIN account a ON a.account_id = b.account_id
        LEFT JOIN bronze_opportunity o ON o.source_activity_id = b.activity_id
        """
    )
    conn.execute(
        """
        INSERT INTO gold_opportunity
        SELECT o.opp_id, o.account_id, a.account_name, a.channel, a.region, a.subregion, o.family,
               o.stage, o.status, o.opened_date, o.expected_net_cents, o.source_activity_id,
               CASE WHEN CAST(substr(o.opened_date, 6, 2) AS INTEGER) >= 10
                    THEN 'FY' || CAST(CAST(substr(o.opened_date, 1, 4) AS INTEGER) + 1 AS TEXT)
                    ELSE 'FY' || substr(o.opened_date, 1, 4) END
        FROM bronze_opportunity o
        JOIN account a ON a.account_id = o.account_id
        """
    )
    conn.execute(
        """
        INSERT INTO gold_invoice
        SELECT i.invoice_id, i.account_id, a.account_name, a.channel, a.region, a.subregion,
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
                 ELSE 0.60 END) AS INTEGER),
               CASE WHEN CAST(substr(i.invoice_date, 6, 2) AS INTEGER) >= 10
                    THEN 'FY' || CAST(CAST(substr(i.invoice_date, 1, 4) AS INTEGER) + 1 AS TEXT)
                    ELSE 'FY' || substr(i.invoice_date, 1, 4) END
        FROM bronze_invoice i
        JOIN account a ON a.account_id = i.account_id
        JOIN sku s ON s.sku_id = i.sku_id
        WHERE i.reject_reason IS NULL
        """
    )
    _load_supply(conn)
    conn.commit()
    conn.close()
    from app.public_context import ensure_public

    ensure_public(path)
    return path


SLICE_VALUES = {
    "channel": {"Grocery", "Mass", "Convenience", "Club", "Drug"},
    "region": set(REGIONS),
    "subregion": set(SUBREGION_OF),
    "family": {name for name, _price, _cogs in FAMILIES},
    "year": set(FISCAL_YEARS),
}


class SliceError(ValueError):
    pass


def clean_filters(filters):
    cleaned = {}
    for key in ("channel", "region", "subregion", "family", "year"):
        value = ((filters or {}).get(key) or "").strip()
        if not value:
            continue
        if value not in SLICE_VALUES[key]:
            raise SliceError(key)
        cleaned[key] = value
    if cleaned.get("region") and cleaned.get("subregion"):
        if SUBREGION_OF[cleaned["subregion"]] != cleaned["region"]:
            raise SliceError("subregion")
    return cleaned


def _pair_clause(pairs):
    parts = []
    params = []
    for column, value in pairs:
        if value:
            parts.append(f"{column} = ?")
            params.append(value)
    if not parts:
        return "", ()
    return " AND " + " AND ".join(parts), tuple(params)


def metric_sql(name, account_id=None, filters=None):
    spec = METRICS[name]
    if spec.get("source_metric"):
        return metric_sql(spec["source_metric"], account_id, filters)
    if spec.get("unscoped"):
        return spec["sql"], ()
    chosen = clean_filters(filters)
    clauses = {
        "scope": _pair_clause(
            [
                ("account_id", account_id),
                ("channel", chosen.get("channel")),
                ("region", chosen.get("region")),
                ("subregion", chosen.get("subregion")),
            ]
        ),
        "year": _pair_clause([("fiscal_year", chosen.get("year"))]),
        "family": _pair_clause([("family", chosen.get("family"))]),
        "ifamily": _pair_clause([("i.family", chosen.get("family"))]),
        "ofamily": _pair_clause([("o.family", chosen.get("family"))]),
        "iyear": _pair_clause([("i.fiscal_year", chosen.get("year"))]),
        "oyear": _pair_clause([("o.fiscal_year", chosen.get("year"))]),
        "gyear": _pair_clause([("g.fiscal_year", chosen.get("year"))]),
    }
    pieces = []
    params = []
    position = 0
    for match in re.finditer(r"\{(scope|year|family|ifamily|ofamily|iyear|oyear|gyear)\}", spec["sql"]):
        pieces.append(spec["sql"][position:match.start()])
        clause, extra = clauses[match.group(1)]
        pieces.append(clause)
        params.extend(extra)
        position = match.end()
    pieces.append(spec["sql"][position:])
    return "".join(pieces), tuple(params)


def run_metric(conn, name, account_id=None, filters=None):
    if name not in METRICS:
        raise KeyError(name)
    spec = METRICS[name]
    if spec.get("hide_when_scoped") and account_id:
        return []
    sql, params = metric_sql(name, None if spec.get("unscoped") else account_id, None if spec.get("unscoped") else filters)
    rows = [dict(row) for row in conn.execute(sql, params)]
    if name == "call_list":
        calls = account_calls(rows)
        attach_open_deals(conn, calls, filters)
        return calls
    return rows


def account_calls(rows):
    """Open pipeline plus a weak close or a quiet activity log. Eight names, largest pipeline first."""
    rates = sorted(row["win_rate"] for row in rows if row.get("win_rate") is not None)
    if not rates:
        return []
    median = rates[(len(rates) - 1) // 2]
    calls = []
    for row in rows:
        pipeline = row.get("open_pipeline") or 0
        if pipeline <= 0:
            continue
        reasons = []
        if row.get("win_rate") is not None and row["win_rate"] < median:
            reasons.append(f"win rate {row['win_rate']}% is below the median in this slice ({median}%)")
        last = row.get("last_activity") or ""
        if not last or last < "2026-07-01":
            reasons.append(f"last activity {last or 'is missing'}, before 1 July 2026")
        if not reasons:
            continue
        calls.append(
            {
                "account_id": row["account_id"],
                "account_name": row["account_name"],
                "channel": row["channel"],
                "region": row["region"],
                "subregion": row["subregion"],
                "win_rate": row["win_rate"],
                "trade_pct": row["trade_pct"],
                "open_pipeline": pipeline,
                "last_activity": row["last_activity"],
                "reason": "; ".join(reasons),
                "deals": [],
            }
        )
    calls.sort(key=lambda row: row["open_pipeline"], reverse=True)
    return calls[:8]


def attach_open_deals(conn, calls, filters=None):
    """Three largest open opportunities on each called account. Same book, same family and year slice."""
    if not calls:
        return
    chosen = clean_filters(filters)
    marks = ",".join("?" for _ in calls)
    sql = (
        "SELECT account_id, family, stage, opened_date, "
        "ROUND(expected_net_cents / 100.0, 2) AS expected_net "
        "FROM gold_opportunity WHERE status = 'Open' AND account_id IN (" + marks + ")"
    )
    params = [row["account_id"] for row in calls]
    if chosen.get("family"):
        sql += " AND family = ?"
        params.append(chosen["family"])
    if chosen.get("year"):
        sql += " AND fiscal_year = ?"
        params.append(chosen["year"])
    sql += " ORDER BY expected_net_cents DESC"
    grouped = {row["account_id"]: [] for row in calls}
    for deal in conn.execute(sql, params):
        bucket = grouped[deal["account_id"]]
        if len(bucket) < 3:
            bucket.append(
                {
                    "family": deal["family"],
                    "stage": deal["stage"],
                    "opened_date": deal["opened_date"],
                    "expected_net": deal["expected_net"],
                }
            )
    for row in calls:
        row["deals"] = grouped[row["account_id"]]


def slice_options(conn):
    def column(sql):
        return [row[0] for row in conn.execute(sql)]

    return {
        "channel": column("SELECT DISTINCT channel FROM account ORDER BY 1"),
        "region": column("SELECT DISTINCT region FROM account ORDER BY 1"),
        "subregion": column("SELECT DISTINCT subregion FROM account ORDER BY 1"),
        "family": column("SELECT DISTINCT family FROM gold_invoice ORDER BY 1"),
        "year": column("SELECT DISTINCT fiscal_year FROM gold_invoice ORDER BY 1"),
        "subregion_of": SUBREGION_OF,
    }


def catalog(conn):
    layers = []
    for table, layer, note in (
        ("bronze_activity", "Bronze", "CRM activity events as received"),
        ("bronze_opportunity", "Bronze", "Opportunities opened from a subset of activities"),
        ("bronze_invoice", "Bronze", "Shipment invoices, including rejected rows"),
        ("quarantine", "Quarantine", "Invoices kept out of Gold"),
        ("gold_activity", "Gold", "Activities conformed to account, channel, region, and subregion"),
        ("gold_opportunity", "Gold", "Opportunities with commercial status and expected net"),
        ("gold_invoice", "Gold", "Invoices with gross, trade, net, COGS, and margin"),
        ("gold_receipt", "Gold", "Synthetic vendor receipts sized to invoice units. Not a supplier master and not a forecast"),
    ):
        count = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
        layers.append({"table": table, "layer": layer, "rows": count, "note": note})
    return {
        "layers": layers,
        "metrics": {name: spec["description"] for name, spec in METRICS.items()},
        "families": [family for family, _price, _cogs in FAMILIES],
        "window": "FY2020 through FY2026",
    }


def _family_close_line(rows):
    grouped = {}
    for row in rows:
        if row.get("win_rate") is None or not row.get("opportunities"):
            continue
        grouped.setdefault(row["family"], []).append(row)
    spreads = []
    for family, cells in grouped.items():
        if len(cells) < 2:
            continue
        weak = min(cells, key=lambda item: (item["win_rate"], -item["opportunities"]))
        strong = max(cells, key=lambda item: (item["win_rate"], item["opportunities"]))
        spreads.append((strong["win_rate"] - weak["win_rate"], family, weak, strong))
    if not spreads:
        if not rows:
            return "No opportunities in this slice."
        only = min(rows, key=lambda item: item["win_rate"])
        return (
            f"{only['family']} wins {only['win_rate']}% in {only['channel']}. "
            "That is the only close in view, and it is not a syndicated rank."
        )
    _gap, family, weak, strong = max(spreads)
    return (
        f"{family} wins {weak['win_rate']}% in {weak['channel']} "
        f"({int(weak['won'])} of {int(weak['opportunities'])}) and "
        f"{strong['win_rate']}% in {strong['channel']}. "
        "That gap is this synthetic book, not a syndicated rank."
    )


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
    if metric == "close_by_family_channel":
        return _family_close_line(rows)
    if metric == "win_rate_by_channel":
        return f"{top['channel']} leads win rate at {top['win_rate']}% ({top['won']} of {top['opportunities']})."
    if metric == "win_rate_by_region":
        return f"{top['region']} leads regional win rate at {top['win_rate']}% ({top['won']} of {top['opportunities']})."
    if metric == "win_rate_by_subregion":
        return f"{top['subregion']} leads subregional win rate at {top['win_rate']}% ({top['won']} of {top['opportunities']})."
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
    if metric == "net_by_subregion":
        return f"{top['subregion']} leads subregional net sales at ${top['net_sales']:,.0f}."
    if metric == "net_by_year":
        return f"{top['year']} is the first fiscal year in this cut at ${top['net_sales']:,.0f}. Later years carry the book growth."
    if metric == "net_by_month":
        peak = max(rows, key=lambda row: row["net_sales"])
        return f"Peak invoice month is {peak['month']} at ${peak['net_sales']:,.0f}. September and October include the Halloween family lift."
    if metric == "top_accounts":
        return f"{top['account_name']} is the largest account in this scope at ${top['net_sales']:,.0f} net."
    if metric in ("waterfall_by_channel", "waterfall_by_family", "waterfall_by_account"):
        label = top.get("channel") or top.get("family") or top.get("account_name")
        return f"{label} nets ${top['net_sales']:,.0f} after ${top['trade_spend']:,.0f} trade, with ${top['margin']:,.0f} margin."
    if metric == "season_index":
        january = next(row for row in rows if row["invoice_month"] == "Jan")
        peak = max(rows, key=lambda row: row["net_sales"])
        return f"January is the index base at ${january['net_sales']:,.0f}. Peak month {peak['invoice_month']} indexes at {peak['index_vs_january']}."
    if metric == "halloween_window":
        window = next(row for row in rows if row["season_window"] == "Halloween window")
        return f"The Halloween window is ${window['net_sales']:,.0f} net on Nerds, Trolli, SweeTarts, and Laffy Taffy in September and October."
    if metric == "call_list":
        if not rows:
            return (
                "No account in this slice has open pipeline with a below-median close or a quiet activity log. "
                "This is the synthetic book, not a Ferrara call plan."
            )
        names = ", ".join(row["account_name"] for row in rows[:3])
        deal = (rows[0].get("deals") or [None])[0]
        deal_line = ""
        if deal:
            deal_line = (
                f" The largest open deal on {rows[0]['account_name']} is {deal['family']} at {deal['stage']}, "
                f"${deal['expected_net']:,.0f} expected net."
            )
        return (
            f"Call {names} first. They have open pipeline and either a win rate below the median in this slice "
            "or no activity since 1 July 2026."
            + deal_line
            + " This list is the synthetic book, not a Ferrara call plan and not a forecast."
        )
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
    if metric == "vendor_scorecard":
        return (
            f"{top['vendor_name']} is the lowest score at {top['score']} "
            f"(fill {top['fill_pct']}%, on time {top['on_time_pct']}%). "
            "The weights are 40% fill, 30% on-time, 20% accepted quality, and 10% cost."
        )
    if metric == "supply_service":
        return (
            f"{top['family']} has the lowest fill at {top['fill_pct']}%. "
            f"{int(top['units_short']):,} units were ordered from the invoice book and did not arrive. "
            "That gap is not a forecast."
        )
    if metric == "supply_risk":
        return (
            f"{top['family']} is {top['share_pct']}% {top['vendor_name']}. "
            "That concentration is inside this synthetic book, not a supplier filing."
        )
    if metric == "quality":
        total = sum(row["rejected"] for row in rows)
        return f"{total} invoice rows are quarantined and absent from every commercial metric."
    return METRICS[metric]["description"]


def match_refusal(question):
    for needles, message in REFUSALS:
        if any(needle in question for needle in needles):
            return message
    return None


_PUBLIC_FOCUS = (
    "orangeburg",
    "bellwood",
    "forest park",
    "linares",
    "shaboozey",
    "andy cohen",
    "u.s. soccer",
    "big game",
    "hershey",
    "mondelez",
    "mondelēz",
    "tootsie",
    "haribo",
    "perfetti",
    "mars",
)


def _focus_public(question, rows):
    folded = question.lower()
    tokens = [token for token in _PUBLIC_FOCUS if token in folded]
    if not tokens and not any(row["entity"].lower() in folded for row in rows):
        return []
    focused = []
    for row in rows:
        blob = f"{row['entity']} {row['scope_note']} {row['metric']}".lower()
        entity = row["entity"].lower()
        if entity in folded or any(token in blob and token in folded for token in tokens):
            focused.append(row)
    return focused


def _cite_public(rows):
    sentences = []
    for row in rows:
        figure = "not published" if row["value_num"] is None else f"{row['value_num']:g} {row['unit']}"
        sentences.append(
            f"{row['entity']}: {row['metric']} is {figure} ({row['period']}). {row['scope_note']}"
        )
    return " ".join(sentences)


PRESS_NEEDLES = (
    "where to press",
    "where should we press",
    "how do we compete",
    "competitive play",
    "crush",
)


def _is_press(question):
    return any(needle in question for needle in PRESS_NEEDLES)


def _speak_plays(brief):
    lines = [brief["book_label"], brief["boundary"]]
    lines.extend(f"{play['title']}. {play['detail']}" for play in brief["plays"])
    lines.extend(f"{arena['name']}: {arena['press']}" for arena in brief["arenas"])
    return " ".join(lines)


def match_metric(question):
    for metric, needles in ROUTES:
        if any(needle in question for needle in needles):
            return metric
    return None


def _applied_filters(chosen, params):
    applied = {}
    skipped = []
    for key, value in chosen.items():
        if value in params:
            applied[key] = value
        else:
            skipped.append(key)
    return applied, skipped


def answer(conn, question, username, account_id=None, audit_conn=None, filters=None):
    text = (question or "").strip()
    folded = text.lower()
    metric = None
    arenas = []
    chosen = clean_filters(filters)
    applied = {}
    skipped = []
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
        elif _is_press(folded):
            from app.compete import compete_brief

            route = "plays"
            brief = compete_brief(conn, audit_conn or conn, account_id, chosen)
            message = _speak_plays(brief)
            rows = brief["plays"]
            arenas = brief["arenas"]
            sql = None
            params = []
            applied = brief["filters"]
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
                sql, params = metric_sql(metric, account_id, chosen)
                source = audit_conn if metric == "public_landscape" and audit_conn is not None else conn
                rows = run_metric(source, metric, account_id, chosen)
                applied, skipped = _applied_filters(chosen, params)
                if metric == "public_landscape":
                    focused = _focus_public(folded, rows)
                    if focused:
                        rows = focused
                        message = _cite_public(rows)
                    else:
                        message = insight(metric, rows)
                else:
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
        "description": (
            METRICS[metric]["description"]
            if metric
            else "Commercial plays from the approved win-rate, trade, and net queries."
            if route == "plays"
            else None
        ),
        "answer": message,
        "sql": " ".join(sql.split()) if sql else None,
        "params": list(params),
        "rows": rows,
        "arenas": arenas,
        "filters": applied,
        "skipped": skipped,
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
