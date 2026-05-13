"""
app.py – SB 375 Capstone Dashboard (main entry point)
======================================================
Run with:
    streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="SB 375 Capstone – VMT & GHG Framework Analysis",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar navigation (Streamlit multi-page via pages/ folder is used, but this
# home page provides the project overview and landing experience)
# ---------------------------------------------------------------------------
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Flag_of_California.svg/320px-Flag_of_California.svg.png",
    use_container_width=True,
)
st.sidebar.markdown("## Navigation")
st.sidebar.markdown(
    """
Use the **Pages** menu above to explore:

- 🏠 **Home** *(this page)*
- 📊 **VMT Analysis**
- 🌡️ **GHG Emissions**
- 🗺️ **State Framework Comparison**
- 🏥 **Health Impacts**
- 💡 **Policy Recommendations**
"""
)

# ---------------------------------------------------------------------------
# Hero section
# ---------------------------------------------------------------------------
st.title("🌿 SB 375 Reform Capstone")
st.subheader(
    "Assessing Multi-State VMT & GHG Reduction Frameworks to Strengthen "
    "California's Sustainable Communities Strategy"
)

col1, col2, col3 = st.columns(3)
col1.metric(
    label="California 2022 Per-Capita VMT",
    value="8,960 mi/yr",
    delta="+1.1% vs 2019 trend",
    delta_color="inverse",
)
col2.metric(
    label="SB 375 2035 Target (SCAG)",
    value="7,520 mi/yr",
    delta="−17% from 2008 baseline",
)
col3.metric(
    label="Implementation Gap (2022)",
    value="~1,440 mi/capita",
    delta="Growing since 2015",
    delta_color="inverse",
)

st.divider()

# ---------------------------------------------------------------------------
# Project overview
# ---------------------------------------------------------------------------
st.markdown(
    """
## Project Overview

Since its enactment in **2008**, California's *Sustainable Communities and Climate
Protection Act* (**SB 375**) has been the primary statutory tool for aligning
regional land-use and transportation planning with GHG reduction targets.
Under SB 375, each Metropolitan Planning Organization (MPO) is required to
prepare a **Sustainable Communities Strategy (SCS)** — a land-use scenario
demonstrating how the region will meet its CARB-established per-capita GHG
reduction target.

### The Implementation Gap

Despite over 15 years of planning mandates, **actual per-capita VMT in California
continues to rise**, while SCS targets project steady declines.  Key contributing
factors include:

- **Non-binding targets:** MPOs face no enforceable consequence for missing SCS
  milestones.
- **Weak land-use override authority:** Local zoning decisions can undermine SCS
  projections without recourse.
- **Insufficient monitoring:** Performance is tracked with modeled projections, not
  observed VMT.
- **Inadequate funding linkages:** No dedicated, outcomes-based funding stream for
  Transportation Demand Management (TDM).
- **Equity gaps:** Disadvantaged communities bear a disproportionate pollution burden
  yet receive inconsistent SCS protections.

### This Capstone

This dashboard examines four out-of-state legislative and programmatic frameworks —
**Colorado's GHG Program**, the **Massachusetts Global Warming Solutions Act**,
**Minnesota's GHG Assessment**, and **Virginia's SMART Scale** — to identify specific
provisions, data tools, and accountability mechanisms that can be translated into
proposed SB 375 reform language for California.

Use the sidebar pages to explore:
1. **VMT Analysis** – Statewide VMT trends vs. targets and multi-state comparison
2. **GHG Emissions** – CARB EMFAC-informed emissions trends and scenario modeling
3. **State Framework Comparison** – Scored assessment of each state's legislative
   framework across six policy dimensions
4. **Health Impacts** – CalEnviroScreen-based analysis of disproportionate pollution
   burden in California communities
5. **Policy Recommendations** – Specific reform language drawn from multi-state
   lessons learned
"""
)

st.divider()

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------
with st.expander("📚 Data Sources & Methodology"):
    st.markdown(
        """
### Primary Data Sources

| Dataset | Source | Use in This Project |
|---|---|---|
| California Statewide VMT | Caltrans HPMS Annual Report | Statewide VMT trends (2000–2022) |
| Per-Capita VMT vs. SB 375 Targets | CARB Target-Setting Technical Analysis; US Census | Implementation gap calculation |
| Transportation GHG Emissions | CARB GHG Emission Inventory (EMFAC2021) | Emissions trend analysis |
| Multi-State VMT per Capita | FHWA Highway Statistics Table VM-2; US Census | Cross-state VMT comparison |
| Multi-State GHG per Capita | EPA State GHG Inventories; FHWA | Cross-state emissions comparison |
| County Pollution Burden | CalEnviroScreen 4.0 (OEHHA, 2021) | Environmental justice mapping |
| GHG Emission Factor | CARB EMFAC2021 (statewide average 2020) | GHG reduction scenario modeling |

### Methodology

- **Implementation gap** = actual per-capita VMT minus CARB-adopted SCS target VMT for
  the SCAG region (the largest MPO, representing ~50% of CA population).
- **GHG reduction estimates** use the EMFAC2021 statewide average emission factor of
  **0.338 kg CO₂e per VMT**.
- **Framework scores** are expert-coded on a 0–10 scale across six dimensions:
  Binding Targets, Enforcement & Accountability, Equity Provisions, Data & Monitoring,
  Land-Use Integration, and Funding Mechanisms.
- All per-capita calculations use US Census Bureau mid-year population estimates.
"""
    )
