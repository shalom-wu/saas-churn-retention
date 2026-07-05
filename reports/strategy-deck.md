# Customer Churn: Cost & Retention Strategy

*Strategy deck (markdown source — the presentation version is
[`strategy-deck.pptx`](strategy-deck.pptx)). Analysis of a 7,043-customer
subscription business; all figures reproducible via `python -m src.run_pipeline`.*

---

## Slide 1 — Title

**Customer churn is a $4.5M problem. Half of it is concentrated where we can act.**

Churn analysis & retention strategy — Shalom Wu

Data: public Telco Customer Churn dataset (Kaggle/IBM), framed as a
subscription/SaaS business · 7,043 customers · $456K MRR

---

## Slide 2 — The problem, in revenue terms

**26.5% of the customer book churned — walking out with 31% of MRR.**

- 1,869 of 7,043 customers churned → **$139K MRR lost** (churners skew
  premium: they average $74/month vs $61 for those who stay)
- Annualized, that is **$1.67M of recurring revenue** if none is replaced
- Full economic cost — foregone customer lifetime value plus the cost of
  acquiring replacements — is **$4.5M** (defensible range $3.3M–$6.3M)
- Blended monthly churn hazard is ~0.8% (healthy by SaaS benchmarks); the
  problem is not the average — it is the **month-to-month segment at ~2.4%/month**

*Visual: `fig_ltv_by_contract.png` — what one lost customer is worth*

---

## Slide 3 — What actually drives churn here

**Five patterns, consistent across descriptive cuts and two predictive models
(logistic regression and XGBoost, test ROC-AUC 0.84):**

1. **Contract type is the fault line** — month-to-month churns at 43% vs 11%
   (one-year) and 3% (two-year). 55% of the book is month-to-month.
2. **Risk is front-loaded** — 53% churn in the first 6 months; new
   month-to-month customers churn at 55%
3. **The premium tier leaks most** — churn peaks at 38% in the $70–90 tier
   (mostly fiber customers), and the $70+ tiers hold 71% of MRR. Fiber
   *raises* churn risk after controlling for everything else: a
   **price/value problem, not a customer-quality problem**
4. **Add-ons anchor customers** — churn falls monotonically from 52% (no
   add-ons) to 5% (all six); support-type add-ons matter most
5. **Electronic check is a red flag** — 45% churn vs 15–19% for automatic
   payment methods

*Visuals: `fig_contract_tenure_heatmap.png`, `fig_shap_summary.png`*

---

## Slide 4 — The cost of doing nothing

**Each year of inaction repeats a ~$4.5M loss — and it is concentrated.**

| At-risk segment (overlapping) | Customers | Churn rate | MRR at stake |
|---|---|---|---|
| New month-to-month (≤12m tenure) | 1,994 | 51% | $116K |
| Month-to-month + electronic check | 1,850 | 54% | $139K |
| Fiber, no support/security add-ons | 1,765 | 55% | $152K |
| Premium ($90+), first year | 219 | **76%** | $21K |
| *Whole book (reference)* | *7,043* | *26.5%* | *$456K* |

- Cost per lost customer: **$2,061** (month-to-month) to **$2,887** (one-year),
  including replacement acquisition cost (~$400/customer)
- Sensitivity: even with every assumption at its most favorable, the churned
  cohort cost **$3.3M** (tornado: gross margin and churn hazard move the
  estimate most; CAC least)

*Visuals: `fig_risk_segments.png`, `fig_cost_of_churn_sensitivity.png`*

---

## Slide 5 — Three intervention options

| | A — Contract-shift incentive | B — Model-targeted saves | C — Premium onboarding bundle |
|---|---|---|---|
| **What** | "12 months for the price of 11" offer to move month-to-month customers to annual contracts | Score the book monthly; retention offers to the riskiest 20% | Bundle tech support + security free for 6 months for new fiber customers |
| **Why it works** | Annual contract economics add ~$830 PV per customer (LTV $1,661 → $2,487) | Model finds churners at 2.5x random: 67% precision at 20% depth | Support add-ons show the steepest retention gradient (52% → 5%) |
| **Year-1 net PV (conservative)** | **~$134K** (10% take-up, 50% deadweight haircut) | **~$231K** (15% save rate among true risks) | **~$37K** (pilot of 500; 5pp churn reduction) |
| **ROI** | ~6x | ~4.7x | ~3.4x |
| **Key risk** | Discounts customers who would have stayed anyway | Offer fatigue; model precision decays without retraining | Add-on effect may be self-selection, not causal |
| **Confidence** | High (mechanical LTV math) | Medium-high (model validated out-of-sample) | Medium (needs A/B test) |

All three are self-funding under conservative assumptions; none requires new
data infrastructure.

---

## Slide 6 — Recommendation & expected ROI

**Run A + B together; pilot C. Expected year-1 net impact ~$0.4M PV,
attacking a $4.5M/year problem.**

- **Now:** launch the contract-shift offer (A) to all 3,875 month-to-month
  customers, prioritized by model score (B) so the riskiest hear first —
  the offers share one campaign
- **Quarterly:** rescore and rerun; track save rate and take-up against the
  assumptions below
- **Pilot:** onboarding bundle (C) as a 500-customer A/B test before scaling

**Stated assumptions behind the ROI (deliberately conservative):**

| Assumption | Value | Basis |
|---|---|---|
| Contract-offer take-up | 10% | low end of published win-back/upgrade campaign rates |
| Deadweight haircut on A | 50% | half of converters assumed would have stayed anyway |
| Save rate among true churn risks | 15% | retention campaigns typically save 10–30% |
| Value per save | $2,061 | month-to-month cost-per-churn (the conservative segment figure) |
| Offer + ops cost | ~$88K yr-1 | one free month per conversion + $150/accepted save offer + ops |

If realized rates land mid-range instead of low-end, year-1 net impact
roughly doubles to ~$0.8M. Downside floor: every component priced above is
capped and self-limiting (offers only pay out on acceptance).

---

## Slide 7 — Appendix: methodology & caveats

**Method in one breath:** exposure-based churn hazard → capped expected
lifetime → discounted LTV (70% gross margin, 10% discount rate, $400
replacement CAC) → cost of churn = foregone LTV + replacement; churn
prediction via class-weighted logistic regression and shallow XGBoost on an
80/20 stratified split; drivers via SHAP + standardized coefficients.

**Caveats stated plainly:**

- **Snapshot dataset** — no event timestamps; production would need
  point-in-time features and out-of-time validation
- **Label window unspecified** — cohort framings used throughout; the 26.5%
  is not a monthly rate
- **Margin, CAC, discount rate are SaaS benchmarks**, not company actuals —
  every number lives in `src/config.py` and the tornado shows the swing
- **Correlation ≠ causation** — contract type is partly self-selection;
  intervention effects use haircuts and pilots, not point estimates
- **Telecom data, SaaS framing** — the structure transfers; the specific
  coefficients would not. The method is the portable part.
- Model ceiling (~0.84 AUC) reflects missing behavioral features (usage,
  tickets, payment failures), not modeling choices

*Full detail: `reports/model-report.md`, notebooks 01–03*
