# Customer Churn Analysis And Retention Strategy

This repository analyzes churn in the public Telco Customer Churn dataset, framed as a subscription business. The workflow combines data cleaning, segment analysis, LTV and cost-of-churn calculations, predictive modeling, and a retention scenario.

## Project Summary

| Area | Details |
|---|---|
| Business question | Which customers are most likely to churn, what is the economic cost, and which retention actions are worth funding? |
| Data | Public Telco Customer Churn sample dataset, reframed as a subscription/SaaS-style business case. |
| Methods | Cohort analysis, LTV modeling, churn hazard estimation, logistic regression, XGBoost, SHAP, intervention ROI modeling. |
| Main outputs | Strategy deck, model report, figures, Power BI dashboard, SQL KPI exports. |
| Tools | Python, pytest, DuckDB SQL, Power BI, `.pbix` dashboard. |

## Key Findings

| # | Finding | Evidence |
|---|---|---|
| 1 | Churn has a large economic cost. | Estimated churned-cohort cost is about $4.5M, with a sensitivity range of $3.3M-$6.3M. |
| 2 | Contract type is the clearest business fault line. | Month-to-month customers churn at 43% versus 3% for two-year contracts. |
| 3 | Risk is front-loaded. | Churn in the first six months of tenure is about 53%. |
| 4 | The premium price tier leaks value. | The $70-$90 price tier churns at about 38%, and $70+ customers hold most MRR. |
| 5 | The model is useful for campaign targeting. | The riskiest decile reaches 77% precision, about 2.9x random targeting. |
| 6 | The recommended interventions clear the ROI screen. | Conservative year-1 net present value is about $0.4M, roughly 5x ROI under the stated assumptions. |

![Churn by contract type](reports/figures/fig_churn_by_contract.png)

## Data

The project uses the public Telco Customer Churn dataset hosted on Kaggle and commonly attributed to IBM sample data. Source notes and caveats are documented in [data-sources.md](data-sources.md) and [data/data_manifest.md](data/data_manifest.md).

The dataset is a static customer snapshot. It does not include true event timestamps, acquisition costs, customer acquisition channels, or actual gross margin. Business-dollar assumptions are explicit and centralized in [src/config.py](src/config.py).

## Methodology

1. Clean `TotalCharges`, derive tenure bands, price tiers, add-on counts, and segment labels.
2. Analyze churn by contract, tenure, payment method, price tier, add-ons, and at-risk segments.
3. Estimate customer lifetime value using exposure-based churn hazard, gross margin, discount rate, and replacement CAC assumptions.
4. Train class-weighted logistic regression and XGBoost models; evaluate with ROC-AUC, PR-AUC, precision, recall, and campaign-depth metrics.
5. Translate model and segment findings into contract, onboarding, and save-offer interventions with conservative deadweight haircuts.

## Repository Contents

| Path | Purpose |
|---|---|
| [notebooks/](notebooks) | Executed notebooks for cleaning, LTV/cost modeling, and predictive modeling. |
| [src/](src) | Data prep, LTV, modeling, visualization, and pipeline code. |
| [reports/](reports) | Strategy deck, model report, metrics, and figures. |
| [sql/](sql) | DuckDB quality checks, KPI views, and claim checks. |
| [power-bi/](power-bi) | Three-page Power BI dashboard, model notes, DAX, refresh steps, and screenshots. |
| [data/](data) | Raw, cleaned, processed, and Power BI-ready data files. |
| [tests/](tests) | Cleaning, LTV, and modeling tests. |

## Reproduce

Requires Python 3.11+.

```bash
git clone https://github.com/shalom-wu/saas-churn-retention-strategy.git
cd saas-churn-retention-strategy
pip install -r requirements.txt

python -m src.run_pipeline
python scripts/run_sql.py
pytest
```

The dataset is included in `data/`, so the analysis can run without a separate download.

## Reporting Layer

SQL is the validation and KPI reference layer. It checks the data, recomputes churn and MRR cuts, validates exposure-based churn hazards, and exports Power BI inputs to `data/powerbi/`.

Power BI is the stakeholder dashboard layer. The [power-bi/](power-bi) folder includes a working `.pbix`, data model notes, DAX measures, refresh steps, screenshots, and dashboard documentation.

## Limitations

- The dataset is a static snapshot with no true churn event dates.
- The churn label's observation window is unspecified.
- Margin, CAC, and discount rate are assumptions, not company actuals.
- Contract type is correlated with churn but may include self-selection.
- The telecom sample is used as a subscription-business proxy; the method is more portable than the exact coefficients.

## License And Credit

MIT License. Copyright (c) 2026 Shalom Wu.

Data credit: IBM Telco Customer Churn sample data hosted on Kaggle (`blastchar/telco-customer-churn`). See [data-sources.md](data-sources.md) and [data/data_manifest.md](data/data_manifest.md).
