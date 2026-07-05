# Data Sources

## Telco Customer Churn (Kaggle)

- **Source:** [Telco Customer Churn on Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) (`blastchar/telco-customer-churn`)
- **Original publisher:** IBM sample data sets (the file `WA_Fn-UseC_-Telco-Customer-Churn.csv`, also mirrored in IBM's [telco-customer-churn-on-icp4d](https://github.com/IBM/telco-customer-churn-on-icp4d) repository)
- **Size:** 7,043 customers, 21 columns
- **Contents:** customer tenure, contract type, monthly/total charges, service subscriptions (phone, internet, add-on services), payment method, demographics, and a churn label

## Why this dataset, and how it is framed here

This is a telecom dataset, but this project deliberately frames it as a
**subscription/SaaS-style recurring-revenue business**. Structurally the two are
the same problem: customers pay a monthly fee, can be on month-to-month or
annual contracts, subscribe to a base product plus add-ons, and cancel
(churn). The unit economics concepts used here — MRR, LTV, CAC, cost of
churn — transfer directly. Where the framing matters (e.g. calibrating
gross-margin and acquisition-cost assumptions), the assumptions are stated
explicitly and benchmarked against published SaaS figures rather than telecom
ones.

## Getting the data

The raw file is **not redistributed in this repository** (it stays out of git
via `.gitignore`). To reproduce the analysis, download it yourself:

1. **From Kaggle:** download `WA_Fn-UseC_-Telco-Customer-Churn.csv` from the
   [dataset page](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
2. **Or from IBM's public mirror** (identical file):

   ```
   https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
   ```

3. Save it as `data/raw/telco-customer-churn.csv`

Then run the pipeline (see README for details).

## Known data quality issues

Documented in full in `notebooks/01-data-cleaning-eda.ipynb`; the headline
issue is that `TotalCharges` is stored as text and contains 11 blank values —
all brand-new customers (tenure = 0) who had not yet been billed. See
`src/data_prep.py` for how each issue is handled.
