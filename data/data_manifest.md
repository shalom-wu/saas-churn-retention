# Data Manifest

Every data file in this repo, what it is, and where it came from. The repo
is fully self-contained: everything needed to run the notebooks, SQL,
pipeline, and Power BI dashboard is included.

| File | Type | Rows × Cols | Size | Used by |
|---|---|---|---|---|
| `raw/telco-customer-churn.csv` | **Real, raw** | 7,043 × 21 | 0.9 MB | `src/data_prep.py` |
| `processed/churn_clean.csv` | **Real, derived** (cleaned + derived columns) | 7,043 × 27 | 1.2 MB | notebooks, SQL layer, tests |
| `powerbi/fact_customers.csv` | Derived (SQL export, analysis columns) | 7,043 × 16 | ~0.7 MB | Power BI |
| `powerbi/kpi_churn_by_*.csv` (5 files) | Derived (SQL KPI views) | 3–7 rows each | <1 KB | Power BI, review |
| `powerbi/kpi_hazard_by_contract.csv` | Derived (SQL) | 3 × 6 | <1 KB | Power BI, LTV validation |
| `powerbi/at_risk_segments.csv` | Derived (SQL) | 4 × 5 | <1 KB | Power BI |
| `powerbi/ltv_by_contract.csv` | **Derived + assumed** (from `src/ltv.py`: real hazards × assumed margin/CAC/discount) | 3 × 7 | <1 KB | Power BI |
| `powerbi/kpi_cost_of_churn.csv` | **Derived + assumed** (LTV model summary, base case) | 1 × 7 | <1 KB | Power BI |
| `powerbi/dim_interventions.csv` | **Assumed** (the deck's costed options — an assumption table, not data) | 3 × 7 | <1 KB | Power BI decision page |

## Source & provenance

- **Original dataset:** Telco Customer Churn (`WA_Fn-UseC_-Telco-Customer-Churn`),
  IBM sample data, hosted on Kaggle by user *blastchar*
  ([link](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)) and
  mirrored publicly by IBM ([github.com/IBM/telco-customer-churn-on-icp4d](https://github.com/IBM/telco-customer-churn-on-icp4d)).
  Pulled 2026-07-05 from the IBM mirror. IBM distributes this file publicly
  as sample data; it is synthetic/sample data about fictional customers (no
  real PII), which is why redistribution here is appropriate. Kaggle hosts
  it; IBM authored it.
- **Cleaning applied** (`src/data_prep.py`): `TotalCharges` text→numeric with
  the 11 blank/zero-tenure rows set to $0 (documented); `SeniorCitizen`
  recoded 0/1→No/Yes; derived tenure bands, charge tiers, add-on counts,
  churn flag. No rows dropped, no values imputed beyond the 11 documented
  zeros.
- **Assumption-bearing files** are labeled above; the assumptions live in
  `src/config.py` with rationales, and the sensitivity analysis in
  [notebook 02](../notebooks/02-ltv-cost-of-churn.ipynb) shows how much the
  headline moves when they're wrong.

## Regenerating

```bash
python -m src.run_pipeline    # processed data, figures, metrics (from raw/)
python scripts/run_sql.py     # everything in powerbi/
```

The raw file is included, so there is nothing to download; `data-sources.md`
documents the original pull for anyone who wants to re-fetch it.
