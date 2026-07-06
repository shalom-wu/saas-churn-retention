# Explain It to Me: The Churn Project, No Jargon Required

This guide explains the whole project to someone with zero data science
background — what the business problem is, what I built, how the code works,
and how I'd answer the questions people actually ask about it. Technical terms
are **bolded and defined the first time they appear**, and there's a
[glossary](#glossary) at the end.

---

## Section 1 — The plain-English walkthrough

### Start with the business question, not the data

Imagine you run a subscription business — customers pay you monthly, like
Netflix or a software product. Some fraction of them cancel every month. That
cancelling is called **churn**, and it's the quiet killer of subscription
businesses: losing a customer doesn't just cost you next month's payment, it
costs you *every* payment they would have made for years, plus the marketing
money you'll spend recruiting someone to replace them.

So the questions any operator would ask are:

1. **How bad is our churn, in dollars?** Not percentages — dollars.
2. **Who exactly is leaving?** Is it random, or concentrated in groups we can describe?
3. **Can we predict who's about to leave**, so we can do something before they go?
4. **What should we actually do**, and would it pay for itself?

This project answers all four, in that order.

### The data

I used a public dataset of 7,043 customers from a telecom company (the
Telco Customer Churn dataset — a well-known practice dataset originally
published by IBM). Each row is one customer: how long they've been a customer,
what they pay monthly, what kind of contract they're on (month-to-month or
annual), which services they subscribe to, how they pay, and — crucially —
whether they churned.

One honest framing note: it's telecom data, but I've treated it as a generic
subscription/SaaS business, because structurally they're the same machine —
recurring monthly payments, optional add-ons, contracts, cancellations. The
README and every report say this out loud rather than hiding it.

### What I found (the headlines)

- **26.5% of the customers in this snapshot churned**, and they were the
  *more expensive* customers — averaging $74/month versus $61 for those who
  stayed.
- **Churn is wildly concentrated.** Customers on month-to-month contracts
  churn at 43%; customers on two-year contracts churn at 3%. New customers
  churn far more than tenured ones — over half of customers in their first
  six months leave.
- **The total damage is about $4.5 million** for that churned group, once you
  count the profit they would have generated had they stayed, plus the cost
  of acquiring replacements. I stress-tested that number: under every
  reasonable set of assumptions it stays between $3.3M and $6.3M. Big number,
  any way you slice it.
- **A model can find the leavers before they leave.** My model ranks
  customers by churn risk; among the riskiest 10% it flags, about 77% really
  are churners — nearly three times better than guessing.
- **There's a self-funding fix.** Nudging month-to-month customers onto
  annual contracts and aiming retention offers at the riskiest customers
  yields roughly $0.4M of net value in year one under deliberately
  conservative assumptions — about a 5x return on what the campaign costs.

### What I actually built

Three things, layered on top of each other:

1. **A cleaned dataset and descriptive analysis.** Before anything fancy: fix
   the data problems (there were a few — see Section 3), then compute churn
   rates by contract type, customer age, price tier, payment method, and
   service bundle. Most of the business story is visible right here, no
   machine learning needed.

2. **A cost model.** This converts churn percentages into dollars. It
   estimates each customer's **LTV (lifetime value)** — the total profit a
   customer generates over their whole time with the business — and from
   that, the cost of losing them. Every assumption (profit margins, cost to
   acquire a customer) is written down in one file, sourced from industry
   benchmarks, and stress-tested.

3. **A prediction model.** Two, actually: a simple one (**logistic
   regression** — a statistical workhorse that estimates each customer's
   churn probability from their attributes) and a fancier one (**XGBoost** —
   a method that combines hundreds of small decision trees). The punchline:
   the fancy model barely beats the simple one, which is itself an honest and
   useful finding — the signal lives in a few strong patterns, not subtle
   interactions.

Then everything funnels into a strategy deck: what's broken, what it costs,
and three costed interventions with a recommendation.

---

## Section 2 — The elevator versions

### 30 seconds

"I analyzed churn for a subscription business — 7,000 customers, about a
quarter of them cancelled. I put a dollar figure on the problem — roughly
$4.5 million in lost lifetime value — then found where it concentrates:
month-to-month customers in their first year, on premium prices. I built a
model that spots likely churners at three times better than chance, and
designed a retention plan that returns about five dollars for every dollar it
costs, under conservative assumptions."

### 2 minutes

Add these beats:

- "The single biggest lever is contract type. Month-to-month customers churn
  at 43%; two-year customers at 3%. That's not a small gap — that's the
  business's fault line, and over half the customer base sits on the wrong
  side of it."
