# Production Runbook

## 1) Intake and staging
1. Drop source files into `data/raw/`.
2. Validate required columns against `data/raw/schema_reference.csv`.
3. Confirm analysis window and corridor in `config/project.yaml`.

Optional auto-staging path:
- Update file-matching rules in `config/data_staging.yaml`.
- Run: `python -m src.pipeline.stage_raw_data`

## 2) Run analysis pipeline
- Command: `python -m src.run_all`
- This runs:
  - diagnostic implementation-gap build
  - congestion rebound + induced CO2 estimate
  - climate floor scenario scoring
  - figure generation

## 3) Validate outputs
Expected files:
- `data/processed/diagnostic_dataset.parquet`
- `data/processed/congestion_rebound_results.csv`
- `data/processed/climate_floor_results.csv`
- `output/figures/fig01_implementation_gap.png`
- `output/figures/fig02_congestion_rebound.png`
- `output/figures/fig03_climate_floor.png`

Pre-run quality check:
- `python -m src.pipeline.check_placeholder_data`
- Replace any files flagged as placeholder/synthetic before policy publication.

## 4) Publish artifacts
1. Fill `output/briefs/corridor-evidence-brief-template.md`.
2. Populate policy memo sections from `docs/policy-memo/outline.md`.
3. Build slide deck from `docs/slides/storyboard.md` and generated figures.

## 5) QA checklist
- Metrics are corridor-consistent across all visuals.
- Units are explicit (mph, VMT/capita, tons CO2e).
- Scenario assumptions are documented in technical appendix.
- Climate floor eligibility decision is traceable to score inputs.
