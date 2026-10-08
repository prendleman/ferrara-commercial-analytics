-- Ferrara commercial demo, Databricks SQL.
-- Synthetic book plus the published-context table.
-- Catalog name follows DATABRICKS_CATALOG (default ferrara_commercial_demo).
-- Do not point this at a Ferrara production catalog.

CREATE CATALOG IF NOT EXISTS ferrara_commercial_demo;
CREATE SCHEMA IF NOT EXISTS ferrara_commercial_demo.commercial;

CREATE TABLE IF NOT EXISTS ferrara_commercial_demo.commercial.gold_invoice (
  invoice_id STRING,
  account_id STRING,
  account_name STRING,
  channel STRING,
  region STRING,
  sku_id STRING,
  family STRING,
  sku_name STRING,
  opp_id STRING,
  invoice_date STRING,
  units BIGINT,
  gross_cents BIGINT,
  trade_cents BIGINT,
  net_cents BIGINT,
  cogs_cents BIGINT,
  margin_cents BIGINT
);

CREATE TABLE IF NOT EXISTS ferrara_commercial_demo.commercial.gold_opportunity (
  opp_id STRING,
  account_id STRING,
  account_name STRING,
  channel STRING,
  region STRING,
  family STRING,
  stage STRING,
  status STRING,
  opened_date STRING,
  expected_net_cents BIGINT,
  source_activity_id STRING
);

CREATE TABLE IF NOT EXISTS ferrara_commercial_demo.commercial.gold_activity (
  activity_id STRING,
  account_id STRING,
  account_name STRING,
  channel STRING,
  region STRING,
  activity_date STRING,
  activity_type STRING,
  owner STRING,
  opp_id STRING
);

CREATE TABLE IF NOT EXISTS ferrara_commercial_demo.commercial.quarantine (
  invoice_id STRING,
  reason STRING
);

CREATE TABLE IF NOT EXISTS ferrara_commercial_demo.commercial.public_context (
  group_name STRING,
  entity STRING,
  relationship STRING,
  metric STRING,
  value_num DOUBLE,
  unit STRING,
  period STRING,
  scope_note STRING,
  source STRING,
  source_url STRING
);

-- Same definition the local app serves. Scope predicate is appended by the app.
CREATE OR REPLACE VIEW ferrara_commercial_demo.commercial.v_net_by_channel AS
SELECT channel,
       ROUND(SUM(net_cents) / 100.0, 2) AS net_sales,
       SUM(units) AS units
FROM ferrara_commercial_demo.commercial.gold_invoice
GROUP BY channel;