- "I was careful with the dollar figure. Lifetime value calculations can be
  hand-wavy, so I kept every assumption explicit — a 70% gross margin, $400
  to replace a lost customer, future profits discounted — and ran a
  sensitivity analysis. The answer stays between $3.3M and $6.3M no matter
  which reasonable assumptions you pick."
- "For prediction I deliberately built a simple model first. The complex one
  only beat it by half a point of accuracy, which tells you the churn signal
  here is a few strong, actionable patterns — contract, tenure, price — not
  deep magic. I'd rather report that honestly than pretend the neural-net
  fairy visited."
- "The recommendation is three moves: an annual-contract incentive, retention
  offers targeted by the model, and an onboarding bundle pilot — all
  self-funding, all with the assumptions written down."

### 5 minutes

Walk the actual pipeline: data cleaning (the TotalCharges quirk — see
Section 3), the churn-rate cuts, how the hazard-based LTV works and why
snapshot data forces that choice, the class-imbalance problem in evaluation
and why I report precision/recall at campaign depth instead of accuracy, the
SHAP-based driver analysis, then the ROI math on the three interventions —
ending on the limitations: snapshot data, benchmark assumptions,
correlation-not-causation, and how each is handled.

---

## Section 3 — How the code actually works

### The map, and what order to read it in

```
saas-churn-retention/
├── README.md                ← start here (5 min)
├── data-sources.md          ← where the data comes from, how to get it
├── notebooks/               ← the narrative walkthroughs (read 2nd)
│   ├── 01-data-cleaning-eda.ipynb
│   ├── 02-ltv-cost-of-churn.ipynb
│   └── 03-churn-modeling.ipynb
├── src/                     ← the actual logic (read 3rd)
│   ├── config.py            ← every business assumption, one file
│   ├── data_prep.py         ← cleaning + derived features
│   ├── eda.py               ← churn-rate tables + charts
│   ├── ltv.py               ← the money math
│   ├── modeling.py          ← the prediction models
│   ├── visuals.py           ← shared chart styling
│   └── run_pipeline.py      ← runs everything end to end
├── reports/
│   ├── figures/             ← every chart as a standalone PNG
│   ├── strategy-deck.md / .pptx
│   ├── model-report.md      ← honest model performance write-up
│   └── model-metrics.json
├── tests/                   ← automated checks on the logic
└── explainer-guide/         ← you are here
```

Reading order: **README → notebooks (in order) → src modules**. The notebooks
tell the story with the code's results embedded; the `src/` files are where
the logic actually lives. The notebooks deliberately contain almost no logic —
they import functions from `src/` and display what comes back. That's a
design choice: logic that lives in modules can be tested and reused; logic
trapped in notebooks can't.

### What each key piece does, in plain terms

**`src/config.py` — the assumptions file.** Every number a skeptic would want
to challenge (profit margin, replacement cost, discount rate) lives here with
a comment citing its basis. Change a number here and the whole analysis —
charts, deck figures, everything — updates on the next run.

**`src/data_prep.py` — cleaning.** Real data is never clean. Here, the
`TotalCharges` column (total amount ever billed) was stored as *text*, and 11
customers had a blank there. Why? All 11 were brand-new customers who hadn't
been billed yet. The code converts the column to numbers and sets those 11 to
zero — instead of deleting them, because "new customer, nothing billed yet"
is real information, not an error. It also builds the analysis features:
tenure bands (0–6 months, 7–12, ...), price tiers, and a count of add-on
services per customer. It refuses to run (raises an error) if the data looks
different than expected — a tripwire against silent corruption.

**`src/eda.py` — the descriptive analysis.** ("EDA" = **exploratory data
analysis** — systematically looking at the data before modeling.) One
function computes churn rate, customer count, and revenue share for any
grouping; the rest generate the charts. It also defines the four "at-risk
profiles" — describable groups like "month-to-month + pays by electronic
check" that a marketing team could actually target.

**`src/ltv.py` — the money math.** The heart of the project. Three steps:

1. *How fast do customers leave?* You can't just divide churners by customers
   — the data is a snapshot, not a diary. Instead it counts churn events per
   **customer-month** (one customer observed for one month). This gives a
   monthly leaving rate — about 2.4% for month-to-month customers.
2. *How long does a customer last?* One divided by that rate. A 2.4% monthly
   leaving rate implies roughly 42 months of expected lifetime. (Capped at 72
   months — the data only covers six years, so the code refuses to
   extrapolate beyond what it has seen.)
