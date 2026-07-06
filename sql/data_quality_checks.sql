-- ============================================================================
-- data_quality_checks.sql — validation gate for the customer table
-- Each check returns: check_name | records_flagged | detail
-- Expected values reflect the known quirks of the IBM Telco file.
-- ============================================================================

SELECT '01 duplicate customer IDs' AS check_name,
       COUNT(*) - COUNT(DISTINCT customerID) AS records_flagged,
       'each customer must appear exactly once' AS detail
FROM customers

UNION ALL
SELECT '02 zero-tenure customers (the 11 blank-TotalCharges rows)',
       COUNT(*) FILTER (WHERE tenure = 0),
       'brand-new unbilled customers; TotalCharges set to 0 in cleaning, not dropped'
FROM customers

UNION ALL
SELECT '03 TotalCharges missing or negative',
       COUNT(*) FILTER (WHERE TotalCharges IS NULL OR TotalCharges < 0),
       'must be zero after cleaning'
FROM customers

UNION ALL
SELECT '04 MonthlyCharges outside plausible range ($0-200)',
       COUNT(*) FILTER (WHERE MonthlyCharges <= 0 OR MonthlyCharges > 200),
       'sanity bound on the price column'
FROM customers

UNION ALL
SELECT '05 churn flag disagrees with Churn label',
       COUNT(*) FILTER (WHERE (Churn = 'Yes') <> (churn_flag = 1)),
       'derived 0/1 flag must match the source label'
FROM customers

UNION ALL
SELECT '06 unexpected Contract values',
       COUNT(*) FILTER (WHERE Contract NOT IN ('Month-to-month', 'One year', 'Two year')),
       'contract drives the LTV segmentation'
FROM customers

UNION ALL
SELECT '07 TotalCharges wildly inconsistent with tenure x MonthlyCharges',
       COUNT(*) FILTER (WHERE tenure > 0
                        AND ABS(TotalCharges - tenure * MonthlyCharges)
                            > 0.5 * tenure * MonthlyCharges),
       'loose internal-consistency bound (price changes over a lifetime are normal)'
FROM customers

ORDER BY check_name;
