# Dashboard Brief — SaaS Customer Churn & Retention

## Audience & purpose

A retention lead's working view of the churn problem: how much revenue is
leaking, where it concentrates, what a lost customer is worth, and which
interventions are priced and ready to run. Built on the same cleaned table,
SQL KPI definitions, and LTV model as the rest of the repo — one logic,
three tools.

## Pages

### 1 — Retention Overview (executive KPI page)
Cards: Customers (7,043), Churn Rate (26.5%), MRR ($456K), MRR Lost to
Churn ($139K), Cost of Churned Cohort (~$4.5M, from the LTV model's
documented assumptions). Churn by contract (the 43%-vs-3% fault line) and by
tenure band (risk is front-loaded). Contract slicer + a "what this says"
interpretation tile.

### 2 — Churn Diagnostics
Churn rate by payment method (the electronic-check red flag), by price tier
(the $70–90 leak), by add-on count (52% → 5% retention gradient, internet
customers only, straight from the SQL aggregate), and by internet service
(fiber's price/value problem). Slicers: internet service, senior citizen.

### 3 — Value & Action (decision-support page)
Discounted LTV and all-in cost-per-churn by contract (from `src/ltv.py`),
the four at-risk segments sized in MRR terms, and the three costed
interventions with year-1 net PV, ROI and key risks — labeled as
decision-support estimates under stated assumptions, not promises.

## Honesty notes

- Churn rates are cohort shares of a snapshot, never monthly rates.
- The dollar layer (LTV, cost of churn, intervention PV) rests on documented
  assumptions in `src/config.py`; the tornado analysis in the repo shows the
  $3.3M–$6.3M range.
- Footer on every page credits the IBM Telco sample dataset and the
  subscription-business reframing.
