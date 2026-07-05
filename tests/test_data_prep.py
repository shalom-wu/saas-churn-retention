"""Tests for the cleaning and feature-engineering pipeline."""

import numpy as np
import pandas as pd
import pytest

from src.data_prep import ADDON_SERVICE_COLS, add_features, clean


def make_raw(**overrides) -> pd.DataFrame:
    """A minimal raw-schema frame (2 rows) mirroring the Kaggle file."""
    base = {
        "customerID": ["0001-AAAAA", "0002-BBBBB"],
        "gender": ["Female", "Male"],
        "SeniorCitizen": [0, 1],
        "Partner": ["Yes", "No"],
        "Dependents": ["No", "No"],
        "tenure": [12, 0],
        "PhoneService": ["Yes", "No"],
        "MultipleLines": ["No", "No phone service"],
        "InternetService": ["Fiber optic", "DSL"],
        "OnlineSecurity": ["No", "Yes"],
        "OnlineBackup": ["Yes", "No"],
        "DeviceProtection": ["No", "No"],
        "TechSupport": ["No", "Yes"],
        "StreamingTV": ["Yes", "No"],
        "StreamingMovies": ["Yes", "No"],
        "Contract": ["Month-to-month", "One year"],
        "PaperlessBilling": ["Yes", "No"],
        "PaymentMethod": ["Electronic check", "Mailed check"],
        "MonthlyCharges": [89.5, 29.85],
        "TotalCharges": ["1074.0", " "],  # second row: unbilled new customer
        "Churn": ["Yes", "No"],
    }
    base.update(overrides)
    return pd.DataFrame(base)


class TestClean:
    def test_blank_total_charges_becomes_zero_for_new_customers(self):
        out = clean(make_raw())
        assert out.loc[1, "TotalCharges"] == 0.0
        assert out["TotalCharges"].dtype == np.float64

    def test_blank_total_charges_with_nonzero_tenure_raises(self):
        raw = make_raw(tenure=[12, 5])  # blank charge but 5 months tenure
        with pytest.raises(ValueError, match="TotalCharges"):
            clean(raw)

    def test_senior_citizen_recoded_to_yes_no(self):
        out = clean(make_raw())
        assert set(out["SeniorCitizen"]) == {"No", "Yes"}

    def test_churn_flag_is_binary_and_matches_label(self):
        out = clean(make_raw())
        assert out["churn_flag"].tolist() == [1, 0]

    def test_duplicate_customer_ids_raise(self):
        raw = make_raw(customerID=["0001-AAAAA", "0001-AAAAA"])
        with pytest.raises(ValueError, match="Duplicate"):
            clean(raw)

    def test_original_frame_not_mutated(self):
        raw = make_raw()
        original_total = raw["TotalCharges"].copy()
        clean(raw)
        pd.testing.assert_series_equal(raw["TotalCharges"], original_total)


class TestAddFeatures:
    def test_tenure_bands(self):
        out = add_features(clean(make_raw(tenure=[6, 0])))
        assert out["tenure_band"].astype(str).tolist() == ["0-6m", "0-6m"]
        out = add_features(clean(make_raw(tenure=[7, 72],
                                          TotalCharges=["100", "200"])))
        assert out["tenure_band"].astype(str).tolist() == ["7-12m", "49-72m"]

    def test_charge_tiers_are_left_inclusive(self):
        out = add_features(clean(make_raw(MonthlyCharges=[70.0, 34.99])))
        assert out["charge_tier"].astype(str).tolist() == ["$70-90", "<$35"]

    def test_addon_service_count(self):
        out = add_features(clean(make_raw()))
        # row 0: OnlineBackup, StreamingTV, StreamingMovies = 3
        assert out.loc[0, "n_addon_services"] == 3
        assert out.loc[1, "n_addon_services"] == 2
        assert out["n_addon_services"].between(0, len(ADDON_SERVICE_COLS)).all()

    def test_service_bundle_labels(self):
        out = add_features(clean(make_raw()))
        assert out["service_bundle"].tolist() == ["Phone + Internet", "Internet only"]
