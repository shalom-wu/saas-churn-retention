"""Customer lifetime value (LTV) and cost-of-churn model.

Approach
--------
1. **Monthly churn hazard.** The churn label is a snapshot ("this customer
   left recently"), not a rate, so churned-count / customer-count is *not* a
   monthly churn rate. Instead the hazard is estimated on an exposure basis:

       hazard = churn events / total customer-months observed

   i.e. each customer contributes their tenure in months to the denominator.
   This is the standard "events per unit exposure" estimator and assumes a
   constant hazard within a segment (a real limitation, discussed in
   reports/model-report.md — churn is actually front-loaded in tenure).

2. **Expected lifetime.** With a constant hazard h, expected lifetime is
   1/h months, capped at the 72-month observation window so sticky segments
   are not extrapolated beyond what the data can support.

3. **LTV.** Discounted stream of gross profit over the expected lifetime:

       LTV = monthly_revenue x gross_margin x annuity_factor(lifetime)

4. **Cost of one churn event.** The gross profit the business would have
   earned had the customer stayed a typical lifetime for their segment, plus
   the acquisition cost of replacing them:

       cost_of_churn = remaining_LTV + replacement_CAC

All business assumptions (margin, CAC, discount rate, caps) live in
``src.config`` and are stress-tested in :func:`sensitivity_table`.
"""

import itertools

import numpy as np
import pandas as pd

from src.config import (
    ANNUAL_DISCOUNT_RATE,
    GROSS_MARGIN,
    LIFETIME_CAP_MONTHS,
    REPLACEMENT_CAC,
    SENSITIVITY,
)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

def monthly_churn_hazard(df: pd.DataFrame, by: str | None = None):
    """Churn events per customer-month of exposure.

    Customers with tenure 0 (joined this month) contribute one month of
    exposure so the denominator can never be zero.
    """
    exposure = df["tenure"].clip(lower=1)
    if by is None:
        return df["churn_flag"].sum() / exposure.sum()
    g = df.assign(exposure=exposure).groupby(by, observed=True)
    return g["churn_flag"].sum() / g["exposure"].sum()


def expected_lifetime_months(hazard, cap: int = LIFETIME_CAP_MONTHS):
    """Expected customer lifetime under a constant monthly hazard, capped at
    the observation window. Zero-hazard segments hit the cap."""
    with np.errstate(divide="ignore"):
        life = np.minimum(1.0 / np.asarray(hazard, dtype=float), cap)
    if isinstance(hazard, pd.Series):
        return pd.Series(life, index=hazard.index)
    return life


