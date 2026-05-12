# MCS-Capstone-NRDC-SB-375

Production workspace for the capstone project:
**Strengthening SB 1087: Guardrails for Performance-Based Transportation Funding**

## Project objective

Build a reproducible, evidence-first policy package with three linked products:

1. Policy memo
2. Technical appendix
3. Visual story (slides/figures) for a corridor case (default: I-80 Yolo County)

The analysis is organized around three accountability pillars:

- Pillar 1: Corrective Action moratorium
- Pillar 2: VMT neutrality and mitigation banking
- Pillar 3: Objective need and climate floor

## Repository structure

- docs/
	- policy-memo/outline.md
	- technical-appendix/methods.md
	- slides/storyboard.md
- data/
	- raw/ (source drops)
	- interim/
	- processed/ (pipeline outputs)
- src/
	- pipeline/
		- 01_build_diagnostic_dataset.py
		- 02_congestion_rebound_analysis.py
		- 03_climate_floor_scenarios.py
		- utils.py
	- viz/build_figures.py
	- run_all.py
- config/project.yaml
- output/
	- figures/
	- tables/
	- briefs/

## Data inputs required

Place required source files in data/raw:

1. vmt_index_cbg.csv
2. calenviroscreen40.csv
3. pems_segment_timeseries.csv
4. induced_travel_inputs.csv
5. emfac_scenario_a.csv
6. emfac_scenario_b.csv

Minimum column requirements are documented in:
data/raw/schema_reference.csv

## Quick start

1. Create and activate a Python environment.
2. Install dependencies:

	 pip install -r requirements.txt

3. Confirm path settings in:

	 config/project.yaml

4. Run full pipeline:

	 python -m src.run_all

## Outputs

Generated analysis outputs:

- data/processed/diagnostic_dataset.parquet
- data/processed/congestion_rebound_results.csv
- data/processed/climate_floor_results.csv

Generated figures:

- output/figures/fig01_implementation_gap.png
- output/figures/fig02_congestion_rebound.png
- output/figures/fig03_climate_floor.png

Draft policy artifact template:

- output/briefs/corridor-evidence-brief-template.md

## Dashboard application

Streamlit app structure:

- app.py
- pages/1_VMT_Analysis.py
- pages/2_GHG_Emissions.py
- pages/3_State_Framework_Comparison.py
- pages/4_Health_Impacts.py
- pages/5_Policy_Recommendations.py
- src/data_processing.py
- src/analysis.py

Bundled dashboard datasets are in data/app:

1. ca_vmt_targets_actual.csv
2. state_vmt_per_capita.csv
3. ca_transport_ghg_subsectors.csv
4. state_ghg_per_capita.csv
5. state_framework_dimensions.csv
6. state_framework_provisions.csv
7. calenviroscreen_health.csv
8. policy_reform_actions.csv

Run dashboard:

    streamlit run app.py

Run tests:

    pytest -q

## Notes

- Scripts intentionally enforce minimum schema checks.
- Weighting for climate floor scoring is a starting policy calibration and should be iterated with advisor/stakeholder input.
- Current dashboard data is representative and intended for analysis prototyping; replace with final validated sources for publication.
