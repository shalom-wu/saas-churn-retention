"""Central configuration: paths, business assumptions, and visual style.

Every business assumption used in the LTV / cost-of-churn model lives here so
it can be challenged and changed in one place. Sources for each number are
noted inline and discussed in reports/model-report.md.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = PROJECT_ROOT / "data" / "raw" / "telco-customer-churn.csv"
PROCESSED_DATA = PROJECT_ROOT / "data" / "processed" / "churn_clean.csv"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
REPORTS_DIR = PROJECT_ROOT / "reports"

# ---------------------------------------------------------------------------
# Business assumptions for the LTV / cost-of-churn model
# ---------------------------------------------------------------------------
# Gross margin on subscription revenue. Public SaaS companies report gross
# margins of roughly 68-78% (median ~73-75% in most annual SaaS benchmark
# reports, e.g. KeyBanc/OpenView surveys). 70% is used as a slightly
# conservative base case.
GROSS_MARGIN = 0.70

# Customer acquisition cost (CAC) to replace a churned customer. Calibrated
# from the CAC-payback benchmark: healthy SMB-focused subscription businesses
# recover CAC in ~5-12 months of gross profit. At this book's average revenue
# (~$65/month) and 70% margin, monthly gross profit is ~$45, implying a CAC
# of roughly $230-$550. $400 (~9 months payback) is the base case.
REPLACEMENT_CAC = 400.0

# Annual discount rate applied to future cash flows in the LTV calculation.
ANNUAL_DISCOUNT_RATE = 0.10

# Expected-lifetime cap, in months. Lifetimes are estimated as 1 / monthly
# churn hazard; for very sticky segments this can extrapolate far beyond the
# 72-month observation window in the data, so it is capped there.
LIFETIME_CAP_MONTHS = 72

# Sensitivity ranges (low, base, high) used in the cost-of-churn model.
SENSITIVITY = {
    "gross_margin": (0.60, GROSS_MARGIN, 0.80),
    "replacement_cac": (250.0, REPLACEMENT_CAC, 700.0),
    "hazard_multiplier": (0.80, 1.00, 1.20),
}

# ---------------------------------------------------------------------------
# Modeling
# ---------------------------------------------------------------------------
RANDOM_STATE = 42
TEST_SIZE = 0.20

# ---------------------------------------------------------------------------
# Visual identity (single palette used across every figure and the deck)
# ---------------------------------------------------------------------------
PALETTE = {
    "churn": "#D64550",      # red — churned / at risk / cost
    "retain": "#1F7A8C",     # teal — retained / healthy / revenue
    "accent": "#F4A259",     # amber — highlights, callouts
    "neutral": "#9AA5B1",    # grey — context, de-emphasised series
    "dark": "#26343F",       # near-black — text, axis labels
}

# Sequential ramp for ordered categories (light -> dark teal)
SEQUENTIAL = ["#BFD9E0", "#8FBFCB", "#5FA3B4", "#33879D", "#1F7A8C"]
