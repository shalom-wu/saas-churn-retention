"""Run the full analysis end to end: clean -> EDA -> LTV -> models.

Usage (from the repo root, with data/raw/telco-customer-churn.csv in place):

    python -m src.run_pipeline

Regenerates every figure in reports/figures and reports/model-metrics.json.
"""

from src.data_prep import prepare
from src.eda import at_risk_segments, run_eda
from src.ltv import (
    cost_of_churn_summary,
    ltv_by_segment,
    plot_ltv_by_segment,
    plot_sensitivity_tornado,
)
from src.modeling import run_modeling


def main() -> None:
    print("1/4  Cleaning data and deriving features...")
    df = prepare()
    print(f"     {len(df):,} customers | churn rate {df['churn_flag'].mean():.1%}")

    print("2/4  Descriptive analysis...")
    run_eda(df)
    seg = at_risk_segments(df)
    worst = seg["churn_rate"].drop("Whole customer base (reference)").idxmax()
    print(f"     riskiest segment: {worst} "
          f"({seg.loc[worst, 'churn_rate']:.0%} churn)")

    print("3/4  LTV / cost-of-churn model...")
    ltv_table = ltv_by_segment(df)
    plot_ltv_by_segment(ltv_table)
    plot_sensitivity_tornado(df)
    cost = cost_of_churn_summary(df)
    print(f"     churned cohort: {cost['churned_customers']:,} customers | "
          f"total cost ${cost['total_cost_of_churn']/1e6:.1f}M")

    print("4/4  Churn models...")
    out = run_modeling(df)
    m = out["metrics"]
    print(f"     logistic ROC-AUC {m['logistic']['roc_auc']:.3f} | "
          f"xgboost ROC-AUC {m['xgboost']['roc_auc']:.3f}")
    print("Done. Figures in reports/figures, metrics in reports/model-metrics.json")


if __name__ == "__main__":
    main()
