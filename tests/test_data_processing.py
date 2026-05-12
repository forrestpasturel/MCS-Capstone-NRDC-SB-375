from __future__ import annotations

import pandas as pd
import pytest

from src import data_processing as dp


LOADERS = [
    ("ca_vmt_targets_actual", dp.load_ca_vmt_targets_actual, {"year", "actual_vmt_index", "target_vmt_index", "actual_vmt_per_capita"}),
    ("state_vmt_per_capita", dp.load_state_vmt_per_capita, {"year", "state", "vmt_per_capita"}),
    ("ca_transport_ghg_subsectors", dp.load_ca_transport_ghg_subsectors, {"year", "light_duty_mmt", "heavy_duty_mmt", "aviation_mmt", "rail_mmt", "marine_mmt"}),
    ("state_ghg_per_capita", dp.load_state_ghg_per_capita, {"year", "state", "ghg_per_capita_transport"}),
    ("state_framework_dimensions", dp.load_state_framework_dimensions, {"state", "planning_mandate_strength", "funding_accountability", "induced_demand_controls", "equity_targeting", "monitoring_enforcement", "multimodal_investment"}),
    ("state_framework_provisions", dp.load_state_framework_provisions, {"state", "policy_dimension", "current_provision", "recommended_ca_reform"}),
    ("calenviroscreen_health", dp.load_calenviroscreen_health, {"tract_id", "region", "pollution_burden", "traffic_density", "pm25", "diesel_pm", "disadvantaged_share"}),
    ("policy_reform_actions", dp.load_policy_reform_actions, {"action", "pillar", "impact", "feasibility", "annual_vmt_savings_million", "start_year", "end_year", "phase"}),
]


@pytest.mark.parametrize("_name,loader,_cols", LOADERS)
def test_loader_returns_dataframe(_name, loader, _cols):
    df = loader()
    assert isinstance(df, pd.DataFrame)


@pytest.mark.parametrize("_name,loader,_cols", LOADERS)
def test_loader_not_empty(_name, loader, _cols):
    df = loader()
    assert len(df) > 0


@pytest.mark.parametrize("_name,loader,cols", LOADERS)
def test_loader_has_expected_columns(_name, loader, cols):
    df = loader()
    assert cols.issubset(set(df.columns))