def monthly_discount_rate(annual_rate: float = ANNUAL_DISCOUNT_RATE) -> float:
    return (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0


def annuity_factor(n_months, monthly_rate: float | None = None):
    """Present value of $1/month for n months (ordinary annuity)."""
    d = monthly_discount_rate() if monthly_rate is None else monthly_rate
    n = np.asarray(n_months, dtype=float)
    if d == 0:
        return n
    return (1.0 - (1.0 + d) ** -n) / d


def discounted_ltv(monthly_revenue, lifetime_months,
                   gross_margin: float = GROSS_MARGIN,
                   monthly_rate: float | None = None):
    """Present value of gross profit over the expected lifetime."""
    return (np.asarray(monthly_revenue, dtype=float) * gross_margin
            * annuity_factor(lifetime_months, monthly_rate))


# ---------------------------------------------------------------------------
# Segment-level LTV and the cost-of-churn model
# ---------------------------------------------------------------------------

def ltv_by_segment(df: pd.DataFrame, by: str = "Contract") -> pd.DataFrame:
    """LTV economics per segment: hazard, lifetime, average LTV, and the
    all-in cost of losing one customer."""
    hazard = monthly_churn_hazard(df, by=by)
    lifetime = expected_lifetime_months(hazard)
    avg_rev = df.groupby(by, observed=True)["MonthlyCharges"].mean()
    ltv = discounted_ltv(avg_rev, lifetime)
    out = pd.DataFrame({
        "customers": df.groupby(by, observed=True).size(),
        "avg_monthly_revenue": avg_rev,
        "monthly_churn_hazard": hazard,
        "expected_lifetime_months": lifetime,
        "avg_ltv": ltv,
        "cost_per_churn": ltv + REPLACEMENT_CAC,
    })
    return out


def cost_of_churn_summary(df: pd.DataFrame,
                          gross_margin: float = GROSS_MARGIN,
                          replacement_cac: float = REPLACEMENT_CAC,
                          hazard_multiplier: float = 1.0) -> dict:
    """Dollarize what the observed churned cohort cost the business.

    For each churned customer, the foregone value is the discounted LTV a
    comparable customer (same contract type) would have delivered, plus the
    cost of acquiring a replacement. Reported alongside simpler headline
    numbers (lost MRR, annualized lost revenue) that need fewer assumptions.
    """
    churned = df[df["churn_flag"] == 1]

    hazard = monthly_churn_hazard(df, by="Contract") * hazard_multiplier
    lifetime = expected_lifetime_months(hazard)
    lifetime_per_row = churned["Contract"].map(lifetime).astype(float)

    foregone_ltv = discounted_ltv(churned["MonthlyCharges"], lifetime_per_row,
                                  gross_margin)

    lost_mrr = churned["MonthlyCharges"].sum()
    return {
        "churned_customers": int(len(churned)),
        "lost_mrr": float(lost_mrr),
        "annualized_lost_revenue": float(lost_mrr * 12),
        "foregone_ltv": float(foregone_ltv.sum()),
        "replacement_cac_total": float(replacement_cac * len(churned)),
        "total_cost_of_churn": float(foregone_ltv.sum()
                                     + replacement_cac * len(churned)),
        "avg_cost_per_churned_customer": float(
            (foregone_ltv.sum() + replacement_cac * len(churned))
            / len(churned)),
    }


def sensitivity_table(df: pd.DataFrame) -> pd.DataFrame:
    """Total cost of churn across the full grid of assumption ranges in
    ``config.SENSITIVITY`` — shows how much the headline number moves when
    each assumption is pushed to its low/high value."""
    rows = []
    grid = itertools.product(SENSITIVITY["gross_margin"],
                             SENSITIVITY["replacement_cac"],
                             SENSITIVITY["hazard_multiplier"])
    for margin, cac, hmult in grid:
        s = cost_of_churn_summary(df, gross_margin=margin,
                                  replacement_cac=cac,
                                  hazard_multiplier=hmult)
        rows.append({
            "gross_margin": margin,
            "replacement_cac": cac,
            "hazard_multiplier": hmult,
            "total_cost_of_churn": s["total_cost_of_churn"],
            "avg_cost_per_churn": s["avg_cost_per_churned_customer"],
        })
    return pd.DataFrame(rows)


def one_way_sensitivity(df: pd.DataFrame) -> pd.DataFrame:
    """Move one assumption at a time to its low/high value (others at base)
    and record the total cost of churn — feeds the tornado chart."""
    base = cost_of_churn_summary(df)["total_cost_of_churn"]
    rows = []
    labels = {
        "gross_margin": "Gross margin",
        "replacement_cac": "Replacement CAC",
        "hazard_multiplier": "Churn hazard",
    }
    for param, (low, _, high) in SENSITIVITY.items():
        low_total = cost_of_churn_summary(df, **{param: low})["total_cost_of_churn"]
        high_total = cost_of_churn_summary(df, **{param: high})["total_cost_of_churn"]
        rows.append({"assumption": labels[param], "low": low_total,
                     "base": base, "high": high_total})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def plot_ltv_by_segment(seg_table: pd.DataFrame) -> str:
    """Average LTV and all-in cost per churn by contract type."""
    import matplotlib.pyplot as plt

    from src.config import PALETTE
    from src.visuals import apply_style, save_fig

    apply_style()
    t = seg_table.sort_values("avg_ltv")
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    y = np.arange(len(t))
    ax.barh(y + 0.2, t["avg_ltv"], height=0.38, color=PALETTE["retain"],
            label="Avg customer LTV (discounted gross profit)")
    ax.barh(y - 0.2, t["cost_per_churn"], height=0.38, color=PALETTE["churn"],
            label="All-in cost of losing one customer (LTV + replacement CAC)")
    ax.set_yticks(y, t.index.astype(str))
    for yi, (ltv_v, cost_v) in enumerate(zip(t["avg_ltv"], t["cost_per_churn"])):
        ax.annotate(f"${ltv_v:,.0f}", xy=(ltv_v, yi + 0.2), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=9,
                    color=PALETTE["dark"])
        ax.annotate(f"${cost_v:,.0f}", xy=(cost_v, yi - 0.2), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=9,
                    color=PALETTE["dark"], fontweight="bold")
    ax.set_title("What one lost customer is worth, by contract type")
    ax.set_xlabel("US$ (present value)")
    ax.xaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    ax.margins(x=0.12)
    # Legend below the axes so it can never collide with the bars
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.14), fontsize=9)
    ax.annotate("Source: Telco Customer Churn dataset (Kaggle / IBM), n=7,043",
                xy=(0, -0.42), xycoords="axes fraction",
                fontsize=8, color=PALETTE["neutral"], ha="left")
    return save_fig(fig, "fig_ltv_by_contract")


