from __future__ import annotations

import pandas as pd

from src.pipeline.utils import (
    abs_path,
    ensure_columns,
    load_config,
    safe_read_csv,
    write_csv,
)


def main() -> None:
    cfg = load_config()

    pems = safe_read_csv(abs_path(cfg["paths"]["pems_timeseries"]))
    induced = safe_read_csv(abs_path(cfg["paths"]["induced_travel_inputs"]))

    ensure_columns(
        pems,
        ["segment_id", "date", "period", "avg_speed_mph", "capacity_added", "phase"],
        "PeMS",
    )
    ensure_columns(
        induced,
        ["segment_id", "annual_induced_vmt", "co2_kg_per_vmt"],
        "NCST inputs",
    )

    pems["date"] = pd.to_datetime(pems["date"])

    summary = (
        pems.groupby(["segment_id", "phase"], as_index=False)
        .agg(avg_speed_mph=("avg_speed_mph", "mean"), capacity_added=("capacity_added", "max"))
    )

    pivot = summary.pivot(index="segment_id", columns="phase", values="avg_speed_mph").reset_index()
    pivot.columns.name = None

    for col in ["pre", "post", "year_3"]:
        if col not in pivot.columns:
            pivot[col] = pd.NA

    pivot["speed_gain_post"] = pivot["post"] - pivot["pre"]
    pivot["speed_rebound_year3"] = pivot["year_3"] - pivot["post"]
    pivot["rebounded_to_pre_or_worse"] = pivot["year_3"] <= pivot["pre"]

    results = pivot.merge(induced, on="segment_id", how="left")
    results["annual_co2_penalty_kg"] = results["annual_induced_vmt"] * results["co2_kg_per_vmt"]

    output_path = abs_path(cfg["output"]["congestion_results"])
    write_csv(results, output_path)

    print(f"Wrote congestion rebound results: {output_path}")


if __name__ == "__main__":
    main()
