"""Descriptive analysis: churn rates by segment, and at-risk profiles.

Every figure uses the shared style in ``src.visuals`` and is exported as a
standalone PNG under ``reports/figures`` so it can be dropped straight into
the deck or README.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config import PALETTE, SEQUENTIAL
from src.visuals import add_source_note, annotate_bars, apply_style, save_fig


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def churn_rate_by(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Churn rate, customer count and MRR share for each level of `col`."""
    total_mrr = df["MonthlyCharges"].sum()
    out = (
        df.groupby(col, observed=True)
        .agg(customers=("churn_flag", "size"),
             churn_rate=("churn_flag", "mean"),
             mrr=("MonthlyCharges", "sum"))
        .assign(mrr_share=lambda t: t["mrr"] / total_mrr)
    )
    return out


def at_risk_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Named at-risk customer profiles, built from the descriptive patterns.

    These are deliberately simple, describable segments (the kind a retention
    team could actually target), not model-derived clusters. Segments can
    overlap; each row is evaluated independently against the full book.
    """
    m2m = df["Contract"] == "Month-to-month"
    segments = {
        "New month-to-month (tenure <= 12m)":
            m2m & (df["tenure"] <= 12),
        "Month-to-month + electronic check":
            m2m & (df["PaymentMethod"] == "Electronic check"),
        "Fiber, no support/security add-ons":
            (df["InternetService"] == "Fiber optic")
            & (df["OnlineSecurity"] == "No") & (df["TechSupport"] == "No"),
        "Premium charges ($90+), first year":
            (df["MonthlyCharges"] >= 90) & (df["tenure"] <= 12),
        "Whole customer base (reference)":
            pd.Series(True, index=df.index),
    }
    rows = []
    for name, mask in segments.items():
        seg = df[mask]
        rows.append({
            "segment": name,
            "customers": len(seg),
            "share_of_base": len(seg) / len(df),
            "churn_rate": seg["churn_flag"].mean(),
            "avg_monthly_charge": seg["MonthlyCharges"].mean(),
            "mrr": seg["MonthlyCharges"].sum(),
            "mrr_lost_to_churn": seg.loc[seg["churn_flag"] == 1, "MonthlyCharges"].sum(),
        })
    return pd.DataFrame(rows).set_index("segment")


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def _churn_bar(table: pd.DataFrame, title: str, xlabel: str, name: str,
               highlight_over: float = 0.35) -> str:
    """Horizontal bar chart of churn rate by category, worst highlighted."""
    apply_style()
    table = table.sort_values("churn_rate")
    colors = [PALETTE["churn"] if r >= highlight_over else PALETTE["retain"]
              for r in table["churn_rate"]]
    labels = [f"{cat}\n(n={n:,})" for cat, n in
              zip(table.index.astype(str), table["customers"])]
    fig, ax = plt.subplots(figsize=(8, 0.7 * len(table) + 2))
    ax.barh(labels, table["churn_rate"], color=colors)
    for i, rate in enumerate(table["churn_rate"]):
        ax.annotate(f"{rate:.0%}", xy=(rate, i), xytext=(4, 0),
                    textcoords="offset points", va="center",
                    fontsize=10, color=PALETTE["dark"], fontweight="bold")
    ax.set_title(title)
    ax.set_xlabel("Churn rate")
    ax.set_ylabel(xlabel)
    ax.xaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    add_source_note(ax)
    return save_fig(fig, name)


def plot_churn_by_contract(df: pd.DataFrame) -> str:
    t = churn_rate_by(df, "Contract")
    return _churn_bar(t, "Month-to-month contracts churn at 15x the rate of two-year deals",
                      "Contract type", "fig_churn_by_contract")


def plot_churn_by_payment(df: pd.DataFrame) -> str:
    t = churn_rate_by(df, "PaymentMethod")
    return _churn_bar(t, "Electronic-check payers churn at more than double the base rate",
                      "Payment method", "fig_churn_by_payment_method")


def plot_churn_by_tenure(df: pd.DataFrame) -> str:
    apply_style()
    t = churn_rate_by(df, "tenure_band")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(t.index.astype(str), t["churn_rate"], color=SEQUENTIAL[::-1])
    annotate_bars(ax)
    ax.set_title("Churn risk is front-loaded: over half of first-half-year customers leave")
    ax.set_xlabel("Tenure")
    ax.set_ylabel("Churn rate")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    add_source_note(ax)
    return save_fig(fig, "fig_churn_by_tenure_band")


def plot_churn_by_charge_tier(df: pd.DataFrame) -> str:
    apply_style()
    t = churn_rate_by(df, "charge_tier")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = [PALETTE["retain"]] * len(t)
    colors[list(t.index.astype(str)).index("$70-90")] = PALETTE["churn"]
    ax.bar(t.index.astype(str), t["churn_rate"], color=colors)
    annotate_bars(ax)
    ax.set_title("Churn concentrates in the $70-90 tier, not the cheapest plans")
    ax.set_xlabel("Monthly charge tier")
    ax.set_ylabel("Churn rate")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    add_source_note(ax)
    return save_fig(fig, "fig_churn_by_charge_tier")


def plot_churn_by_services(df: pd.DataFrame) -> str:
    """Churn by number of add-on services, split by internet customers only
    (customers without internet can't buy add-ons, so including them would
    conflate product depth with product mix)."""
    apply_style()
    internet = df[df["InternetService"] != "No"]
    t = churn_rate_by(internet, "n_addon_services")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(t.index.astype(str), t["churn_rate"], color=PALETTE["retain"])
    for i, rate in enumerate(t["churn_rate"]):
        ax.annotate(f"{rate:.0%}", xy=(i, rate), xytext=(0, 4),
                    textcoords="offset points", ha="center",
                    fontsize=10, color=PALETTE["dark"])
    ax.set_title("Every add-on service deepens retention (internet customers)")
    ax.set_xlabel("Number of add-on services (0-6)")
    ax.set_ylabel("Churn rate")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    add_source_note(ax, "Source: Telco Customer Churn dataset (Kaggle / IBM); internet customers only, n=5,517")
    return save_fig(fig, "fig_churn_by_addon_services")


def plot_contract_tenure_heatmap(df: pd.DataFrame) -> str:
    """Contract x tenure churn heatmap — the interaction behind the story."""
    import seaborn as sns
    apply_style()
    pivot = df.pivot_table(index="Contract", columns="tenure_band",
                           values="churn_flag", aggfunc="mean", observed=True)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    sns.heatmap(pivot, annot=True, fmt=".0%", cmap="RdYlBu_r",
                vmin=0, vmax=0.6, linewidths=0.5, linecolor="white",
                cbar_kws={"label": "Churn rate", "format": lambda x, _: f"{x:.0%}"},
                ax=ax)
    ax.set_title("The risk pocket: new customers on month-to-month contracts")
    ax.set_xlabel("Tenure")
    ax.set_ylabel("")
    return save_fig(fig, "fig_contract_tenure_heatmap")


def plot_risk_segments(seg: pd.DataFrame) -> str:
    """Bubble chart: segment size vs churn rate, bubble = MRR at stake."""
    apply_style()
    plot_df = seg.drop(index="Whole customer base (reference)")
    base_rate = seg.loc["Whole customer base (reference)", "churn_rate"]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.scatter(plot_df["customers"], plot_df["churn_rate"],
               s=plot_df["mrr"] / 150, color=PALETTE["churn"], alpha=0.55,
               edgecolor=PALETTE["dark"], linewidth=1)
    # Alternate labels above/below the bubbles so the clustered segments
    # don't overlap each other.
    offsets = [(0, 26), (0, -40), (0, 26), (0, -40)]
    for (name, row), (dx, dy) in zip(
            plot_df.sort_values("customers").iterrows(), offsets):
        ax.annotate(name, xy=(row["customers"], row["churn_rate"]),
                    xytext=(dx, dy), textcoords="offset points",
                    ha="center", fontsize=9, color=PALETTE["dark"])
    ax.margins(x=0.15)
    ax.axhline(base_rate, color=PALETTE["neutral"], linestyle="--", linewidth=1)
    ax.annotate(f"base rate {base_rate:.0%}", xy=(0.99, base_rate),
                xycoords=("axes fraction", "data"), xytext=(0, 4),
                textcoords="offset points", ha="right",
                fontsize=9, color=PALETTE["neutral"])
    ax.set_title("At-risk segments: all far above the base churn rate\n(bubble size = monthly recurring revenue at stake)")
    ax.set_xlabel("Customers in segment")
    ax.set_ylabel("Churn rate")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0%}")
    ax.set_ylim(0, plot_df["churn_rate"].max() * 1.25)
    add_source_note(ax)
    return save_fig(fig, "fig_risk_segments")


def run_eda(df: pd.DataFrame) -> dict:
    """Generate all descriptive figures; returns {figure name: path}."""
    seg = at_risk_segments(df)
    return {
        "contract": plot_churn_by_contract(df),
        "tenure": plot_churn_by_tenure(df),
        "payment": plot_churn_by_payment(df),
        "charge_tier": plot_churn_by_charge_tier(df),
        "services": plot_churn_by_services(df),
        "heatmap": plot_contract_tenure_heatmap(df),
        "segments": plot_risk_segments(seg),
    }
