"""
build_ghg_scenarios.py
======================
Computes conceptual GHG emission trajectories for the SB 375 / SB 1087 website.

Methodology:
  1. Start from a 2025 GHG index (= 100) representing CA transportation sector emissions.
  2. BAU: emissions grow roughly in line with VMT (BAU VMT growth rate + slight efficiency gain).
  3. Reform scenarios: combine two effects per year —
       (a) Avoided induced VMT via guardrail (from VMT script rates)
       (b) Fleet efficiency improvement trend (CARB ZEV targets ~3 % / yr fleet-avg improvement)
  4. Induced-travel GHG uses EMFAC2021-derived light-duty CO₂ factor:
       ~0.282 kg CO₂ per VMT (fleet-average, 2025 model year mix; EMFAC2021 statewide)

Sources / references:
  - CARB EMFAC2021: https://arb.ca.gov/emfac/
  - NCST Induced Travel Calculator elasticity: 0.65 (Handy & Boarnet)
  - CARB Advanced Clean Cars II / ZEV mandate: fleet efficiency improvement ~3 % / yr

Replace PARAM block with EMFAC model outputs or CARB inventory data when available.
Run:  python build_ghg_scenarios.py
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# PARAMETERS
# ──────────────────────────────────────────────────────────────────────────────
START_YEAR          = 2025
END_YEAR            = 2045
YEARS               = list(range(START_YEAR, END_YEAR + 1, 5))

GHG_INDEX_2025      = 100.0    # baseline index

# BAU: net emission change per year
# VMT grows ~0.4 % / yr; fleet efficiency improves ~1.2 % / yr → net ~-0.8 % / yr
BAU_NET_RATE        = -0.008   # slight decline even without reform (ZEV penetration)

# EMFAC-based CO₂ factor (tons per 1000 VMT), light-duty fleet average 2025
CO2_PER_1000VMT     = 0.282    # kg CO₂ per VMT → 0.282 tons / 1000 VMT

# Induced VMT suppression rates (same as VMT script, per year)
SUPPRESS_RATES = {
    "colorado_budget_lock"      : 0.008,
    "minnesota_capacity_trigger": 0.006,
    "virginia_scoring"          : 0.004,
    "massachusetts_caps"        : 0.010,
    "combined_approach"         : 0.018,
}

# Additional fleet efficiency gain from reform (investment shifts to EVs, transit)
REFORM_EFFICIENCY_BONUS = 0.003   # +0.3 % / yr on top of BAU fleet improvement

# ──────────────────────────────────────────────────────────────────────────────
# COMPUTE
# ──────────────────────────────────────────────────────────────────────────────

def ghg_index(start: float, annual_rate: float, n_years: int) -> float:
    return round(start * ((1 + annual_rate) ** n_years), 2)


rows = []

for yr in YEARS:
    n = yr - START_YEAR

    # BAU
    bau = ghg_index(GHG_INDEX_2025, BAU_NET_RATE, n)
    rows.append({"year": yr, "scenario": "california_today_bau", "ghg_index": bau})

    # Massachusetts-style cap as reference ceiling
    # (hard annual cap forces aggressive fleet turnover + reduced VMT)
    ma_cap_rate = BAU_NET_RATE - SUPPRESS_RATES["massachusetts_caps"] - REFORM_EFFICIENCY_BONUS
    rows.append({
        "year": yr,
        "scenario": "massachusetts_style_annual_cap_ceiling",
        "ghg_index": ghg_index(GHG_INDEX_2025, ma_cap_rate, n)
    })

    # Each reform scenario
    for name, suppress in SUPPRESS_RATES.items():
        # Net rate = BAU drift - VMT suppression effect - bonus efficiency
        # Convert VMT suppression to GHG suppression (roughly proportional, slightly lower
        # because fleet is already partially electrified; use 0.75 pass-through factor)
        ghg_suppress = suppress * 0.75 + REFORM_EFFICIENCY_BONUS
        net_rate = BAU_NET_RATE - ghg_suppress
        rows.append({
            "year": yr,
            "scenario": name,
            "ghg_index": ghg_index(GHG_INDEX_2025, net_rate, n)
        })

df = pd.DataFrame(rows)
pivot = df.pivot(index="year", columns="scenario", values="ghg_index").reset_index()
print("=== GHG Index Scenarios (2025 = 100) ===")
print(pivot.to_string(index=False))

out_dir = Path(__file__).parent
df.to_csv(out_dir / "ghg_scenarios.csv", index=False)
print(f"\nSaved: {out_dir / 'ghg_scenarios.csv'}")

# JS export
scenario_order = [
    "california_today_bau",
    "massachusetts_style_annual_cap_ceiling",
    "colorado_budget_lock",
    "minnesota_capacity_trigger",
    "virginia_scoring",
    "massachusetts_caps",
    "combined_approach",
]

js_payload = {
    "years": YEARS,
    "scenarios": {},
    "metadata": {
        "index_basis": "2025 CA transportation GHG = 100",
        "co2_factor_kg_per_vmt": CO2_PER_1000VMT,
        "bau_net_rate_pct_yr": BAU_NET_RATE * 100,
        "source": "Derived from EMFAC2021 fleet-average CO₂ factor + NCST induced-travel elasticity",
        "note": "Conceptual / illustrative — replace with EMFAC model runs when available",
    }
}
for name in scenario_order:
    if name in df["scenario"].values:
        subset = df[df["scenario"] == name].sort_values("year")
        js_payload["scenarios"][name] = subset["ghg_index"].tolist()

(out_dir / "ghg_scenarios_js.json").write_text(
    json.dumps(js_payload, indent=2), encoding="utf-8"
)
print(f"Saved: {out_dir / 'ghg_scenarios_js.json'}")
