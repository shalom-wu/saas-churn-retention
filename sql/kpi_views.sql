-- ============================================================================
-- kpi_views.sql — churn and revenue KPIs, defined once
-- These views are the SQL reference for the numbers quoted in README.md and
-- the strategy deck; src/ implements the same definitions in Python (the
-- discounted-LTV math stays in Python — see sql/README.md).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Churn rate + revenue exposure by any segment column
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_churn_by_contract AS
SELECT Contract,
       COUNT(*)                                        AS customers,
       ROUND(AVG(churn_flag), 4)                       AS churn_rate,
       ROUND(SUM(MonthlyCharges), 2)                   AS mrr,
       ROUND(SUM(MonthlyCharges * churn_flag), 2)      AS mrr_lost_to_churn,
       ROUND(AVG(MonthlyCharges), 2)                   AS avg_monthly_charge
FROM customers GROUP BY Contract;

CREATE OR REPLACE VIEW v_churn_by_tenure_band AS
SELECT tenure_band,
       COUNT(*)                                        AS customers,
       ROUND(AVG(churn_flag), 4)                       AS churn_rate,
       ROUND(SUM(MonthlyCharges * churn_flag), 2)      AS mrr_lost_to_churn
FROM customers GROUP BY tenure_band;

CREATE OR REPLACE VIEW v_churn_by_payment AS
SELECT PaymentMethod,
       COUNT(*)                                        AS customers,
       ROUND(AVG(churn_flag), 4)                       AS churn_rate,
       ROUND(SUM(MonthlyCharges * churn_flag), 2)      AS mrr_lost_to_churn
FROM customers GROUP BY PaymentMethod;

CREATE OR REPLACE VIEW v_churn_by_charge_tier AS
SELECT charge_tier,
       COUNT(*)                                        AS customers,
       ROUND(AVG(churn_flag), 4)                       AS churn_rate,
       ROUND(SUM(MonthlyCharges), 2)                   AS mrr,
       ROUND(100.0 * SUM(MonthlyCharges) / SUM(SUM(MonthlyCharges)) OVER (), 1) AS mrr_share_pct
FROM customers GROUP BY charge_tier;

CREATE OR REPLACE VIEW v_churn_by_addons AS
-- add-on depth only makes sense for internet customers
SELECT n_addon_services,
       COUNT(*)                                        AS customers,
       ROUND(AVG(churn_flag), 4)                       AS churn_rate
FROM customers
WHERE InternetService <> 'No'
GROUP BY n_addon_services;

-- ----------------------------------------------------------------------------
-- Exposure-based monthly churn hazard by contract — the LTV model's key
-- input, computed here as the reference implementation:
--   hazard = churn events / total customer-months observed
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_hazard_by_contract AS
SELECT Contract,
       COUNT(*)                                        AS customers,
       SUM(churn_flag)                                 AS churned,
       SUM(GREATEST(tenure, 1))                        AS customer_months,
       ROUND(1.0 * SUM(churn_flag) / SUM(GREATEST(tenure, 1)), 5) AS monthly_churn_hazard,
       ROUND(LEAST(1.0 / NULLIF(1.0 * SUM(churn_flag) / SUM(GREATEST(tenure, 1)), 0),
                   (SELECT value FROM assumptions WHERE name = 'lifetime_cap_months')), 1)
           AS expected_lifetime_months
FROM customers GROUP BY Contract;

-- ----------------------------------------------------------------------------
-- The four named at-risk segments from the analysis (overlapping on purpose —
-- they are targetable descriptions, not a partition)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_at_risk_segments AS
WITH segs AS (
    SELECT 'New month-to-month (tenure <= 12m)' AS segment, *
    FROM customers WHERE Contract = 'Month-to-month' AND tenure <= 12
    UNION ALL
    SELECT 'Month-to-month + electronic check', *
    FROM customers WHERE Contract = 'Month-to-month' AND PaymentMethod = 'Electronic check'
    UNION ALL
    SELECT 'Fiber, no support/security add-ons', *
    FROM customers WHERE InternetService = 'Fiber optic'
                     AND OnlineSecurity = 'No' AND TechSupport = 'No'
    UNION ALL
    SELECT 'Premium charges ($90+), first year', *
    FROM customers WHERE MonthlyCharges >= 90 AND tenure <= 12
)
SELECT segment,
       COUNT(*)                                   AS customers,
       ROUND(AVG(churn_flag), 4)                  AS churn_rate,
       ROUND(SUM(MonthlyCharges), 2)              AS mrr,
       ROUND(SUM(MonthlyCharges * churn_flag), 2) AS mrr_lost_to_churn
FROM segs GROUP BY segment;

-- ----------------------------------------------------------------------------
-- Validation view: recompute the headline numbers quoted in README.md /
-- the deck, so a reviewer can check the claims in one query
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_validation_headlines AS
SELECT 'overall churn rate (README: 26.5%)' AS claim,
       ROUND(AVG(churn_flag), 4)::VARCHAR    AS sql_value
FROM customers
UNION ALL
SELECT 'month-to-month churn (README: 43%)',
       ROUND(AVG(churn_flag) FILTER (WHERE Contract = 'Month-to-month'), 4)::VARCHAR
FROM customers
UNION ALL
SELECT 'two-year churn (README: 3%)',
       ROUND(AVG(churn_flag) FILTER (WHERE Contract = 'Two year'), 4)::VARCHAR
FROM customers
UNION ALL
SELECT 'first-6-months churn (README: 53%)',
       ROUND(AVG(churn_flag) FILTER (WHERE tenure <= 6), 4)::VARCHAR
FROM customers
UNION ALL
SELECT 'MRR lost with churned cohort (deck: ~$139K)',
       ROUND(SUM(MonthlyCharges * churn_flag), 0)::VARCHAR
FROM customers
UNION ALL
SELECT 'monthly hazard, month-to-month (deck: ~2.4%)',
       (SELECT monthly_churn_hazard::VARCHAR FROM v_hazard_by_contract
        WHERE Contract = 'Month-to-month');
