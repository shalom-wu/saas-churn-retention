# DAX Measures

Copy-paste ready. Formats in parentheses.

## fact_customers

```dax
Customers = COUNTROWS ( fact_customers )                                  -- #,0

Churned Customers =
CALCULATE ( [Customers], fact_customers[churn_flag] = 1 )                 -- #,0

Churn Rate = DIVIDE ( [Churned Customers], [Customers] )                  -- 0.0%

MRR = SUM ( fact_customers[MonthlyCharges] )                              -- $#,0

MRR Lost to Churn =
CALCULATE ( [MRR], fact_customers[churn_flag] = 1 )                       -- $#,0

MRR Lost % = DIVIDE ( [MRR Lost to Churn], [MRR] )                        -- 0.0%

Avg Monthly Charge = AVERAGE ( fact_customers[MonthlyCharges] )           -- $#,0.00

Avg Tenure (months) = AVERAGE ( fact_customers[tenure] )                  -- 0.0

Share of Customers =
DIVIDE ( [Customers],
         CALCULATE ( [Customers], ALLSELECTED ( fact_customers ) ) )      -- 0.0%
```

## ltv_by_contract (values computed by src/ltv.py)

```dax
Avg Customer LTV = AVERAGE ( ltv_by_contract[avg_ltv] )                   -- $#,0
Avg Cost per Churn = AVERAGE ( ltv_by_contract[cost_per_churn] )          -- $#,0
```

## kpi_cost_of_churn (one-row summary from src/ltv.py)

```dax
Cost of Churned Cohort = MAX ( kpi_cost_of_churn[total_cost_of_churn] )   -- $#,0
Annualized Lost Revenue = MAX ( kpi_cost_of_churn[annualized_lost_revenue] ) -- $#,0
```

*(Cards auto-abbreviate to $4.47M / $1.67M via display units.)*

Definitions match `sql/kpi_views.sql` — the SQL layer is the reference; run
`sql/analysis_queries.sql` Q8 to cross-check every headline number.
