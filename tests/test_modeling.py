"""Tests for feature construction and evaluation helpers (no model training,
so the suite stays fast)."""

import numpy as np
import pandas as pd

from src.data_prep import add_features, clean
from src.modeling import build_feature_frame, targeting_table
from tests.test_data_prep import make_raw


class TestFeatureFrame:
    def test_all_numeric_no_missing(self):
        df = add_features(clean(make_raw()))
        X, y = build_feature_frame(df)
        assert X.select_dtypes(exclude="number").empty
        assert not X.isna().any().any()
        assert set(y.unique()) <= {0, 1}

    def test_total_charges_excluded(self):
        df = add_features(clean(make_raw()))
        X, _ = build_feature_frame(df)
        assert not any("TotalCharges" in c for c in X.columns)

    def test_row_alignment(self):
        df = add_features(clean(make_raw()))
        X, y = build_feature_frame(df)
        assert len(X) == len(y) == len(df)


class TestTargetingTable:
    def test_perfect_ranking(self):
        # 10 customers, 3 churners, model ranks them perfectly
        y = pd.Series([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
        proba = np.linspace(1.0, 0.1, 10)
        t = targeting_table(proba, y, depths=(0.30,))
        row = t.iloc[0]
        assert row["customers_contacted"] == 3
        assert row["precision"] == 1.0
        assert row["recall"] == 1.0
        assert row["lift_vs_random"] == pytest_approx(1 / 0.3)

    def test_random_ranking_has_lift_one(self):
        rng = np.random.default_rng(0)
        y = pd.Series(rng.integers(0, 2, 2000))
        proba = rng.random(2000)
        t = targeting_table(proba, y, depths=(0.50,))
        assert abs(t.iloc[0]["lift_vs_random"] - 1.0) < 0.15


def pytest_approx(x, rel=1e-6):
    import pytest
    return pytest.approx(x, rel=rel)
