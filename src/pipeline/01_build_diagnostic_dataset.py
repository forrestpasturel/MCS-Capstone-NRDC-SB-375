from __future__ import annotations

import pandas as pd

from src.pipeline.utils import (
    abs_path,
    ensure_columns,
    load_config,
    safe_read_csv,
    write_parquet,
)


def main() -> None:
    cfg = load_config()

    vmt = safe_read_csv(abs_path(cfg["paths"]["vmt_index_cbg"]))
    ces = safe_read_csv(abs_path(cfg["paths"]["calenviroscreen"]))

    ensure_columns(vmt, ["cbg_id", "year", "vmt_per_capita"], "VMTIndex")
    ensure_columns(ces, ["cbg_id", "traffic_density", "pollution_burden_pctile"], "CalEnviroScreen")

    merged = vmt.merge(ces, on="cbg_id", how="left")

    start_year = cfg["project"]["analysis_year_start"]
    end_year = cfg["project"]["analysis_year_end"]

    window = merged[merged["year"].between(start_year, end_year)].copy()

    trend = (
        window.sort_values(["cbg_id", "year"])
        .groupby("cbg_id")
        .agg(
            vmt_first=("vmt_per_capita", "first"),
            vmt_last=("vmt_per_capita", "last"),
            traffic_density=("traffic_density", "max"),
            pollution_burden_pctile=("pollution_burden_pctile", "max"),
        )
        .reset_index()
    )

    trend["vmt_change_pct"] = ((trend["vmt_last"] - trend["vmt_first"]) / trend["vmt_first"]) * 100
    trend["implementation_gap_flag"] = (trend["vmt_change_pct"] > 0) & (trend["pollution_burden_pctile"] >= 75)

    output_path = abs_path(cfg["output"]["diagnostic_dataset"])
    write_parquet(trend, output_path)

    print(f"Wrote diagnostic dataset: {output_path}")
    print(f"Flagged CBGs: {int(trend['implementation_gap_flag'].sum())} / {len(trend)}")


if __name__ == "__main__":
    main()
