"""
data_processing.py
------------------
Loads and pre-processes the datasets used throughout the SB 375 Capstone
dashboard.  All data are representative figures drawn from publicly available
sources (CARB GHG Inventory, Caltrans HPMS, CalEnviroScreen 4.0, FHWA, US
Census Bureau) and are suitable for illustrative policy analysis.
"""
from __future__ import annotations

import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")


# ---------------------------------------------------------------------------
# 1. California statewide VMT (billions of vehicle-miles, 2000-2022)
#    Source: Caltrans HPMS / DOT annual reports
# ---------------------------------------------------------------------------
def load_ca_vmt() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "ca_vmt.csv")
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(int)
    return df


# ---------------------------------------------------------------------------
# 2. California per-capita VMT vs. SB 375 target trajectory
#    Source: CARB SB 375 target-setting, US Census population estimates
# ---------------------------------------------------------------------------
def load_ca_vmt_per_capita() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "ca_vmt_per_capita.csv")
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(int)
    return df


# ---------------------------------------------------------------------------
# 3. California transportation GHG emissions (million metric tons CO2e)
#    Source: CARB GHG Emission Inventory (EMFAC-based)
# ---------------------------------------------------------------------------
def load_ca_ghg() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "ca_ghg_transport.csv")
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(int)
    return df


# ---------------------------------------------------------------------------
# 4. Multi-state VMT per capita comparison (CA, CO, MA, MN, VA)
#    Source: FHWA Highway Statistics, US Census Bureau
# ---------------------------------------------------------------------------
def load_multistate_vmt() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "multistate_vmt_per_capita.csv")
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(int)
    return df


# ---------------------------------------------------------------------------
# 5. Multi-state GHG emissions per capita (transport sector)
#    Source: EPA State GHG Inventories, FHWA Highway Statistics
# ---------------------------------------------------------------------------
def load_multistate_ghg() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "multistate_ghg_per_capita.csv")
    df = pd.read_csv(path)
    df["year"] = df["year"].astype(int)
    return df


# ---------------------------------------------------------------------------
# 6. California county-level health / pollution burden
#    Source: CalEnviroScreen 4.0 (OEHHA)
# ---------------------------------------------------------------------------
def load_calenviroscreen() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "calenviroscreen_county.csv")
    df = pd.read_csv(path)
    return df


# ---------------------------------------------------------------------------
# 7. State framework scoring matrix
#    Expert-coded assessment of each state's legislative framework across
#    six policy dimensions relevant to SB 375 reform.
# ---------------------------------------------------------------------------
def load_framework_scores() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "framework_scores.csv")
    df = pd.read_csv(path)
    return df


# ---------------------------------------------------------------------------
# 8. State framework detailed provisions
# ---------------------------------------------------------------------------
def load_framework_details() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "framework_details.csv")
    df = pd.read_csv(path)
    return df


# ---------------------------------------------------------------------------
# Helper: compute a simple trend line (linear regression)
# ---------------------------------------------------------------------------
def linear_trend(series: pd.Series, years: pd.Series) -> pd.Series:
    """Return fitted values from a linear regression of *series* on *years*."""
    x = years.values.astype(float)
    y = series.values.astype(float)
    valid = ~(np.isnan(x) | np.isnan(y))
    if valid.sum() < 2:
        return series
    coeffs = np.polyfit(x[valid], y[valid], 1)
    return pd.Series(np.polyval(coeffs, x), index=series.index)
