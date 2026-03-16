# MCS-Capstone-NRDC-SB-375

Since 2008, California's **SB 375** (Sustainable Communities and Climate Protection Act)
has relied on planning mandates that have failed to curb transportation emissions.
Current data shows a widening **Implementation Gap**: California is on track for a 29%
VMT reduction in its Sustainable Communities Strategies, but actual per-capita VMT
continues to *increase* statewide.

This Capstone investigates possible solutions by comparing SB 375 to four out-of-state
legislative frameworks and translating their most effective provisions into concrete
SB 375 reform language:

| State | Framework |
|-------|-----------|
| Colorado | [CDOT GHG Program (SB 21-260)](https://www.codot.gov/programs/environmental/greenhousegas) |
| Massachusetts | [Global Warming Solutions Act – Transportation Requirements (310 CMR 60.05)](https://www.law.cornell.edu/regulations/massachusetts/310-CMR-60-05) |
| Minnesota | [MnDOT GHG Assessment](https://www.dot.state.mn.us/sustainability/ghg-assessment.html) |
| Virginia | [SMART Scale](https://smartscale.virginia.gov/) |

---

## Dashboard

The project is delivered as an interactive **Streamlit** dashboard with five analytical
pages:

| Page | Description |
|------|-------------|
| 🏠 Home | Project overview, implementation gap summary |
| 📊 VMT Analysis | Statewide VMT trends vs. SB 375 targets; multi-state comparison |
| 🌡️ GHG Emissions | CARB EMFAC-based emissions modeling and scenario tool |
| 🗺️ State Framework Comparison | Scored radar chart, heatmap, and detailed provisions explorer |
| 🏥 Health Impacts | CalEnviroScreen-based pollution burden analysis |
| 💡 Policy Recommendations | Reform priority matrix, waterfall scenario, and phased roadmap |

---

## Quick Start

### Prerequisites

- Python 3.9+
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the dashboard

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Project Structure

```
.
├── app.py                        # Streamlit home page (entry point)
├── pages/
│   ├── 1_VMT_Analysis.py
│   ├── 2_GHG_Emissions.py
│   ├── 3_State_Framework_Comparison.py
│   ├── 4_Health_Impacts.py
│   └── 5_Policy_Recommendations.py
├── src/
│   ├── __init__.py
│   ├── data_processing.py        # CSV loaders for all datasets
│   └── analysis.py               # Core analytical functions
├── data/
│   └── processed/
│       ├── ca_vmt.csv
│       ├── ca_vmt_per_capita.csv
│       ├── ca_ghg_transport.csv
│       ├── multistate_vmt_per_capita.csv
│       ├── multistate_ghg_per_capita.csv
│       ├── calenviroscreen_county.csv
│       ├── framework_scores.csv
│       └── framework_details.csv
├── tests/
│   ├── test_data_processing.py
│   └── test_analysis.py
└── requirements.txt
```

---

## Data Sources

| Dataset | Source |
|---------|--------|
| California Statewide VMT | Caltrans HPMS Annual Report |
| Per-Capita VMT vs. SB 375 Targets | CARB SB 375 Target-Setting; US Census |
| Transportation GHG Emissions | CARB GHG Emission Inventory (EMFAC2021) |
| Multi-State VMT per Capita | FHWA Highway Statistics Table VM-2; US Census |
| Multi-State GHG per Capita | EPA State GHG Inventories; FHWA |
| County Pollution Burden | CalEnviroScreen 4.0 (OEHHA, 2021) |
| GHG Emission Factor | CARB EMFAC2021 (0.338 kg CO₂e / VMT) |

---

## Running Tests

```bash
python -m pytest tests/ -v
```

58 tests cover all data-loading and analytical functions.
