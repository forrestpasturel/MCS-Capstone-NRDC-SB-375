"""
tests/test_analysis.py
-----------------------
Tests for src/analysis.py – verifies correctness of analytical routines.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import numpy as np
import pytest
from src.analysis import (
    compute_implementation_gap,
    pct_change_from_baseline,
    rank_frameworks,
    vmt_ghg_correlation,
    ghg_reduction_from_vmt,
    weighted_policy_score,
    EMFAC_EMISSION_FACTOR_KG_PER_VMT,
    DIMENSION_WEIGHTS,
)


class TestComputeImplementationGap:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame(
            {
                "year": [2008, 2010, 2015, 2020],
                "actual_vmt_per_capita": [9060, 8760, 8890, 7780],
                "target_vmt_per_capita": [9060, 8960, 8710, 8420],
            }
        )

    def test_returns_dataframe(self, sample_df):
        result = compute_implementation_gap(sample_df)
        assert isinstance(result, pd.DataFrame)

    def test_gap_column_correct(self, sample_df):
        result = compute_implementation_gap(sample_df)
        expected_gap = (
            sample_df["actual_vmt_per_capita"] - sample_df["target_vmt_per_capita"]
        )
        pd.testing.assert_series_equal(result["gap"], expected_gap, check_names=False)

    def test_gap_pct_column_correct(self, sample_df):
        result = compute_implementation_gap(sample_df)
        expected_pct = (
            (sample_df["actual_vmt_per_capita"] - sample_df["target_vmt_per_capita"])
            / sample_df["target_vmt_per_capita"]
            * 100
        )
        pd.testing.assert_series_equal(
            result["gap_pct"], expected_pct, check_names=False
        )

    def test_baseline_year_gap_is_zero(self, sample_df):
        result = compute_implementation_gap(sample_df)
        baseline = result[result["year"] == 2008].iloc[0]
        assert baseline["gap"] == 0
        assert baseline["gap_pct"] == 0.0


class TestPctChangeFromBaseline:
    def test_returns_series(self):
        s = pd.Series([100.0, 110.0, 120.0])
        y = pd.Series([2008, 2009, 2010])
        result = pct_change_from_baseline(s, y, 2008)
        assert isinstance(result, pd.Series)

    def test_baseline_year_is_zero(self):
        s = pd.Series([100.0, 110.0, 120.0])
        y = pd.Series([2008, 2009, 2010])
        result = pct_change_from_baseline(s, y, 2008)
        assert result.iloc[0] == 0.0

    def test_correct_pct_values(self):
        s = pd.Series([100.0, 110.0, 90.0])
        y = pd.Series([2008, 2009, 2010])
        result = pct_change_from_baseline(s, y, 2008)
        assert abs(result.iloc[1] - 10.0) < 1e-6
        assert abs(result.iloc[2] - (-10.0)) < 1e-6

    def test_missing_baseline_year_returns_copy(self):
        s = pd.Series([100.0, 110.0])
        y = pd.Series([2010, 2011])
        result = pct_change_from_baseline(s, y, 2008)
        pd.testing.assert_series_equal(result, s)


class TestRankFrameworks:
    @pytest.fixture
    def sample_scores(self):
        return pd.DataFrame(
            {
                "state": ["StateA", "StateB", "StateC"],
                "binding_targets": [8, 5, 6],
                "enforcement_accountability": [7, 4, 6],
            }
        )

    def test_returns_dataframe(self, sample_scores):
        result = rank_frameworks(sample_scores)
        assert isinstance(result, pd.DataFrame)

    def test_composite_score_column_exists(self, sample_scores):
        result = rank_frameworks(sample_scores)
        assert "composite_score" in result.columns

    def test_sorted_descending(self, sample_scores):
        result = rank_frameworks(sample_scores)
        scores = result["composite_score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_top_state_is_highest(self, sample_scores):
        result = rank_frameworks(sample_scores)
        assert result.iloc[0]["state"] == "StateA"


class TestVmtGhgCorrelation:
    @pytest.fixture
    def sample_vmt(self):
        return pd.DataFrame(
            {
                "year": [2020, 2020, 2020],
                "state": ["StateA", "StateB", "StateC"],
                "vmt_per_capita": [9000, 6000, 8000],
            }
        )

    @pytest.fixture
    def sample_ghg(self):
        return pd.DataFrame(
            {
                "year": [2020, 2020, 2020],
                "state": ["StateA", "StateB", "StateC"],
                "ghg_per_capita_tonnes": [4.5, 2.8, 4.0],
            }
        )

    def test_returns_dataframe(self, sample_vmt, sample_ghg):
        result = vmt_ghg_correlation(sample_vmt, sample_ghg, 2020)
        assert isinstance(result, pd.DataFrame)

    def test_correct_columns(self, sample_vmt, sample_ghg):
        result = vmt_ghg_correlation(sample_vmt, sample_ghg, 2020)
        assert "vmt_per_capita" in result.columns
        assert "ghg_per_capita_tonnes" in result.columns

    def test_correct_row_count(self, sample_vmt, sample_ghg):
        result = vmt_ghg_correlation(sample_vmt, sample_ghg, 2020)
        assert len(result) == 3

    def test_filters_by_year(self, sample_vmt, sample_ghg):
        result = vmt_ghg_correlation(sample_vmt, sample_ghg, 2019)
        assert len(result) == 0


class TestGhgReductionFromVmt:
    def test_returns_dict(self):
        result = ghg_reduction_from_vmt(8, 362.4)
        assert isinstance(result, dict)

    def test_required_keys(self):
        result = ghg_reduction_from_vmt(8, 362.4)
        assert "vmt_reduced_billion" in result
        assert "ghg_reduced_mmt" in result

    def test_zero_reduction(self):
        result = ghg_reduction_from_vmt(0, 362.4)
        assert result["vmt_reduced_billion"] == 0.0
        assert result["ghg_reduced_mmt"] == 0.0

    def test_full_reduction(self):
        result = ghg_reduction_from_vmt(100, 362.4)
        assert abs(result["vmt_reduced_billion"] - 362.4) < 0.01

    def test_ghg_calculation(self):
        # 10% of 100 billion VMT * 0.338 kg/VMT = 3.38 billion kg = 3.38 MMT
        result = ghg_reduction_from_vmt(10, 100.0)
        expected_ghg = (100.0 * 0.10 * 1e9 * EMFAC_EMISSION_FACTOR_KG_PER_VMT) / 1e9
        assert abs(result["ghg_reduced_mmt"] - round(expected_ghg, 2)) < 0.01

    def test_custom_emission_factor(self):
        result = ghg_reduction_from_vmt(10, 100.0, emission_factor=0.4)
        expected_ghg = (100.0 * 0.10 * 1e9 * 0.4) / 1e9
        assert abs(result["ghg_reduced_mmt"] - round(expected_ghg, 2)) < 0.01


class TestWeightedPolicyScore:
    def test_returns_float(self):
        scores = {dim: 5.0 for dim in DIMENSION_WEIGHTS}
        result = weighted_policy_score(scores)
        assert isinstance(result, float)

    def test_all_zero_scores_gives_zero(self):
        scores = {dim: 0 for dim in DIMENSION_WEIGHTS}
        assert weighted_policy_score(scores) == 0.0

    def test_all_ten_scores_gives_ten(self):
        scores = {dim: 10 for dim in DIMENSION_WEIGHTS}
        result = weighted_policy_score(scores)
        # weights sum to 1.0 × 10 = 10.0
        assert abs(result - 10.0) < 0.01

    def test_weights_sum_to_one(self):
        assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 1e-9

    def test_missing_dimension_defaults_to_zero(self):
        # Only provide two dimensions; missing ones should default to 0
        partial = {"binding_targets": 10, "enforcement_accountability": 10}
        result = weighted_policy_score(partial)
        expected = 10 * DIMENSION_WEIGHTS["binding_targets"] + 10 * DIMENSION_WEIGHTS["enforcement_accountability"]
        assert abs(result - round(expected, 2)) < 0.01
