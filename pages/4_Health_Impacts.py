"""
pages/4_Health_Impacts.py
-------------------------
CalEnviroScreen-based analysis of disproportionate pollution burden
in California communities related to highway traffic.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.data_processing import load_calenviroscreen

st.set_page_config(page_title="Health Impacts", page_icon="🏥", layout="wide")
st.title("🏥 Highway Proximity & Community Health Impacts")
st.markdown(
    "Analysis of traffic-related pollution burden in California counties, "
    "based on CalEnviroScreen 4.0 (OEHHA, 2021). Demonstrates the co-benefit "
    "of VMT reduction for environmental justice communities."
)

df = load_calenviroscreen()

# ---------------------------------------------------------------------------
# Section 1: Overview metrics
# ---------------------------------------------------------------------------
dac = df[df["disadvantaged_community"] == "Yes"]
non_dac = df[df["disadvantaged_community"] == "No"]

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Avg Pollution Burden (DAC counties)",
    f"{dac['pollution_burden_score'].mean():.1f} / 10",
)
col2.metric(
    "Avg Pollution Burden (non-DAC counties)",
    f"{non_dac['pollution_burden_score'].mean():.1f} / 10",
)
col3.metric(
    "Avg Traffic Density Percentile (DAC)",
    f"{dac['traffic_density_percentile'].mean():.0f}th",
)
col4.metric(
    "Avg Low-Income Population (DAC)",
    f"{dac['low_income_pct'].mean():.1f}%",
)

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Bubble chart – pollution burden vs traffic density
# ---------------------------------------------------------------------------
st.subheader("1. Pollution Burden vs. Traffic Density by County")
st.markdown(
    "Bubble size = low-income population share. Red = Disadvantaged Community "
    "(SB 535 definition). Counties in the upper-right quadrant face the highest "
    "combined burden and are primary targets for SB 375 reform."
)

fig_bubble = px.scatter(
    df,
    x="traffic_density_percentile",
    y="pollution_burden_score",
    size="low_income_pct",
    color="disadvantaged_community",
    hover_name="county",
    color_discrete_map={"Yes": "#e74c3c", "No": "#3498db"},
    labels={
        "traffic_density_percentile": "Traffic Density Percentile (CalEnviroScreen)",
        "pollution_burden_score": "Pollution Burden Score (0–10)",
        "disadvantaged_community": "SB 535 DAC",
    },
    size_max=40,
)
fig_bubble.add_vline(
    x=75, line_dash="dash", line_color="gray",
    annotation_text="75th percentile threshold"
)
fig_bubble.add_hline(
    y=7.0, line_dash="dash", line_color="gray",
    annotation_text="High burden threshold"
)
fig_bubble.update_layout(height=500)
st.plotly_chart(fig_bubble, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 3: PM2.5 and Diesel PM comparison
# ---------------------------------------------------------------------------
st.subheader("2. PM₂.₅ and Diesel PM Percentiles by County")
st.markdown(
    "Both PM₂.₅ and diesel particulate matter (PM) are directly linked to "
    "heavy vehicle traffic on California highways. Communities near freight "
    "corridors (e.g., Inland Empire, Central Valley) face compounded exposure."
)

import pandas as pd
pm_df = df[["county", "pm25_percentile", "diesel_pm_percentile", "disadvantaged_community"]].sort_values(
    "pm25_percentile", ascending=False
)

fig_pm = go.Figure()
fig_pm.add_trace(
    go.Bar(
        y=pm_df["county"],
        x=pm_df["pm25_percentile"],
        name="PM₂.₅ Percentile",
        orientation="h",
        marker_color="#e74c3c",
    )
)
fig_pm.add_trace(
    go.Bar(
        y=pm_df["county"],
        x=pm_df["diesel_pm_percentile"],
        name="Diesel PM Percentile",
        orientation="h",
        marker_color="#c0392b",
        opacity=0.7,
    )
)
fig_pm.update_layout(
    barmode="group",
    xaxis_title="CalEnviroScreen Percentile",
    height=560,
    hovermode="y unified",
)
st.plotly_chart(fig_pm, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 4: Equity analysis narrative
# ---------------------------------------------------------------------------
st.subheader("3. Equity Implications for SB 375 Reform")
st.markdown(
    """
The CalEnviroScreen analysis reveals a consistent pattern:

- **Disadvantaged communities** (designated under SB 535) score significantly
  higher on both pollution burden and traffic density percentiles than non-DAC
  counties.
- **The Central Valley** (Fresno, Merced, Madera, Kings, Tulare, San Joaquin)
  combines among the highest PM₂.₅ levels in the state with low-income
  populations exceeding 44%, yet these counties are outside major MPO
  jurisdictions and largely exempt from SB 375 planning requirements.
- **The Inland Empire** (San Bernardino, Riverside) is home to the largest
  concentration of warehousing and freight activity in the Western US, driving
  diesel PM exposures that disproportionately burden low-income communities of
  color.

### Policy Implication

Current SB 375 does not mandate that Sustainable Communities Strategies
demonstrate a **net benefit** to disadvantaged communities. The Massachusetts
GWSA and Colorado GHG Program both include explicit environmental justice
provisions. Proposed SB 375 reform should:

1. **Require** each SCS to include a Displacement Risk Analysis and demonstrate
   measurable air quality improvements in CalEnviroScreen top-quartile
   communities.
2. **Allocate** ≥25% of VMT Reduction Trust Fund resources to SB 535 DAC
   projects, consistent with AB 1550 principles.
3. **Expand** SB 375 applicability to rural / non-MPO regions through a Caltrans-
   administered rural VMT-reduction framework, closing the Central Valley gap.
"""
)

with st.expander("📋 View county-level data"):
    st.dataframe(df)
