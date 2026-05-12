"""
build_vmt_scenarios.py
======================
Computes conceptual per-capita VMT scenarios for the SB 375 / SB 1087 website.

Data basis:
  - California per-capita VMT reference baseline: ~10,000 mi/person/yr (Caltrans, c. 2001 peak)
  - Statewide 29 % reduction target by 2045 from 2001 levels (SB 375 / CARB guidance)
  - BAU trend: gentle continued growth at ~0.4% / yr (recent Caltrans MVMT pattern)
  - Reform scenarios: apply annual reduction multipliers reflecting strength of each policy tool
    (Colorado budget lock, Minnesota capacity trigger, Virginia scoring, Massachusetts caps)
  - Elasticity for induced-demand suppression: literature range 0.5–0.8; we use 0.65
    (source: Duranton & Turner 2011, replicated in NCST Induced Travel Calculator docs)

Outputs:
  - data/vmt_scenarios.csv   — tidy long-format
  - (merged into) data/chart_data.js

Replace the PARAM block below with real Caltrans MVMT CSV inputs when available.
Run:  python build_vmt_scenarios.py
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# PARAMETERS  (replace with real data when available)
# ──────────────────────────────────────────────────────────────────────────────
BASELINE_YEAR   = 2001          # index year (= 100)
START_YEAR      = 2025          # chart start
END_YEAR        = 2045          # chart end (matches CA climate targets)
YEARS           = list(range(START_YEAR, END_YEAR + 1, 5))  # 5-yr steps: 2025,2030…2045

# CA 29 % reduction target by 2045 from 2001 baseline
# 2001 reference index = 100; by 2045 must reach 71
TARGET_2045     = 71.0

# BAU: slight continued growth from 2025 level
# 2025 index ≈ 108 (rough Caltrans estimate post-COVID recovery)
BAU_2025        = 108.0
BAU_GROWTH_RATE = 0.004         # 0.4 % / yr

# Annual VMT reduction rates PER YEAR attributable to each guardrail
# (on top of BAU) — derived from induced-travel suppression literature
# and state program evaluations; treated as conservative lower bounds
GUARDRAIL_RATES = {
    "colorado_budget_lock"     : 0.008,   # 0.8 % / yr suppression vs BAU
    "minnesota_capacity_trigger": 0.006,   # 0.6 % / yr
    "virginia_scoring"         : 0.004,   # 0.4 % / yr
    "massachusetts_caps"       : 0.010,   # 1.0 % / yr (hardest constraint)
    "combined_approach"        : 0.018,   # compounding of all four tools
}

# ──────────────────────────────────────────────────────────────────────────────
# COMPUTE
# ──────────────────────────────────────────────────────────────────────────────

def vmt_index(start_val: float, annual_rate: float, n_years: int) -> float:
    """Compound a VMT index from start_val for n_years at annual_rate."""
    return round(start_val * ((1 + annual_rate) ** n_years), 1)


rows = []

for yr in YEARS:
    n = yr - START_YEAR  # years since 2025

    # BAU
    bau = vmt_index(BAU_2025, BAU_GROWTH_RATE, n)
    rows.append({"year": yr, "scenario": "california_today_bau", "vmt_index": bau})

    # Target path (linear interpolation from BAU_2025 down to TARGET_2045)
    target = round(BAU_2025 + (TARGET_2045 - BAU_2025) * (n / (END_YEAR - START_YEAR)), 1)
    rows.append({"year": yr, "scenario": "ca_29pct_target_path", "vmt_index": target})

    # Each guardrail scenario: suppress BAU growth each year
    for name, suppress_rate in GUARDRAIL_RATES.items():
        # Net rate = BAU growth minus policy suppression (can go negative = actual reduction)
        net_rate = BAU_GROWTH_RATE - suppress_rate
        val = vmt_index(BAU_2025, net_rate, n)
        rows.append({"year": yr, "scenario": name, "vmt_index": val})

df = pd.DataFrame(rows)

# Pivot for easier inspection
pivot = df.pivot(index="year", columns="scenario", values="vmt_index").reset_index()
print("=== VMT Scenarios (index, 2001 = 100) ===")
print(pivot.to_string(index=False))

# Save CSV
out_dir = Path(__file__).parent
df.to_csv(out_dir / "vmt_scenarios.csv", index=False)
print(f"\nSaved: {out_dir / 'vmt_scenarios.csv'}")

# ──────────────────────────────────────────────────────────────────────────────
# EXPORT as JS-friendly dict (consumed by build_chart_data.py)
# ──────────────────────────────────────────────────────────────────────────────
js_payload = {
    "years": YEARS,
    "scenarios": {},
    "metadata": {
        "index_basis": "2001 Caltrans per-capita VMT peak = 100",
        "start_year": START_YEAR,
        "bau_2025_index": BAU_2025,
        "target_2045_index": TARGET_2045,
        "note": "Conceptual / illustrative — replace with Caltrans MVMT CSV inputs",
    }
}

for name in ["california_today_bau", "ca_29pct_target_path"] + list(GUARDRAIL_RATES.keys()):
    subset = df[df["scenario"] == name].sort_values("year")
    js_payload["scenarios"][name] = subset["vmt_index"].tolist()

(out_dir / "vmt_scenarios_js.json").write_text(
    json.dumps(js_payload, indent=2), encoding="utf-8"
)
print(f"Saved: {out_dir / 'vmt_scenarios_js.json'}")
