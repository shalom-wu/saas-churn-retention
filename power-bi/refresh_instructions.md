# Refresh Instructions

## Regenerating the Power BI inputs

```bash
python -m src.run_pipeline    # optional: refresh figures/metrics too
python scripts/run_sql.py     # DQ checks + KPI views + data/powerbi/ exports
```

`scripts/run_sql.py` rewrites everything in `data/powerbi/`: the customer
fact table and KPI aggregates (from the SQL views) plus the LTV tables
(from `src/ltv.py`). `dim_interventions.csv` is a hand-maintained
assumption table — edit it directly if the deck's options change.

## Refreshing the dashboard

1. Open `power-bi/saas_churn_retention.pbix` in Power BI Desktop.
2. **Home → Refresh.**
3. If the repo lives at a different path, update the `DataFolder` parameter
   once: Transform data → Edit parameters.

## Rebuilding the .pbix from source

```bash
python scripts/build_pbip.py
```

then open `power-bi/saas_churn_retention.pbip` in Power BI Desktop, click
**Refresh now** on the banner(s), verify the three pages, and **File → Save
as → .pbix**.
