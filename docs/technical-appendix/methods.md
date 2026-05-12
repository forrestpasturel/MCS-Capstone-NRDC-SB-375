# Technical Appendix Methods

## A. Diagnostic Mapping (Scenario 1 evidence)
- Unit of analysis: Census Block Group.
- Inputs: `vmt_index_cbg.csv`, `calenviroscreen40.csv`.
- Metric: VMT change % from first to last year in analysis window.
- Flag rule: rising VMT + pollution burden percentile >= 75.

## B. Congestion Rebound + Induced Demand (Scenario 2 evidence)
- Inputs: `pems_segment_timeseries.csv`, `induced_travel_inputs.csv`.
- Speed rebound metric:
  - post gain = post - pre
  - rebound = year_3 - post
  - rebound flag if year_3 <= pre
- Annual CO2 penalty = annual induced VMT * CO2 kg/VMT.

## C. Climate Floor Scenario Analysis (Scenario 3 evidence)
- Inputs: `emfac_scenario_a.csv`, `emfac_scenario_b.csv`.
- Compute annual and 20-year deltas for GHG, VMT, accessibility, equity.
- Climate floor score:
  - weighted sum of deltas
  - ineligible if score < 0

## D. Reproducibility
- Config file: `config/project.yaml`
- Pipeline entry point: `src/run_all.py`
- Output directories: `output/figures`, `output/tables`, `output/briefs`
