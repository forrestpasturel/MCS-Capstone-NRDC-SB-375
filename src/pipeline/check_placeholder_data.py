from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.pipeline.utils import abs_path, load_config


def is_probably_synthetic(df: pd.DataFrame, min_rows: int = 25) -> bool:
    return len(df) < min_rows


def main() -> None:
    cfg = load_config()
    warnings = []

    for key, rel in cfg["paths"].items():
        path = abs_path(rel)
        if not path.exists():
            warnings.append(f"Missing: {path}")
            continue

        df = pd.read_csv(path)
        if is_probably_synthetic(df):
            warnings.append(f"Likely placeholder/synthetic (too few rows): {path} ({len(df)} rows)")

    notice = abs_path("data/raw/PLACEHOLDER_NOTICE.md")
    if notice.exists():
        warnings.append("Placeholder notice file exists: data/raw/PLACEHOLDER_NOTICE.md")

    if warnings:
        print("Data quality warnings:")
        for w in warnings:
            print(f"- {w}")
    else:
        print("Raw files look production-ready (basic checks passed).")


if __name__ == "__main__":
    main()
