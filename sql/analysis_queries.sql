-- ============================================================================
-- analysis_queries.sql — the questions a retention team would ask.
-- Standalone; run after create_tables.sql and kpi_views.sql.
-- ============================================================================

-- Q1. Where is the revenue actually leaking? (churn x MRR by contract)
SELECT * FROM v_churn_by_contract ORDER BY mrr_lost_to_churn DESC;

-- Q2. How front-loaded is churn in the customer lifecycle?
SELECT * FROM v_churn_by_tenure_band
ORDER BY CASE tenure_band WHEN '0-6m' THEN 1 WHEN '7-12m' THEN 2
    WHEN '13-24m' THEN 3 WHEN '25-48m' THEN 4 ELSE 5 END;

-- Q3. The payment-method red flag
SELECT * FROM v_churn_by_payment ORDER BY churn_rate DESC;

-- Q4. Which price tier leaks the most, and how much revenue sits there?
SELECT * FROM v_churn_by_charge_tier
ORDER BY CASE charge_tier WHEN '<$35' THEN 1 WHEN '$35-70' THEN 2
    WHEN '$70-90' THEN 3 ELSE 4 END;

-- Q5. Do add-on services anchor customers? (internet customers only)
SELECT * FROM v_churn_by_addons ORDER BY n_addon_services;

-- Q6. The LTV model's inputs: hazard and expected lifetime by contract
SELECT * FROM v_hazard_by_contract ORDER BY monthly_churn_hazard DESC;

-- Q7. The four at-risk segments, sized in revenue terms
SELECT * FROM v_at_risk_segments ORDER BY mrr_lost_to_churn DESC;

-- Q8. Claim check: recompute every headline number quoted in the README
SELECT * FROM v_validation_headlines;

-- Q9. Retention-offer targeting base: month-to-month customers ranked by
-- monthly spend (who a contract-shift campaign would call first)
SELECT customerID, tenure, MonthlyCharges, PaymentMethod, InternetService
FROM customers
WHERE Contract = 'Month-to-month' AND churn_flag = 0
ORDER BY MonthlyCharges DESC
LIMIT 20;
