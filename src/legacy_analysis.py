from __future__ import annotations

import pandas as pd


FRAMEWORK_DIMENSIONS = [
    "planning_mandate_strength",
    "funding_accountability",
    "induced_demand_controls",
    "equity_targeting",
    "monitoring_enforcement",
    "multimodal_investment",
]


def calculate_implementation_gap(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["gap_index_points"] = out["actual_vmt_index"] - out["target_vmt_index"]
    out["target_met"] = out["gap_index_points"] <= 0
    return out


def calculate_percent_change_from_baseline(df: pd.DataFrame, value_col: str, baseline_year: int) -> pd.DataFrame:
    out = df.copy()
    baseline = out.loc[out["year"] == baseline_year, value_col].mean()
    if baseline == 0:
        raise ValueError("Baseline cannot be zero.")
    out["pct_change_from_baseline"] = ((out[value_col] - baseline) / baseline) * 100
    return out


def model_emfac_ghg_reduction(base_ghg_mmt: float, vmt_reduction_pct: float, elasticity: float = 0.8) -> float:
    reduction_fraction = (vmt_reduction_pct / 100.0) * elasticity
    return max(base_ghg_mmt * (1 - reduction_fraction), 0.0)


def compute_framework_composite(df: pd.DataFrame, weights: dict[str, float] | None = None) -> pd.DataFrame:
    out = df.copy()
    if weights is None:
        weights = {d: 1 / len(FRAMEWORK_DIMENSIONS) for d in FRAMEWORK_DIMENSIONS}
    missing = [d for d in FRAMEWORK_DIMENSIONS if d not in out.columns]
    if missing:
        raise ValueError(f"Missing dimensions: {missing}")

    total_weight = sum(weights.values())
    if total_weight <= 0:
        raise ValueError("Weights must sum to a positive value.")

    normalized = {k: v / total_weight for k, v in weights.items()}
    out["composite_score"] = sum(out[col] * normalized[col] for col in FRAMEWORK_DIMENSIONS)
    return out.sort_values("composite_score", ascending=False)


def calculate_multistate_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> float:
    return float(df[x_col].corr(df[y_col]))


def build_vmt_savings_waterfall(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy().sort_values(["start_year", "annual_vmt_savings_million"], ascending=[True, False])
    out["cumulative_vmt_savings_million"] = out["annual_vmt_savings_million"].cumsum()
    return out
