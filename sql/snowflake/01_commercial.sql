-- Ferrara commercial book on Snowflake.
-- Executable path: python3 scripts/snowflake_load.py
-- Database FERRARA_COMMERCIAL. Schema SERVING. No sample-data share.

CREATE DATABASE IF NOT EXISTS FERRARA_COMMERCIAL;
CREATE SCHEMA IF NOT EXISTS FERRARA_COMMERCIAL.SERVING;

CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.bronze_activity (
  activity_id VARCHAR, account_id VARCHAR, activity_date VARCHAR, activity_type VARCHAR, owner VARCHAR
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.bronze_opportunity (
  opp_id VARCHAR, account_id VARCHAR, family VARCHAR, stage VARCHAR, status VARCHAR,
  opened_date VARCHAR, expected_net_cents NUMBER, source_activity_id VARCHAR
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.bronze_invoice (
  invoice_id VARCHAR, account_id VARCHAR, sku_id VARCHAR, opp_id VARCHAR, invoice_date VARCHAR,
  units NUMBER, gross_cents NUMBER, trade_cents NUMBER, reject_reason VARCHAR
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.quarantine (
  invoice_id VARCHAR, reason VARCHAR
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.gold_activity (
  activity_id VARCHAR, account_id VARCHAR, account_name VARCHAR, channel VARCHAR, region VARCHAR, subregion VARCHAR,
  activity_date VARCHAR, activity_type VARCHAR, owner VARCHAR, opp_id VARCHAR, fiscal_year VARCHAR
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.gold_opportunity (
  opp_id VARCHAR, account_id VARCHAR, account_name VARCHAR, channel VARCHAR, region VARCHAR, subregion VARCHAR,
  family VARCHAR, stage VARCHAR, status VARCHAR, opened_date VARCHAR, expected_net_cents NUMBER,
  source_activity_id VARCHAR, fiscal_year VARCHAR
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.gold_invoice (
  invoice_id VARCHAR, account_id VARCHAR, account_name VARCHAR, channel VARCHAR, region VARCHAR, subregion VARCHAR,
  sku_id VARCHAR, family VARCHAR, sku_name VARCHAR, opp_id VARCHAR, invoice_date VARCHAR,
  units NUMBER, gross_cents NUMBER, trade_cents NUMBER, net_cents NUMBER, cogs_cents NUMBER, margin_cents NUMBER,
  fiscal_year VARCHAR
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.gold_receipt (
  receipt_id VARCHAR, vendor_id VARCHAR, vendor_name VARCHAR, vendor_role VARCHAR,
  family VARCHAR, channel VARCHAR, region VARCHAR, subregion VARCHAR, fiscal_year VARCHAR,
  receipts NUMBER, on_time_receipts NUMBER, units_ordered NUMBER, units_received NUMBER,
  reject_units NUMBER, cost_cents NUMBER, contract_cents NUMBER
);
CREATE TABLE IF NOT EXISTS FERRARA_COMMERCIAL.SERVING.public_context (
  group_name VARCHAR, entity VARCHAR, relationship VARCHAR, metric VARCHAR, value_num FLOAT,
  unit VARCHAR, period VARCHAR, scope_note VARCHAR, source VARCHAR, source_url VARCHAR
);
