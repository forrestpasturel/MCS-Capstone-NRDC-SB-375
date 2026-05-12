from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from src.pipeline.utils import abs_path, load_config


def fig_implementation_gap(cfg: dict) -> None:
    df = pd.read_parquet(abs_path(cfg["output"]["diagnostic_dataset"]))

    fig, ax = plt.subplots(figsize=(8, 5))
    sc = ax.scatter(
        df["traffic_density"],
        df["vmt_change_pct"],
        c=df["pollution_burden_pctile"],
        cmap="magma",
        alpha=0.7,
    )
    ax.axhline(0, linestyle="--", linewidth=1)
    ax.set_title("Implementation Gap: VMT Change vs Traffic Density")
    ax.set_xlabel("Traffic Density")
    ax.set_ylabel("VMT Change %")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Pollution Burden Percentile")

    out = abs_path(cfg["output"]["implementation_gap_figure"])
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=200)


def fig_congestion_rebound(cfg: dict) -> None:
    df = pd.read_csv(abs_path(cfg["output"]["congestion_results"]))

    metrics = [
        ("speed_gain_post", "Post Gain (mph)"),
        ("speed_rebound_year3", "Year-3 Rebound (mph)"),
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    for col, label in metrics:
        ax.hist(df[col].dropna(), bins=20, alpha=0.6, label=label)

    ax.set_title("Congestion Rebound Distribution")
    ax.set_xlabel("Speed Change")
    ax.set_ylabel("Count of Segments")
    ax.legend()

    out = abs_path(cfg["output"]["congestion_rebound_figure"])
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=200)


def fig_climate_floor(cfg: dict) -> None:
    df = pd.read_csv(abs_path(cfg["output"]["climate_floor_results"]))

    vals = [df.loc[0, "scenario_a_20y_ghg_tons"], df.loc[0, "scenario_b_20y_ghg_tons"]]
    labels = ["Scenario A: Widening", "Scenario B: BRT + Infill"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(labels, vals)
    ax.set_title("20-Year GHG Comparison")
    ax.set_ylabel("GHG Tons (20-year sum)")
    ax.tick_params(axis="x", rotation=10)

    out = abs_path(cfg["output"]["climate_floor_figure"])
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=200)


def main() -> None:
    cfg = load_config()

    fig_implementation_gap(cfg)
    fig_congestion_rebound(cfg)
    fig_climate_floor(cfg)

    print("Wrote all figure outputs.")


if __name__ == "__main__":
    main()
