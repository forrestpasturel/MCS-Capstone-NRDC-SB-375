from __future__ import annotations

import pytest

from src.analysis import (
    FRAMEWORK_DIMENSIONS,
    build_vmt_savings_waterfall,
    calculate_implementation_gap,
    calculate_multistate_correlation,
    calculate_percent_change_from_baseline,
    compute_framework_composite,
    model_emfac_ghg_reduction,
)
from src.data_processing import (
    load_ca_vmt_targets_actual,
    load_policy_reform_actions,
    load_state_framework_dimensions,
    load_state_ghg_per_capita,
    load_state_vmt_per_capita,
)


def test_implementation_gap_columns():
    df = calculate_implementation_gap(load_ca_vmt_targets_actual())
    assert {"gap_index_points", "target_met"}.issubset(df.columns)


@pytest.mark.parametrize("vmt_reduction", [0, 2, 5, 7, 10, 15, 20, 30])
def test_emfac_model_non_negative(vmt_reduction):
    projected = model_emfac_ghg_reduction(base_ghg_mmt=200.0, vmt_reduction_pct=vmt_reduction)
    assert projected >= 0


@pytest.mark.parametrize("pair", [(0, 5), (2, 8), (5, 10), (8, 15), (10, 20), (12, 25), (15, 30), (20, 35)])
def test_emfac_model_monotonic(pair):
    a, b = pair
    ga = model_emfac_ghg_reduction(base_ghg_mmt=200.0, vmt_reduction_pct=a)
    gb = model_emfac_ghg_reduction(base_ghg_mmt=200.0, vmt_reduction_pct=b)
    assert gb <= ga


@pytest.mark.parametrize("state", ["CA", "CO", "MA", "MN", "VA"])
def test_percent_change_from_baseline_has_zero_at_baseline(state):
    df = load_state_vmt_per_capita()
    s = df[df["state"] == state]
    out = calculate_percent_change_from_baseline(s, "vmt_per_capita", 2008)
    baseline_row = out[out["year"] == 2008].iloc[0]
    assert baseline_row["pct_change_from_baseline"] == pytest.approx(0.0)


@pytest.mark.parametrize("weight_shift", [0.0, 0.1, 0.2])
def test_framework_composite_valid(weight_shift):
    df = load_state_framework_dimensions()
    weights = {d: 1 / len(FRAMEWORK_DIMENSIONS) for d in FRAMEWORK_DIMENSIONS}
    weights["funding_accountability"] += weight_shift
    out = compute_framework_composite(df, weights)
    assert "composite_score" in out.columns


@pytest.mark.parametrize("pair", [("CA", "MA"), ("CA", "VA"), ("MA", "VA")])
def test_framework_composite_ranking_pair(pair):
    df = load_state_framework_dimensions()
    out = compute_framework_composite(df)
    score = dict(zip(out["state"], out["composite_score"]))
    a, b = pair
    assert score[a] != score[b]


@pytest.mark.parametrize("year", [2008, 2012, 2016])
def test_multistate_correlation_bounds(year):
    vmt = load_state_vmt_per_capita()
    ghg = load_state_ghg_per_capita()
    merged = vmt.merge(ghg, on=["year", "state"], how="inner")
    subset = merged[merged["year"] >= year]
    corr = calculate_multistate_correlation(subset, "vmt_per_capita", "ghg_per_capita_transport")
    assert -1 <= corr <= 1


@pytest.mark.parametrize("cutoff", [2026, 2028, 2030])
def test_waterfall_cumulative_increasing(cutoff):
    actions = load_policy_reform_actions()
    wf = build_vmt_savings_waterfall(actions[actions["end_year"] >= cutoff])
    diffs = wf["cumulative_vmt_savings_million"].diff().fillna(wf["cumulative_vmt_savings_million"])
    assert (diffs >= 0).all()
