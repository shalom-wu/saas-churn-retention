"""Run the SQL layer and write the Power BI-ready tables.

Plumbing only — the SQL logic lives in sql/, the LTV math in src/ltv.py.
Run from the repo root:  python scripts/run_sql.py
"""

import os
import re
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FILES = ["create_tables.sql", "data_quality_checks.sql",
         "kpi_views.sql", "analysis_queries.sql"]
SHOW = {"data_quality_checks.sql", "analysis_queries.sql"}

SQL_EXPORTS = {
    "v_churn_by_contract": "kpi_churn_by_contract.csv",
    "v_churn_by_tenure_band": "kpi_churn_by_tenure_band.csv",
    "v_churn_by_payment": "kpi_churn_by_payment.csv",
    "v_churn_by_charge_tier": "kpi_churn_by_charge_tier.csv",
    "v_churn_by_addons": "kpi_churn_by_addons.csv",
    "v_hazard_by_contract": "kpi_hazard_by_contract.csv",
    "v_at_risk_segments": "at_risk_segments.csv",
}


def main() -> None:
    os.chdir(ROOT)
    con = duckdb.connect()
    for name in FILES:
        print(f"\n=== {name} ===")
        sql = (ROOT / "sql" / name).read_text()
        for stmt in [s.strip() for s in re.split(r";\s*(?:\n|$)", sql) if s.strip()]:
            result = con.execute(stmt)
            body = re.sub(r"^\s*(--[^\n]*\n)*", "", stmt).lstrip().upper()
            if name in SHOW and body.startswith(("SELECT", "WITH")):
                print(result.df().to_string(index=False, max_rows=25))
                print()

    out = ROOT / "data" / "powerbi"
    out.mkdir(parents=True, exist_ok=True)
    print("=== exports for Power BI ===")
    for view, fname in SQL_EXPORTS.items():
        con.execute(f"COPY (SELECT * FROM {view}) TO '{(out / fname).as_posix()}' "
                    f"(HEADER, DELIMITER ',')")
        n = con.execute(f"SELECT COUNT(*) FROM {view}").fetchone()[0]
        print(f"  {fname}: {n:,} rows")

    # customer-level fact table (analysis columns only, keeps the file lean).
    # tenure_band is zero-padded here so Power BI's alphabetical category
    # sort puts the bands in life-cycle order.
    con.execute(
        "COPY (SELECT customerID, gender, SeniorCitizen, Partner, Dependents, "
        "tenure, CASE tenure_band WHEN '0-6m' THEN '00-06m' WHEN '7-12m' THEN '07-12m' "
        "ELSE tenure_band END AS tenure_band, Contract, PaymentMethod, InternetService, "
        "n_addon_services, MonthlyCharges, charge_tier, TotalCharges, "
        "Churn, churn_flag FROM customers) TO "
        f"'{(out / 'fact_customers.csv').as_posix()}' (HEADER, DELIMITER ',')")
    print("  fact_customers.csv")

    # LTV by contract needs discounting -> computed by src/ltv.py (Python),
    # exported here so Power BI gets one consistent folder of inputs
    import pandas as pd

    from src.data_prep import prepare
    from src.ltv import cost_of_churn_summary, ltv_by_segment
    df = prepare(save=False)
    ltv = ltv_by_segment(df).reset_index()
    ltv.to_csv(out / "ltv_by_contract.csv", index=False)
    print(f"  ltv_by_contract.csv: {len(ltv)} rows (from src/ltv.py)")
    cost = cost_of_churn_summary(df)
    pd.DataFrame([cost]).to_csv(out / "kpi_cost_of_churn.csv", index=False)
    print("  kpi_cost_of_churn.csv: 1 row (from src/ltv.py, base-case assumptions)")


if __name__ == "__main__":
    main()
