# Data Layout

- raw/: source files from VMTIndex, CalEnviroScreen, PeMS, NCST, EMFAC/TDM exports.
- interim/: optional cleaned intermediate files.
- processed/: analysis outputs consumed by charts and memo tables.

## Required raw files

1. vmt_index_cbg.csv
2. calenviroscreen40.csv
3. pems_segment_timeseries.csv
4. induced_travel_inputs.csv
5. emfac_scenario_a.csv
6. emfac_scenario_b.csv

See [data/raw/schema_reference.csv](raw/schema_reference.csv) for minimum columns.
