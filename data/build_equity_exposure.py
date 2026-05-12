"""
build_equity_exposure.py
========================
Computes a conceptual traffic-related pollution exposure index for disadvantaged
communities near major California highway corridors, before and after SB 1087-style
investment reform.

Methodology:
  - Start from a simplified CalEnviroScreen-style "traffic burden index" per corridor
    (pollution proximity score × VMT density, normalized to 100 at I-710 baseline)
  - Under each reform scenario, apply a VMT reduction that translates to a:
      • Proportional reduction in near-road PM2.5 exposure
        (linear dose-response proxy; literature: ~1% VMT → ~0.6% near-road PM2.5)
      • Additional benefit from investment shift to transit / active modes
        (reduced cold-start emissions, reduced idling near stops)
  - Output: corridor × scenario matrix of before/after exposure index values

Sources:
  - CalEnviroScreen 4.0: https://oehha.ca.gov/calenviroscreen/report/calenviroscreen-40
  - Near-road PM2.5 / VMT dose-response: Rowangould (2013) Transportation Research D
  - CARB Community Air Protection Program: prioritized communities near freight corridors

Replace PARAM block with CalEnviroScreen tract-level exports when available.
Run:  python build_equity_exposure.py
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# CORRIDOR PARAMETERS
# Values are illustrative, calibrated to CalEnviroScreen 4.0 reported ranges
# for tracts adjacent to these corridors.
# ──────────────────────────────────────────────────────────────────────────────
CORRIDORS = {
    "I-80 (Yolo / Sacramento)": {
        "burden_index_today"  : 78,    # traffic burden index (0-100 scale, relative)
        "disadvantaged_pct"   : 0.62,  # share of nearby census tracts flagged as DAC
        "aadt_thousandspday"  : 145,   # approximate AADT (thousands/day), PeMS avg
        "base_vmt_reduction"  : 0.10,  # expected VMT reduction under full reform
    },
    "SR-99 (Central Valley)": {
        "burden_index_today"  : 88,
        "disadvantaged_pct"   : 0.81,
        "aadt_thousandspday"  : 110,
        "base_vmt_reduction"  : 0.12,
    },
    "I-105 (Los Angeles)": {
        "burden_index_today"  : 92,
        "disadvantaged_pct"   : 0.89,
        "aadt_thousandspday"  : 190,
        "base_vmt_reduction"  : 0.14,
    },
    "I-710 (Long Beach)": {
        "burden_index_today"  : 100,   # reference corridor (highest burden)
        "disadvantaged_pct"   : 0.94,
        "aadt_thousandspday"  : 220,
        "base_vmt_reduction"  : 0.16,
    },
}

# Dose-response: each 1% VMT reduction → 0.6% near-road PM2.5 improvement
PM25_VMT_ELASTICITY = 0.60

# Additional co-benefit from investment shift (transit/active modes)
# reduces cold-start, idling → extra 5 % health improvement beyond VMT reduction
COBENFIT_FACTOR = 0.05

# Mark each reform's share of the full reform benefit (0–1 scale)
REFORM_STRENGTH = {
    "colorado_budget_lock"      : 0.55,
    "minnesota_capacity_trigger": 0.45,
    "virginia_scoring"          : 0.35,
    "massachusetts_caps"        : 0.65,
    "combined_approach"         : 1.00,
}

# ──────────────────────────────────────────────────────────────────────────────
# COMPUTE
# ──────────────────────────────────────────────────────────────────────────────
rows = []

for corridor, params in CORRIDORS.items():
    base    = params["burden_index_today"]
    vmt_red = params["base_vmt_reduction"]

    # Baseline row
    rows.append({
        "corridor"           : corridor,
        "scenario"           : "current_burden",
        "exposure_index"     : base,
        "disadvantaged_pct"  : params["disadvantaged_pct"],
        "aadt_thousands"     : params["aadt_thousandspday"],
    })

    for reform, strength in REFORM_STRENGTH.items():
        # Effective VMT reduction for this reform
        eff_vmt_red = vmt_red * strength

        # PM2.5 improvement
        pm25_improve = eff_vmt_red * PM25_VMT_ELASTICITY

        # Co-benefit (proportional to strength)
        cobenefit    = COBENFIT_FACTOR * strength

        # Total exposure reduction
        total_reduce = pm25_improve + cobenefit
        new_index    = round(base * (1 - total_reduce), 1)

        rows.append({
            "corridor"           : corridor,
            "scenario"           : reform,
            "exposure_index"     : new_index,
            "disadvantaged_pct"  : params["disadvantaged_pct"],
            "aadt_thousands"     : params["aadt_thousandspday"],
        })

df = pd.DataFrame(rows)

# Print comparison table (before vs. combined approach)
comp = df[df["scenario"].isin(["current_burden", "combined_approach"])].copy()
comp_pivot = comp.pivot(index="corridor", columns="scenario", values="exposure_index")
comp_pivot["reduction_pct"] = (
    (comp_pivot["current_burden"] - comp_pivot["combined_approach"])
    / comp_pivot["current_burden"] * 100
).round(1)
print("=== Equity Exposure: Before vs. Combined Reform ===")
print(comp_pivot.to_string())

out_dir = Path(__file__).parent
df.to_csv(out_dir / "equity_exposure.csv", index=False)
print(f"\nSaved: {out_dir / 'equity_exposure.csv'}")

# ──────────────────────────────────────────────────────────────────────────────
# JS export
# ──────────────────────────────────────────────────────────────────────────────
corridor_labels = list(CORRIDORS.keys())

before_values  = [CORRIDORS[c]["burden_index_today"] for c in corridor_labels]
after_combined = [
    df[(df["corridor"] == c) & (df["scenario"] == "combined_approach")]["exposure_index"].values[0]
    for c in corridor_labels
]
dac_pcts = [round(CORRIDORS[c]["disadvantaged_pct"] * 100, 0) for c in corridor_labels]

js_payload = {
    "corridor_labels": corridor_labels,
    "before_values"  : before_values,
    "after_combined" : after_combined,
    "dac_pcts"       : dac_pcts,
    "by_reform"      : {},
    "metadata": {
        "index_basis": "I-710 corridor = 100 (highest burden)",
        "vmt_pm25_elasticity": PM25_VMT_ELASTICITY,
        "source": "Calibrated to CalEnviroScreen 4.0 traffic burden scores",
        "note": "Conceptual / illustrative — replace with tract-level CalEnviroScreen exports",
    }
}

for reform in REFORM_STRENGTH:
    vals = [
        df[(df["corridor"] == c) & (df["scenario"] == reform)]["exposure_index"].values[0]
        for c in corridor_labels
    ]
    js_payload["by_reform"][reform] = vals

(out_dir / "equity_exposure_js.json").write_text(
    json.dumps(js_payload, indent=2), encoding="utf-8"
)
print(f"Saved: {out_dir / 'equity_exposure_js.json'}")
