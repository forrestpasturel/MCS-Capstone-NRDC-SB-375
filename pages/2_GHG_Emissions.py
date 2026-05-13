"""
pages/2_GHG_Emissions.py
------------------------
Transportation GHG emission trends, EMFAC-based scenario modeling,
and multi-state comparison.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from src.data_processing import load_ca_ghg, load_multistate_ghg
from src.analysis import ghg_reduction_from_vmt, pct_change_from_baseline

st.set_page_config(page_title="GHG Emissions", page_icon="🌡️", layout="wide")
st.title("🌡️ Transportation GHG Emissions Analysis")
st.markdown(
    "California transportation sector emissions, multi-state per-capita comparison, "
    "and interactive EMFAC-based scenario modeling."
)

ca_ghg = load_ca_ghg()
ms_ghg = load_multistate_ghg()

# ---------------------------------------------------------------------------
# Section 1: CA transport GHG trend (stacked area)
# ---------------------------------------------------------------------------
st.subheader("1. California Transportation GHG Emissions (2000–2022)")
st.markdown(
    "Stacked by sub-sector: passenger vehicles, heavy-duty trucks, and other "
    "transportation (aviation, rail, marine). Data sourced from the CARB GHG "
    "Emission Inventory (EMFAC2021 methodology)."
)

fig_stack = go.Figure()
fig_stack.add_trace(
    go.Scatter(
        x=ca_ghg["year"],
        y=ca_ghg["passenger_vehicles_mmt"],
        name="Passenger Vehicles",
        stackgroup="one",
        fillcolor="#3498db",
        line=dict(color="#3498db"),
    )
)
fig_stack.add_trace(
    go.Scatter(
        x=ca_ghg["year"],
        y=ca_ghg["heavy_duty_mmt"],
        name="Heavy-Duty Trucks",
        stackgroup="one",
        fillcolor="#e74c3c",
        line=dict(color="#e74c3c"),
    )
)
fig_stack.add_trace(
    go.Scatter(
        x=ca_ghg["year"],
        y=ca_ghg["other_transport_mmt"],
        name="Other Transportation",
        stackgroup="one",
        fillcolor="#95a5a6",
        line=dict(color="#95a5a6"),
    )
)
fig_stack.add_hline(
    y=135.0,
    line_dash="dash",
    line_color="green",
    annotation_text="Approx. 2030 target trajectory",
)
fig_stack.update_layout(
    xaxis_title="Year",
    yaxis_title="Million Metric Tons CO₂e",
    hovermode="x unified",
    height=450,
)
st.plotly_chart(fig_stack, use_container_width=True)

# Metrics
latest_yr = ca_ghg.iloc[-1]
baseline_yr = ca_ghg[ca_ghg["year"] == 2008].iloc[0]
col1, col2, col3 = st.columns(3)
col1.metric("2022 Total Transport GHG", f"{latest_yr['transport_ghg_mmt']:.1f} MMT CO₂e")
col2.metric(
    "Change from 2008 Baseline",
    f"{((latest_yr['transport_ghg_mmt'] - baseline_yr['transport_ghg_mmt']) / baseline_yr['transport_ghg_mmt'] * 100):+.1f}%",
)
col3.metric(
    "Passenger Vehicle Share",
    f"{(latest_yr['passenger_vehicles_mmt'] / latest_yr['transport_ghg_mmt'] * 100):.1f}%",
)

# ---------------------------------------------------------------------------
# Section 2: Multi-state GHG per capita
# ---------------------------------------------------------------------------
st.subheader("2. Multi-State Transportation GHG per Capita (2008–2022)")
st.markdown(
    "Massachusetts shows the largest absolute reduction since 2008, reflecting its "
    "legally binding sub-sector targets under the Global Warming Solutions Act. "
    "Colorado's declining trajectory accelerated after SB 21-260 took effect."
)

year_range = st.slider(
    "Select year range",
    min_value=int(ms_ghg["year"].min()),
    max_value=int(ms_ghg["year"].max()),
    value=(2008, 2022),
    key="ghg_yr_range",
)
filt = ms_ghg[
    (ms_ghg["year"] >= year_range[0]) & (ms_ghg["year"] <= year_range[1])
]

color_map = {
    "California": "#e74c3c",
    "Colorado": "#3498db",
    "Massachusetts": "#2ecc71",
    "Minnesota": "#9b59b6",
    "Virginia": "#f39c12",
}

fig_ms = px.line(
    filt,
    x="year",
    y="ghg_per_capita_tonnes",
    color="state",
    color_discrete_map=color_map,
    markers=True,
    labels={
        "ghg_per_capita_tonnes": "Transport GHG per Capita (tCO₂e/yr)",
        "year": "Year",
    },
)
fig_ms.update_layout(height=420, hovermode="x unified")
st.plotly_chart(fig_ms, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 3: EMFAC-based scenario modeler
# ---------------------------------------------------------------------------
st.subheader("3. EMFAC-Based GHG Reduction Scenario Modeler")
st.markdown(
    "Estimate the annual GHG reduction achievable from a given VMT reduction, "
    "using the CARB EMFAC2021 statewide average emission factor "
    "(**0.338 kg CO₂e per VMT**)."
)

col_a, col_b = st.columns(2)
with col_a:
    vmt_reduction_pct = st.slider(
        "VMT Reduction (%)", min_value=1, max_value=30, value=8, step=1
    )
with col_b:
    base_vmt_billion = st.number_input(
        "Base VMT (billion miles/year)",
        min_value=100.0,
        max_value=500.0,
        value=362.4,
        step=1.0,
        help="California statewide VMT 2022 ≈ 362 billion miles",
    )

result = ghg_reduction_from_vmt(vmt_reduction_pct, base_vmt_billion)

col1, col2, col3 = st.columns(3)
col1.metric(
    f"{vmt_reduction_pct}% VMT Reduction",
    f"{result['vmt_reduced_billion']:.1f} B miles/yr fewer",
)
col2.metric(
    "Annual GHG Reduction",
    f"{result['ghg_reduced_mmt']:.1f} MMT CO₂e/yr",
)
col3.metric(
    "Share of 2022 Transport GHG",
    f"{(result['ghg_reduced_mmt'] / latest_yr['transport_ghg_mmt'] * 100):.1f}%",
)

st.info(
    "**Interpretation:** A {pct}% statewide VMT reduction — the SCAG 2035 SB 375 "
    "target — would reduce California's annual transportation GHG emissions by "
    "approximately **{ghg} MMT CO₂e**, or about {share:.0f}% of the 2022 "
    "transportation sector total. This is equivalent to removing roughly "
    "{cars:,} average passenger cars from the road.".format(
        pct=vmt_reduction_pct,
        ghg=result["ghg_reduced_mmt"],
        share=(result["ghg_reduced_mmt"] / latest_yr["transport_ghg_mmt"] * 100),
        cars=int(result["ghg_reduced_mmt"] * 1e6 / 4.6),
    )
)

# ---------------------------------------------------------------------------
# Section 4: Percent change from 2008 (GHG)
# ---------------------------------------------------------------------------
st.subheader("4. Percent Change in Transport GHG per Capita Since 2008")

pct_rows = []
for state, grp in ms_ghg.groupby("state"):
    grp = grp.sort_values("year").reset_index(drop=True)
    pct = pct_change_from_baseline(grp["ghg_per_capita_tonnes"], grp["year"], 2008)
    for i, row in grp.iterrows():
        pct_rows.append({"year": row["year"], "state": state, "pct_change": pct.iloc[i]})

import pandas as pd
pct_df = pd.DataFrame(pct_rows)
pct_filt = pct_df[
    (pct_df["year"] >= year_range[0]) & (pct_df["year"] <= year_range[1])
]

fig_pct = px.line(
    pct_filt,
    x="year",
    y="pct_change",
    color="state",
    color_discrete_map=color_map,
    markers=True,
    labels={"pct_change": "% Change from 2008 Baseline", "year": "Year"},
)
fig_pct.add_hline(y=0, line_dash="dash", line_color="gray")
fig_pct.update_layout(height=400, hovermode="x unified")
st.plotly_chart(fig_pct, use_container_width=True)

with st.expander("📋 View raw data"):
    st.dataframe(
        ms_ghg.pivot(index="year", columns="state", values="ghg_per_capita_tonnes")
    )
