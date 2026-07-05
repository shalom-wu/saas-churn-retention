"""Tests for the LTV / cost-of-churn math."""

import numpy as np
import pandas as pd
import pytest

from src.config import LIFETIME_CAP_MONTHS, REPLACEMENT_CAC
from src.ltv import (
    annuity_factor,
    cost_of_churn_summary,
    discounted_ltv,
    expected_lifetime_months,
    ltv_by_segment,
    monthly_churn_hazard,
    one_way_sensitivity,
    sensitivity_table,
)


def make_book() -> pd.DataFrame:
    """Tiny synthetic customer book: 4 customers, 1 churned."""
    return pd.DataFrame({
        "Contract": ["Month-to-month", "Month-to-month", "Two year", "Two year"],
        "MonthlyCharges": [80.0, 60.0, 50.0, 40.0],
        "tenure": [10, 10, 40, 0],
        "churn_flag": [1, 0, 0, 0],
    })


class TestHazard:
    def test_overall_hazard_is_events_over_exposure(self):
        # 1 churn event / (10 + 10 + 40 + 1) customer-months; tenure 0
        # contributes 1 month of exposure
        assert monthly_churn_hazard(make_book()) == pytest.approx(1 / 61)

    def test_hazard_by_group(self):
        h = monthly_churn_hazard(make_book(), by="Contract")
        assert h["Month-to-month"] == pytest.approx(1 / 20)
        assert h["Two year"] == pytest.approx(0.0)


class TestLifetime:
    def test_inverse_hazard(self):
        assert expected_lifetime_months(0.05) == pytest.approx(20.0)

    def test_capped_at_observation_window(self):
        assert expected_lifetime_months(0.001) == LIFETIME_CAP_MONTHS
        assert expected_lifetime_months(0.0) == LIFETIME_CAP_MONTHS  # 1/0 -> inf -> cap


class TestDiscounting:
    def test_annuity_factor_zero_rate_is_n(self):
        assert annuity_factor(24, monthly_rate=0.0) == pytest.approx(24.0)

    def test_annuity_factor_one_month_closed_form(self):
        d = 0.01
        assert annuity_factor(1, monthly_rate=d) == pytest.approx(1 / (1 + d))

    def test_discounting_reduces_value(self):
        undiscounted = discounted_ltv(100.0, 24, gross_margin=1.0, monthly_rate=0.0)
        discounted = discounted_ltv(100.0, 24, gross_margin=1.0, monthly_rate=0.01)
        assert discounted < undiscounted

    def test_margin_scales_linearly(self):
        full = discounted_ltv(100.0, 24, gross_margin=1.0)
        seventy = discounted_ltv(100.0, 24, gross_margin=0.7)
        assert seventy == pytest.approx(0.7 * full)


class TestCostOfChurn:
    def test_components_add_up(self):
        s = cost_of_churn_summary(make_book())
        assert s["churned_customers"] == 1
        assert s["lost_mrr"] == pytest.approx(80.0)
        assert s["annualized_lost_revenue"] == pytest.approx(960.0)
        assert s["total_cost_of_churn"] == pytest.approx(
            s["foregone_ltv"] + s["replacement_cac_total"])
        assert s["replacement_cac_total"] == pytest.approx(REPLACEMENT_CAC)

    def test_higher_hazard_means_lower_foregone_ltv(self):
        base = cost_of_churn_summary(make_book())
        stressed = cost_of_churn_summary(make_book(), hazard_multiplier=1.2)
        assert stressed["foregone_ltv"] < base["foregone_ltv"]

    def test_ltv_by_segment_shape(self):
        t = ltv_by_segment(make_book(), by="Contract")
        assert set(t.index) == {"Month-to-month", "Two year"}
        assert (t["cost_per_churn"] > t["avg_ltv"]).all()


class TestSensitivity:
    def test_full_grid_size(self):
        assert len(sensitivity_table(make_book())) == 27  # 3 x 3 x 3

    def test_one_way_contains_base_between_low_and_high(self):
        t = one_way_sensitivity(make_book())
        for row in t.itertuples():
            lo, hi = sorted([row.low, row.high])
            assert lo <= row.base <= hi
