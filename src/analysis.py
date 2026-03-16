"""
analysis.py
-----------
Core analytical routines for the SB 375 Capstone dashboard.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Implementation gap calculation
# ---------------------------------------------------------------------------
def compute_implementation_gap(vmt_per_capita: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame with columns [year, actual, target, gap, gap_pct].
    *vmt_per_capita* must contain columns: year, actual_vmt_per_capita,
    target_vmt_per_capita.
    """
    df = vmt_per_capita.copy()
    df["gap"] = df["actual_vmt_per_capita"] - df["target_vmt_per_capita"]
    df["gap_pct"] = (df["gap"] / df["target_vmt_per_capita"]) * 100
    return df


# ---------------------------------------------------------------------------
# 2. Percent change relative to a baseline year
# ---------------------------------------------------------------------------
def pct_change_from_baseline(
    series: pd.Series, years: pd.Series, baseline_year: int = 2008
) -> pd.Series:
    """
    Return percentage change of *series* relative to its value in *baseline_year*.
    """
    idx = years[years == baseline_year].index
    if len(idx) == 0:
        return series.copy()
    baseline_val = series.loc[idx[0]]
    if baseline_val == 0:
        return series.copy()
    return ((series - baseline_val) / baseline_val) * 100


# ---------------------------------------------------------------------------
# 3. Rank states by policy effectiveness score
# ---------------------------------------------------------------------------
def rank_frameworks(scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Given a scores DataFrame with columns [state, dim1, dim2, …],
    compute a composite score (mean of all numeric columns) and return
    the DataFrame sorted by composite score descending.
    """
    df = scores_df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df["composite_score"] = df[numeric_cols].mean(axis=1)
    return df.sort_values("composite_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 4. Correlation: VMT per capita vs. GHG per capita across states
# ---------------------------------------------------------------------------
def vmt_ghg_correlation(
    vmt_df: pd.DataFrame, ghg_df: pd.DataFrame, year: int
) -> pd.DataFrame:
    """
    For a given *year*, merge the multi-state VMT and GHG per-capita DataFrames
    and return a merged table suitable for scatter plotting.
    *vmt_df* columns: year, state, vmt_per_capita
    *ghg_df* columns: year, state, ghg_per_capita_tonnes
    """
    v = vmt_df[vmt_df["year"] == year][["state", "vmt_per_capita"]]
    g = ghg_df[ghg_df["year"] == year][["state", "ghg_per_capita_tonnes"]]
    return v.merge(g, on="state")


# ---------------------------------------------------------------------------
# 5. Estimate GHG reduction potential from VMT reduction
#    Using simplified CARB EMFAC emission factor (kg CO2e / VMT)
# ---------------------------------------------------------------------------
EMFAC_EMISSION_FACTOR_KG_PER_VMT = 0.338  # EMFAC2021 statewide average, 2020


def ghg_reduction_from_vmt(
    vmt_reduction_pct: float,
    base_vmt_billion: float,
    emission_factor: float = EMFAC_EMISSION_FACTOR_KG_PER_VMT,
) -> dict:
    """
    Given a *vmt_reduction_pct* (0–100) applied to *base_vmt_billion* (billion VMT),
    estimate annual GHG reduction in million metric tons CO2e.
    Returns a dict with 'vmt_reduced_billion' and 'ghg_reduced_mmt'.
    """
    vmt_reduced = base_vmt_billion * (vmt_reduction_pct / 100.0)
    ghg_reduced_mmt = (vmt_reduced * 1e9 * emission_factor) / 1e9  # kg → million MT
    return {
        "vmt_reduced_billion": round(vmt_reduced, 2),
        "ghg_reduced_mmt": round(ghg_reduced_mmt, 2),
    }


# ---------------------------------------------------------------------------
# 6. Weighted policy adoption score
#    Weights reflect relative importance of each dimension for SB 375 reform
# ---------------------------------------------------------------------------
DIMENSION_WEIGHTS = {
    "binding_targets": 0.25,
    "enforcement_accountability": 0.20,
    "equity_provisions": 0.15,
    "data_monitoring": 0.15,
    "land_use_integration": 0.15,
    "funding_mechanisms": 0.10,
}


def weighted_policy_score(scores_row: dict) -> float:
    """
    Compute a weighted composite score from a dict of dimension scores (0-10).
    """
    total = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        total += scores_row.get(dim, 0) * weight
    return round(total, 2)
