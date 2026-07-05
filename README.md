# Customer Churn Analysis & Retention Strategy

**The business problem:** A subscription business with 7,043 customers and
$456K in monthly recurring revenue is losing customers at 26.5% per cohort —
and the leavers skew premium ($74/month vs $61 for those who stay). This
project quantifies what that churn costs, finds where it concentrates, builds
a model that predicts who leaves next, and turns the findings into a costed,
self-funding retention plan.

Built on the public [Telco Customer Churn dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
(Kaggle, originally IBM sample data), deliberately reframed as a
subscription/SaaS-style business — the unit economics (MRR, LTV, CAC)
transfer directly, and the reframing is stated everywhere it matters. See
[data-sources.md](data-sources.md).

## Key findings

| # | Finding | Number |
|---|---|---|
| 1 | Full economic cost of the churned cohort (foregone LTV + replacement CAC) | **$4.5M** (range $3.3–6.3M) |
| 2 | Churn by contract type — the fault line of the business | **43%** month-to-month vs **3%** two-year |
| 3 | Churn in the first 6 months of tenure (risk is front-loaded) | **53%** |
| 4 | Churn in the $70–90 price tier — the premium tier leaks most, and $70+ holds 71% of MRR | **38%** |
| 5 | Retention gradient across add-on services (0 → 6 add-ons) | **52% → 5%** |
| 6 | XGBoost model precision in the riskiest decile (2.9x lift vs random) | **77%** |
| 7 | Year-1 net PV of the recommended interventions, conservative assumptions | **~$0.4M** (~5x ROI) |

![Churn by contract type](reports/figures/fig_churn_by_contract.png)

## What's in the box

| | |
|---|---|
| [notebooks/](notebooks) | Three executed walkthroughs: cleaning + EDA, the LTV/cost-of-churn model, and predictive modeling |
| [src/](src) | All logic as tested modules — [config.py](src/config.py) holds every business assumption in one place |
| [reports/strategy-deck.md](reports/strategy-deck.md) / [.pptx](reports/strategy-deck.pptx) | 7-slide strategy deck: problem → drivers → cost of inaction → options → recommendation |
| [reports/model-report.md](reports/model-report.md) | Model performance and limitations, written honestly |
| [reports/figures/](reports/figures) | Every chart as a standalone PNG |
| [explainer-guide/](explainer-guide/explain-it-to-me.md) | The whole project explained for a non-technical reader, with a glossary |
| [tests/](tests) | ~30 pytest checks on the cleaning, LTV math, and evaluation logic |

## Methodology (short version)

1. **Clean:** fix `TotalCharges` stored as text (11 blanks = unbilled new
   customers, set to $0, not dropped); derive tenure bands, price tiers,
   add-on counts. Documented in [notebook 01](notebooks/01-data-cleaning-eda.ipynb).
2. **Descriptive:** churn rate by contract, tenure, payment method, price
   tier, and service bundle; four named at-risk segments (each churns at ≥2x
   the base rate).
3. **Cost model:** exposure-based monthly churn hazard (events ÷
   customer-months) → expected lifetime (capped at the 72-month data window)
   → discounted LTV (70% gross margin, 10% discount rate) → cost of churn =
   foregone LTV + $400 replacement CAC. Assumptions benchmarked to published
   SaaS figures and stress-tested with a tornado sensitivity analysis.
4. **Predict:** class-weighted logistic regression baseline, then shallow
   XGBoost (test ROC-AUC 0.844 vs 0.838 — the honest headline is that the
   signal is mostly in a few strong features). Evaluated with PR-AUC and
   precision/recall at campaign depth, not accuracy. Drivers via SHAP,
   cross-checked against coefficients.
5. **Recommend:** three costed interventions (contract-shift incentive,
   model-targeted saves, onboarding-bundle pilot) with stated assumptions,
   deadweight haircuts, and a phased rollout.

## Reproducing the analysis

```bash
git clone https://github.com/shalom-wu/saas-churn-retention.git && cd saas-churn-retention
pip install -r requirements.txt

# Get the data (not redistributed here — see data-sources.md):
#   save as data/raw/telco-customer-churn.csv

python -m src.run_pipeline   # regenerates all figures + metrics (~1 min)
pytest                       # run the test suite
```

Python 3.11+ recommended. Notebooks re-execute with
`python -m nbconvert --to notebook --execute --inplace notebooks/*.ipynb`.

## Limitations (read before trusting the numbers)

- **Snapshot data.** No event timestamps, so the LTV model assumes a
  constant churn hazard per segment (churn is actually front-loaded — with
  timestamps this would be a survival model). Lifetimes are capped at the
  observation window to limit extrapolation.
- **The churn label's time window is unspecified.** 26.5% is treated as a
  cohort share, never a monthly rate.
- **Margin, CAC, and discount rate are industry benchmarks, not company
  actuals.** They live in [src/config.py](src/config.py) and the tornado
  chart shows exactly how much the headline moves when they're wrong.
- **Correlation ≠ causation.** Contract type is partly self-selection; the
  ROI model applies deadweight haircuts and the rollout plan requires A/B
  tests before scaling.
- **Telecom data in SaaS framing.** The method is the portable part; the
  specific coefficients are not.
- Full discussion: [reports/model-report.md](reports/model-report.md).

## Author

Shalom Wu ([@shalom-wu](https://github.com/shalom-wu)) — analysis, cost
model, and strategy. Dataset credit: IBM / Kaggle
(`blastchar/telco-customer-churn`). MIT licensed.