3. *What are they worth?* Monthly payment × profit margin × expected
   lifetime, with future months worth slightly less than near ones (a
   standard finance adjustment called **discounting**). Losing a customer
   costs that lifetime value *plus* the ~$400 it takes to acquire a
   replacement.

The same file contains the **sensitivity analysis**: rerun the whole
calculation with every assumption pushed to its pessimistic and optimistic
ends, and show the range. That's what makes the $4.5M figure defensible
rather than decorative.

**`src/modeling.py` — the prediction.** This is where the machine learning
happens. Conceptually: show the computer 5,600 customers *with* their known
outcomes (stayed/churned), let it learn the patterns, then test it on 1,400
customers it has never seen. Two models are trained — logistic regression
(simple, transparent) and XGBoost (hundreds of small decision trees voting
together). Because only ~27% of customers churn, the code evaluates with
metrics that respect that imbalance — a model that predicts "nobody ever
churns" would be 73% accurate and 100% useless. The most business-relevant
output is the **targeting table**: "if you can only call 20% of customers,
this model gets you two genuine churn-risks out of every three calls."
Finally, **SHAP** analysis opens the black box — for each prediction, it
attributes the risk score across the customer's attributes, so you can see
*why* the model flagged someone.

**`sql/` — the referee.** Four DuckDB scripts (a tiny local database — no
server) that recompute every number this project claims, straight from the
cleaned table: seven data-quality checks, churn-rate views by every segment,
the leaving-rate calculation the LTV model consumes, and a "claim check"
query that reproduces each README headline. If the Python analysis and the
README ever disagreed, this layer is how you'd catch it. It also exports the
small tables the Power BI dashboard reads.

**`power-bi/` — the stakeholder view.** A three-page dashboard (.pbix you
can open in the free Power BI Desktop): the executive retention overview,
churn diagnostics, and a value-and-action page with the LTV figures,
at-risk segments and the three costed interventions. It reads only the
documented exports in `data/powerbi/` — nothing hidden — and the dashboard
itself was generated from code (the text source sits next to the file), so
even the DAX measures are reviewable.

**`tests/` — the safety net.** ~30 automated checks that the cleaning
handles the known data quirks, the LTV math matches hand-computed answers,
and the evaluation logic is correct. Run them with one command (`pytest`);
they pass in about a second. If someone changes a formula and breaks
something, these catch it.

### How to run it, end to end

```
1. git clone <repo> && cd saas-churn-retention
2. pip install -r requirements.txt
3. Download the dataset (link in data-sources.md) to data/raw/telco-customer-churn.csv
4. python -m src.run_pipeline        # regenerates every figure and metric (~1 min)
5. pytest                            # optional: run the checks
```

### If someone technical says "show me the code"

I'd open **`src/ltv.py`** first. It's the most *mine* — the dataset is
public and churn models are a known genre, but the cost-of-churn model with
its exposure-based hazard, capped lifetimes, discounting, and tornado-chart
sensitivity is original analytical work, and the docstring at the top
explains every choice. Then `src/modeling.py` for the honest evaluation
design, and `tests/test_ltv.py` to show the math is verified, not vibes.

---

## Section 4 — Questions people will ask (and spoken answers)

**"Why this dataset? It's not even SaaS."**

> "Because it's real enough to be interesting and public enough to be
> verifiable. It has the full anatomy of a subscription business — contracts,
> add-ons, payment methods, tenure, churn — at a realistic scale. I was
> explicit about the reframing rather than pretending it's something it
> isn't, and the parts that are genuinely mine — the cost model and the
> intervention ROI — don't depend on it being telecom or SaaS."

**"Why logistic regression and XGBoost? Why not deep learning?"**

> "Seven thousand rows of tabular data is exactly where boosted trees and
> regression live, and where deep learning adds complexity without accuracy.
> I actually tested that intuition in miniature: a bigger XGBoost scored
> *worse* than a smaller one on held-out data. The dataset rewards restraint.
> And the baseline matters — if the fancy model hadn't beaten simple
> regression, that itself changes what you deploy."

**"What would you do differently with more time or data?"**

> "Data beats method here. The three things I'd want are timestamps — so I
> could model *when* churn happens with proper survival analysis instead of
> assuming a constant leaving rate — behavioral signals like usage frequency
> and support tickets, which are the strongest churn predictors in every real
> subscription business, and the company's actual margin and acquisition
> costs to replace my benchmark assumptions. With time: an A/B test of the
> retention offers, because prediction tells you who's at risk, not whether
> the offer works."

**"How confident are you in the numbers?"**

