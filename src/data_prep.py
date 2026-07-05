"""Load and clean the raw churn dataset, and derive analysis features.

Data quality issues found in the raw file (documented in
notebooks/01-data-cleaning-eda.ipynb):

1. ``TotalCharges`` is stored as text and contains 11 blank (single-space)
   values. All 11 belong to customers with ``tenure == 0`` — brand-new
   accounts that had not yet been billed. They are set to 0.0 rather than
   dropped, because "new customer, nothing billed yet" is real information.
2. ``SeniorCitizen`` is encoded 0/1 while every other yes/no column uses
   "Yes"/"No". It is recoded for consistency.
3. No duplicate customer IDs and no other missing values exist.
"""

import numpy as np
import pandas as pd

from src.config import PROCESSED_DATA, RAW_DATA

ADDON_SERVICE_COLS = [
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
]

TENURE_BAND_EDGES = [0, 6, 12, 24, 48, 72]
TENURE_BAND_LABELS = ["0-6m", "7-12m", "13-24m", "25-48m", "49-72m"]

CHARGE_TIER_EDGES = [0, 35, 70, 90, np.inf]
CHARGE_TIER_LABELS = ["<$35", "$35-70", "$70-90", "$90+"]


def load_raw(path=RAW_DATA) -> pd.DataFrame:
    return pd.read_csv(path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Fix the data quality issues; returns a new frame."""
    df = df.copy()

    # TotalCharges: text -> numeric; blanks are new customers (tenure 0)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"].astype(str).str.strip(),
                                       errors="coerce")
    new_customer = df["TotalCharges"].isna() & (df["tenure"] == 0)
    df.loc[new_customer, "TotalCharges"] = 0.0
    if df["TotalCharges"].isna().any():
        raise ValueError("TotalCharges has missing values not explained by tenure==0")

    # SeniorCitizen 0/1 -> No/Yes to match every other yes/no column
    df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})

    # Churn label as 0/1 for arithmetic; keep the original text column too
    df["churn_flag"] = (df["Churn"] == "Yes").astype(int)

    if df["customerID"].duplicated().any():
        raise ValueError("Duplicate customer IDs found")

    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the segmentation features used across EDA, LTV and modeling."""
    df = df.copy()

    df["tenure_band"] = pd.cut(
        df["tenure"], bins=TENURE_BAND_EDGES, labels=TENURE_BAND_LABELS,
        include_lowest=True, right=True,
    )

    df["charge_tier"] = pd.cut(
        df["MonthlyCharges"], bins=CHARGE_TIER_EDGES, labels=CHARGE_TIER_LABELS,
        include_lowest=True, right=False,
    )

    # Number of add-on services the customer subscribes to (0-6). "No
    # internet service" counts as not having the add-on.
    df["n_addon_services"] = (df[ADDON_SERVICE_COLS] == "Yes").sum(axis=1)

    df["has_internet"] = (df["InternetService"] != "No").map({True: "Yes", False: "No"})

    # Coarse product-mix label used for "service bundle" cuts
    phone = df["PhoneService"] == "Yes"
    internet = df["InternetService"] != "No"
    df["service_bundle"] = np.select(
        [phone & internet, internet, phone],
        ["Phone + Internet", "Internet only", "Phone only"],
        default="None",
    )

    return df


def prepare(raw_path=RAW_DATA, save: bool = True) -> pd.DataFrame:
    """Full pipeline: load -> clean -> feature engineering (-> save)."""
    df = add_features(clean(load_raw(raw_path)))
    if save:
        PROCESSED_DATA.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(PROCESSED_DATA, index=False)
    return df
