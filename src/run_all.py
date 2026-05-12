from __future__ import annotations

import runpy


SCRIPTS = [
    "src/pipeline/01_build_diagnostic_dataset.py",
    "src/pipeline/02_congestion_rebound_analysis.py",
    "src/pipeline/03_climate_floor_scenarios.py",
    "src/viz/build_figures.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"Running {script}...")
        runpy.run_path(script, run_name="__main__")

    print("Pipeline complete.")


if __name__ == "__main__":
    main()
