# SQL Layer — Validation & KPI Reference

DuckDB scripts that validate the customer table and compute every churn KPI
quoted in the README and strategy deck — so a reviewer can check the claims
without running any Python. The discounted-LTV and modeling math stays in
`src/` (annuity discounting and scikit-learn belong in Python); SQL covers
everything up to and including the LTV model's *inputs*.

## Files (run in this order)

| File | What it does |
|---|---|
| `create_tables.sql` | Loads `data/processed/churn_clean.csv` + the business-assumption table |
| `data_quality_checks.sql` | 7 checks: duplicate IDs, the 11 zero-tenure rows, negative charges, label/flag agreement, contract domain, tenure×price consistency |
| `kpi_views.sql` | Churn/MRR by contract, tenure band, payment, price tier, add-on depth; exposure-based churn hazard by contract (the LTV input); the four at-risk segments; a validation view that recomputes the README's headline numbers |
| `analysis_queries.sql` | 9 questions a retention team would ask, ending with the claim-check query |

## How to run

```bash
pip install duckdb
python scripts/run_sql.py     # runs everything + writes data/powerbi/ exports
```

Or in the DuckDB CLI from the repo root: `.read sql/<file>` in the order
above.

## Key definitions

- **Churn rate** — mean of the 0/1 churn flag (the label is a snapshot, so
  this is a cohort share, never a monthly rate).
- **Monthly churn hazard** — churn events ÷ total customer-months observed
  (tenure summed, floored at 1). This is the constant-hazard estimator the
  Python LTV model consumes; `v_hazard_by_contract` is its reference
  implementation.
- **At-risk segments** — deliberately overlapping, describable groups (the
  kind a campaign can target), not model clusters.

## Outputs

`scripts/run_sql.py` writes the Power BI inputs to `data/powerbi/`:
segment-level KPI tables from these views, plus the customer-level fact
table. The LTV-by-contract table is exported from Python (`src/ltv.py`)
because it needs discounting — the handoff is deliberate and documented in
`power-bi/data_model.md`.
