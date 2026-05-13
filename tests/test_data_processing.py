"""
tests/test_data_processing.py
------------------------------
Tests for src/data_processing.py – verifies that all CSV datasets load
correctly and return DataFrames with the expected shape and columns.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from src.data_processing import (
    load_ca_vmt,
    load_ca_vmt_per_capita,
    load_ca_ghg,
    load_multistate_vmt,
    load_multistate_ghg,
    load_calenviroscreen,
    load_framework_scores,
    load_framework_details,
    linear_trend,
)


class TestLoadCaVmt:
    def test_returns_dataframe(self):
        df = load_ca_vmt()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = load_ca_vmt()
        assert "year" in df.columns
        assert "total_vmt_billion" in df.columns

    def test_year_is_integer(self):
        df = load_ca_vmt()
        assert df["year"].dtype in (int, "int64", "int32")

    def test_no_null_total_vmt(self):
        df = load_ca_vmt()
        assert df["total_vmt_billion"].notna().all()

    def test_covers_2008(self):
        df = load_ca_vmt()
        assert 2008 in df["year"].values


class TestLoadCaVmtPerCapita:
    def test_returns_dataframe(self):
        df = load_ca_vmt_per_capita()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = load_ca_vmt_per_capita()
        for col in ("year", "actual_vmt_per_capita", "target_vmt_per_capita"):
            assert col in df.columns

    def test_actual_vmt_positive(self):
        df = load_ca_vmt_per_capita()
        # filter to non-projected rows where actual is provided
        obs = df[df["actual_vmt_per_capita"].notna()]
        assert (obs["actual_vmt_per_capita"] > 0).all()


class TestLoadCaGhg:
    def test_returns_dataframe(self):
        df = load_ca_ghg()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = load_ca_ghg()
        assert "transport_ghg_mmt" in df.columns
        assert "year" in df.columns

    def test_ghg_positive(self):
        df = load_ca_ghg()
        assert (df["transport_ghg_mmt"] > 0).all()

    def test_subsector_sum_approx_total(self):
        df = load_ca_ghg()
        sub_sum = (
            df["passenger_vehicles_mmt"]
            + df["heavy_duty_mmt"]
            + df["other_transport_mmt"]
        )
        # Allow ±1% rounding tolerance
        assert (abs(sub_sum - df["transport_ghg_mmt"]) / df["transport_ghg_mmt"] < 0.01).all()


class TestLoadMultistateVmt:
    EXPECTED_STATES = {"California", "Colorado", "Massachusetts", "Minnesota", "Virginia"}

    def test_returns_dataframe(self):
        df = load_multistate_vmt()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = load_multistate_vmt()
        for col in ("year", "state", "vmt_per_capita"):
            assert col in df.columns

    def test_all_states_present(self):
        df = load_multistate_vmt()
        assert self.EXPECTED_STATES == set(df["state"].unique())

    def test_vmt_per_capita_positive(self):
        df = load_multistate_vmt()
        assert (df["vmt_per_capita"] > 0).all()


class TestLoadMultistateGhg:
    EXPECTED_STATES = {"California", "Colorado", "Massachusetts", "Minnesota", "Virginia"}

    def test_returns_dataframe(self):
        df = load_multistate_ghg()
        assert isinstance(df, pd.DataFrame)

    def test_all_states_present(self):
        df = load_multistate_ghg()
        assert self.EXPECTED_STATES == set(df["state"].unique())

    def test_ghg_per_capita_positive(self):
        df = load_multistate_ghg()
        assert (df["ghg_per_capita_tonnes"] > 0).all()


class TestLoadCalenviroscreen:
    def test_returns_dataframe(self):
        df = load_calenviroscreen()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = load_calenviroscreen()
        for col in (
            "county",
            "pollution_burden_score",
            "traffic_density_percentile",
            "disadvantaged_community",
        ):
            assert col in df.columns

    def test_pollution_burden_in_range(self):
        df = load_calenviroscreen()
        assert (df["pollution_burden_score"] >= 0).all()
        assert (df["pollution_burden_score"] <= 10).all()

    def test_percentiles_in_range(self):
        df = load_calenviroscreen()
        for col in ("traffic_density_percentile", "pm25_percentile", "diesel_pm_percentile"):
            assert (df[col] >= 0).all()
            assert (df[col] <= 100).all()


class TestLoadFrameworkScores:
    EXPECTED_STATES = {
        "California (SB 375)",
        "Colorado",
        "Massachusetts",
        "Minnesota",
        "Virginia",
    }
    EXPECTED_DIMS = [
        "binding_targets",
        "enforcement_accountability",
        "equity_provisions",
        "data_monitoring",
        "land_use_integration",
        "funding_mechanisms",
    ]

    def test_returns_dataframe(self):
        df = load_framework_scores()
        assert isinstance(df, pd.DataFrame)

    def test_all_states_present(self):
        df = load_framework_scores()
        assert self.EXPECTED_STATES == set(df["state"].unique())

    def test_scores_in_range(self):
        df = load_framework_scores()
        for dim in self.EXPECTED_DIMS:
            assert (df[dim] >= 0).all()
            assert (df[dim] <= 10).all()


class TestLoadFrameworkDetails:
    def test_returns_dataframe(self):
        df = load_framework_details()
        assert isinstance(df, pd.DataFrame)

    def test_has_required_columns(self):
        df = load_framework_details()
        for col in ("state", "category", "provision", "california_gap", "recommended_language"):
            assert col in df.columns

    def test_no_empty_recommendations(self):
        df = load_framework_details()
        assert (df["recommended_language"].str.strip() != "").all()


class TestLinearTrend:
    def test_returns_series_same_length(self):
        import pandas as pd
        years = pd.Series([2008, 2009, 2010, 2011, 2012])
        values = pd.Series([100.0, 102.0, 104.0, 106.0, 108.0])
        result = linear_trend(values, years)
        assert len(result) == len(values)

    def test_perfect_linear_data(self):
        import pandas as pd
        import numpy as np
        years = pd.Series([2008, 2009, 2010, 2011, 2012])
        values = pd.Series([100.0, 102.0, 104.0, 106.0, 108.0])
        result = linear_trend(values, years)
        assert np.allclose(result, values, atol=0.01)
