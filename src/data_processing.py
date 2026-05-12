from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "app"


def _load_csv(file_name: str, postprocess: Callable[[pd.DataFrame], pd.DataFrame] | None = None) -> pd.DataFrame:
    path = DATA_DIR / file_name
    df = pd.read_csv(path)
    if postprocess is not None:
        df = postprocess(df)
    return df


def load_ca_vmt_targets_actual() -> pd.DataFrame:
    return _load_csv("ca_vmt_targets_actual.csv")


def load_state_vmt_per_capita() -> pd.DataFrame:
    return _load_csv("state_vmt_per_capita.csv")


def load_ca_transport_ghg_subsectors() -> pd.DataFrame:
    return _load_csv("ca_transport_ghg_subsectors.csv")


def load_state_ghg_per_capita() -> pd.DataFrame:
    return _load_csv("state_ghg_per_capita.csv")


def load_state_framework_dimensions() -> pd.DataFrame:
    return _load_csv("state_framework_dimensions.csv")


def load_state_framework_provisions() -> pd.DataFrame:
    return _load_csv("state_framework_provisions.csv")


def load_calenviroscreen_health() -> pd.DataFrame:
    return _load_csv("calenviroscreen_health.csv")


def load_policy_reform_actions() -> pd.DataFrame:
    return _load_csv("policy_reform_actions.csv")


def load_ca_zcta_spatial() -> pd.DataFrame:
    """ZCTA-level spatial attributes: pollution burden, VMT gap, GHG per capita."""
    df = _load_csv("ca_zcta_spatial.csv")
    df['zcta'] = df['zcta'].astype(str).str.zfill(5)
    return df


def load_all_datasets() -> dict[str, pd.DataFrame]:
    return {
        "ca_vmt_targets_actual": load_ca_vmt_targets_actual(),
        "state_vmt_per_capita": load_state_vmt_per_capita(),
        "ca_transport_ghg_subsectors": load_ca_transport_ghg_subsectors(),
        "state_ghg_per_capita": load_state_ghg_per_capita(),
        "state_framework_dimensions": load_state_framework_dimensions(),
        "state_framework_provisions": load_state_framework_provisions(),
        "calenviroscreen_health": load_calenviroscreen_health(),
        "policy_reform_actions": load_policy_reform_actions(),
    }