> "Different numbers, different confidence — and I've tried to label which is
> which. The descriptive facts, like 43% versus 3% churn by contract type,
> are just counting; I'm fully confident. The model's performance is measured
> on customers it never saw, with cross-validation agreeing; that's solid.
> The dollar figures depend on stated assumptions, which is why they come as
> a range — $3.3M to $6.3M — rather than a point. And the intervention ROI is
> the most uncertain, which is why every assumption there is conservative and
> the plan includes measuring actual take-up before scaling."

**"What's the biggest limitation?"**

> "The data is a snapshot, not a history. I know who churned but not exactly
> when, so the lifetime math assumes a constant leaving rate when churn is
> really front-loaded. I handled that with cohort framing, caps, and
> sensitivity ranges — but with timestamped data I'd build a proper survival
> model, and that's the first upgrade I'd make."

**"How do SQL and Power BI fit in?"**

> "SQL is my validation layer — DuckDB views that recompute every churn rate
> and KPI from the cleaned table, including one query that literally
> re-derives each number quoted in the README. Python keeps the parts SQL is
> wrong for: discounted cash-flow math and the classifier. Power BI is the
> presentation layer on top, reading only the exported tables. Three tools,
> one set of definitions — and the SQL is the referee if anything drifts."

**"Walk me through the LTV function."** *(the most likely code question)*

> "Three functions chained together. `monthly_churn_hazard` counts churn
> events divided by total customer-months observed — that's the leaving rate.
> `expected_lifetime_months` inverts it: one over the rate, capped at 72
> months so I never extrapolate past the data window. `discounted_ltv`
> multiplies monthly revenue by margin by an annuity factor — the standard
> present-value formula for a stream of payments. Losing a customer costs
> that, plus $400 to replace them. Every constant comes from `config.py`,
> nothing is hard-coded, and each function has a unit test with a
> hand-computed answer."

---

## Glossary

| Term | Plain-English meaning |
|---|---|
| **Churn** | A customer cancelling. "Churn rate" = fraction of customers who cancel in some period. |
| **MRR** | Monthly recurring revenue — subscription money that arrives every month. |
| **ARPU** | Average revenue per user — average monthly payment per customer. |
| **LTV (lifetime value)** | Total profit one customer generates over their entire time as a customer. |
| **CAC** | Customer acquisition cost — marketing/sales money to win one new customer. |
| **Gross margin** | The share of revenue left after direct costs of serving the customer. 70% here. |
| **Discounting / present value** | Money later is worth slightly less than money now; discounting converts future dollars to today's terms. |
| **Hazard (churn hazard)** | The leaving rate — probability a current customer cancels in a given month. |
| **Customer-month** | One customer observed for one month; the unit for measuring exposure. |
| **Tenure** | How many months a customer has been with the business. |
| **Cohort** | A group of customers considered together (e.g. "everyone who churned"). |
| **EDA** | Exploratory data analysis — systematically summarizing data before modeling. |
| **Logistic regression** | A statistical model that turns customer attributes into a probability (here: of churning). |
| **XGBoost / gradient boosting** | A model built from hundreds of small decision trees, each correcting the previous ones' mistakes. |
| **Decision tree** | A flowchart of yes/no questions ("tenure < 6 months?") ending in a prediction. |
| **Class imbalance** | When one outcome is much rarer than the other (27% churn vs 73% stay), which breaks naive accuracy. |
| **Precision** | Of the customers the model flagged, the share that were genuinely churners. |
| **Recall** | Of all genuine churners, the share the model managed to flag. |
| **ROC-AUC / PR-AUC** | Scores (0–1) for how well the model *ranks* risky customers above safe ones; higher is better, 0.5 = coin flip (for ROC-AUC). |
| **Lift** | How much better than random guessing the model's targeting is (2.9x = nearly three times better). |
| **SHAP** | A technique that splits each individual prediction into per-attribute contributions — "why did the model flag *this* customer?" |
| **Train/test split** | Teaching the model on one part of the data and grading it on a held-back part it never saw. |
| **Cross-validation** | Repeating the train/test exercise several ways and averaging, to check stability. |
| **Sensitivity analysis** | Rerunning a calculation with each assumption pushed high and low, to see how much the answer moves. |
| **Tornado chart** | The chart that displays a sensitivity analysis — one horizontal bar per assumption, widest (most influential) on top. |
| **Deadweight** | Spending an incentive on someone who would have done what you wanted anyway. |
| **A/B test** | Giving an offer to a random half of a group and comparing outcomes against the other half — the honest way to measure whether an intervention *causes* anything. |