def plot_sensitivity_tornado(df: pd.DataFrame) -> str:
    """Tornado chart: how the annual cost-of-churn estimate moves when each
    assumption is pushed to its low/high value."""
    import matplotlib.pyplot as plt

    from src.config import PALETTE
    from src.visuals import add_source_note, apply_style, save_fig

    apply_style()
    t = one_way_sensitivity(df)
    t["spread"] = (t[["low", "high"]].max(axis=1)
                   - t[["low", "high"]].min(axis=1))
    t = t.sort_values("spread")
    base = t["base"].iloc[0]

    fig, ax = plt.subplots(figsize=(8.5, 4))
    y = np.arange(len(t))
    for yi, row in zip(y, t.itertuples()):
        lo, hi = sorted([row.low, row.high])
        ax.barh(yi, hi - lo, left=lo, color=PALETTE["accent"], height=0.55)
        ax.annotate(f"${lo/1e6:,.1f}M", xy=(lo, yi), xytext=(-6, 0),
                    textcoords="offset points", va="center", ha="right",
                    fontsize=9, color=PALETTE["dark"])
        ax.annotate(f"${hi/1e6:,.1f}M", xy=(hi, yi), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=9,
                    color=PALETTE["dark"])
    ax.axvline(base, color=PALETTE["dark"], linewidth=1.2)
    ax.annotate(f"base case ${base/1e6:,.1f}M",
                xy=(base, 1.02), xycoords=("data", "axes fraction"),
                xytext=(0, 2), textcoords="offset points", ha="center",
                fontsize=9, color=PALETTE["dark"], fontweight="bold")
    ax.set_yticks(y, t["assumption"])
    ax.set_title("Cost-of-churn estimate under low/high assumptions (tornado)")
    ax.set_xlabel("Total cost of the churned cohort (US$)")
    ax.xaxis.set_major_formatter(lambda x, _: f"${x/1e6:,.1f}M")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    # Explicit x-limits with padding so the $ labels at each bar end never
    # collide with the y tick labels or the plot edge
    lo_min = t[["low", "high"]].min().min()
    hi_max = t[["low", "high"]].max().max()
    span = hi_max - lo_min
    ax.set_xlim(lo_min - 0.14 * span, hi_max + 0.14 * span)
    add_source_note(ax, "One-way sensitivity; remaining assumptions held at base case")
    return save_fig(fig, "fig_cost_of_churn_sensitivity")
