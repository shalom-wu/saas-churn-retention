-- ============================================================================
-- create_tables.sql — load the cleaned customer table into DuckDB
-- Run from the repo root (scripts/run_sql.py does this for you).
-- ============================================================================

-- One row per customer, as produced by src/data_prep.py (cleaning steps and
-- derived columns are documented there and in the data dictionary).
CREATE OR REPLACE TABLE customers AS
SELECT * FROM read_csv_auto('data/processed/churn_clean.csv', header = true);

-- Business assumptions shared with src/config.py — kept as a table so the
-- SQL layer states its inputs instead of hiding them in queries.
CREATE OR REPLACE TABLE assumptions AS
SELECT * FROM (VALUES
    ('gross_margin',        0.70, 'Share of revenue left after serving cost; public SaaS medians ~73-75%'),
    ('replacement_cac',   400.00, 'Cost to acquire a replacement customer; ~9 months CAC payback at this ARPU'),
    ('annual_discount',     0.10, 'Discount rate for future cash flows'),
    ('lifetime_cap_months', 72.0, 'Do not extrapolate expected lifetimes beyond the observed tenure window')
) AS t(name, value, rationale);
