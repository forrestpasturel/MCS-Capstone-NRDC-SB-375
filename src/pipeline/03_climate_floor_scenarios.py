from __future__ import annotations

import pandas as pd

from src.pipeline.utils import (
    abs_path,
    ensure_columns,
    load_config,
    safe_read_csv,
    write_csv,
)


def climate_floor_score(delta_vmt: float, delta_ghg_tons: float, delta_access: float, delta_equity: float) -> float:
    # Weights can be revised in policy calibration.
    w1, w2, w3, w4 = 0.35, 0.35, 0.2, 0.1
    return (w1 * delta_vmt) + (w2 * delta_ghg_tons) + (w3 * delta_access) + (w4 * delta_equity)


def main() -> None:
    cfg = load_config()

    a = safe_read_csv(abs_path(cfg["paths"]["emfac_scenario_a"]))
    b = safe_read_csv(abs_path(cfg["paths"]["emfac_scenario_b"]))

    required = ["year", "ghg_tons", "vmt_index", "accessibility_index", "equity_index"]
    ensure_columns(a, required, "EMFAC Scenario A")
    ensure_columns(b, required, "EMFAC Scenario B")

    merged = a.merge(b, on="year", suffixes=("_a", "_b"))

    merged["delta_ghg_tons"] = merged["ghg_tons_b"] - merged["ghg_tons_a"]
    merged["delta_vmt"] = merged["vmt_index_b"] - merged["vmt_index_a"]
    merged["delta_access"] = merged["accessibility_index_b"] - merged["accessibility_index_a"]
    merged["delta_equity"] = merged["equity_index_b"] - merged["equity_index_a"]

    score = climate_floor_score(
        delta_vmt=merged["delta_vmt"].sum(),
        delta_ghg_tons=merged["delta_ghg_tons"].sum(),
        delta_access=merged["delta_access"].mean(),
        delta_equity=merged["delta_equity"].mean(),
    )

    summary = pd.DataFrame(
        {
            "scenario_a_20y_ghg_tons": [merged["ghg_tons_a"].sum()],
            "scenario_b_20y_ghg_tons": [merged["ghg_tons_b"].sum()],
            "delta_20y_ghg_tons_b_minus_a": [merged["delta_ghg_tons"].sum()],
            "climate_floor_score": [score],
            "state_funding_eligibility": ["eligible" if score >= 0 else "ineligible"],
        }
    )

    output_path = abs_path(cfg["output"]["climate_floor_results"])
    write_csv(summary, output_path)

    print(f"Wrote climate floor results: {output_path}")


if __name__ == "__main__":
    main()
