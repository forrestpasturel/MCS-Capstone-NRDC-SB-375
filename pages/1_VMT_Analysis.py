"""
pages/1_VMT_Analysis.py
-----------------------
Vehicle Miles Traveled trends, implementation gap, and multi-state comparison.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from src.data_processing import load_ca_vmt, load_ca_vmt_per_capita, load_multistate_vmt
from src.analysis import compute_implementation_gap, pct_change_from_baseline

st.set_page_config(page_title="VMT Analysis", page_icon="📊", layout="wide")
st.title("📊 Vehicle Miles Traveled (VMT) Analysis")
st.markdown(
    "Statewide VMT trends, the SB 375 implementation gap, and how California "
    "compares to Colorado, Massachusetts, Minnesota, and Virginia."
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
ca_vmt = load_ca_vmt()
ca_pc = load_ca_vmt_per_capita()
ms_vmt = load_multistate_vmt()

# ---------------------------------------------------------------------------
# Section 1: Statewide total VMT trend
# ---------------------------------------------------------------------------
st.subheader("1. California Statewide VMT (2000–2022)")
st.markdown(
    "Total annual VMT from Caltrans Highway Performance Monitoring System (HPMS). "
    "The brief dip in 2008–2009 (Great Recession) and the sharp drop in 2020 "
    "(COVID-19) were temporary. VMT had largely recovered to pre-pandemic levels "
    "by 2022."
)

fig_total = go.Figure()
fig_total.add_trace(
    go.Bar(
        x=ca_vmt["year"],
        y=ca_vmt["total_vmt_billion"],
        name="Total VMT (billion miles)",
        marker_color="#1f77b4",
    )
)
fig_total.update_layout(
    xaxis_title="Year",
    yaxis_title="Billion Vehicle-Miles",
    hovermode="x unified",
    height=400,
)
st.plotly_chart(fig_total, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 2: Per-capita VMT vs. SB 375 target
# ---------------------------------------------------------------------------
st.subheader("2. Per-Capita VMT vs. SB 375 Target (Implementation Gap)")
st.markdown(
    "CARB's adopted SCS targets (illustrated here with the SCAG region's 8% "
    "reduction target by 2035) project a steady decline in per-capita VMT. "
    "In reality, actual per-capita VMT has **increased** since 2015, "
    "widening the implementation gap."
)

gap_df = compute_implementation_gap(ca_pc)

# Split historical (up to 2022) and projected
hist = gap_df[gap_df["year"] <= 2022]
proj = gap_df[gap_df["year"] > 2022]

fig_gap = go.Figure()
fig_gap.add_trace(
    go.Scatter(
        x=hist["year"],
        y=hist["actual_vmt_per_capita"],
        name="Actual per-capita VMT",
        line=dict(color="#e74c3c", width=3),
        mode="lines+markers",
    )
)
fig_gap.add_trace(
    go.Scatter(
        x=proj["year"],
        y=proj["actual_vmt_per_capita"],
        name="Projected per-capita VMT (BAU)",
        line=dict(color="#e74c3c", width=2, dash="dash"),
        mode="lines",
    )
)
fig_gap.add_trace(
    go.Scatter(
        x=gap_df["year"],
        y=gap_df["target_vmt_per_capita"],
        name="SB 375 SCS Target Trajectory",
        line=dict(color="#2ecc71", width=3),
        mode="lines+markers",
    )
)
# Shade gap area
fig_gap.add_trace(
    go.Scatter(
        x=pd.concat([gap_df["year"], gap_df["year"][::-1]]),
        y=pd.concat(
            [gap_df["actual_vmt_per_capita"], gap_df["target_vmt_per_capita"][::-1]]
        ),
        fill="toself",
        fillcolor="rgba(231,76,60,0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Implementation Gap",
        showlegend=True,
    )
)
fig_gap.add_vline(x=2008, line_dash="dot", line_color="gray", annotation_text="SB 375 enacted")
fig_gap.add_vline(x=2020, line_dash="dot", line_color="gray", annotation_text="COVID-19")
fig_gap.update_layout(
    xaxis_title="Year",
    yaxis_title="VMT per Capita (miles/year)",
    hovermode="x unified",
    height=450,
)
st.plotly_chart(fig_gap, use_container_width=True)

# Gap metrics
latest = gap_df[gap_df["year"] == 2022].iloc[0]
col1, col2, col3 = st.columns(3)
col1.metric("2022 Actual VMT/capita", f"{int(latest['actual_vmt_per_capita']):,} mi")
col2.metric("2022 SCS Target VMT/capita", f"{int(latest['target_vmt_per_capita']):,} mi")
col3.metric(
    "2022 Implementation Gap",
    f"{int(latest['gap']):,} mi/capita",
    delta=f"{latest['gap_pct']:.1f}% above target",
    delta_color="inverse",
)

# ---------------------------------------------------------------------------
# Section 3: Multi-state per-capita VMT comparison
# ---------------------------------------------------------------------------
st.subheader("3. Multi-State Per-Capita VMT Comparison (2008–2022)")
st.markdown(
    "Massachusetts shows the lowest per-capita VMT — consistent with its denser "
    "urban form and strong transit network. Colorado and Minnesota have followed "
    "declining trajectories since enacting GHG-focused transportation legislation. "
    "Virginia's VMT remains among the highest despite SMART Scale reforms."
)

year_range = st.slider(
    "Select year range",
    min_value=int(ms_vmt["year"].min()),
    max_value=int(ms_vmt["year"].max()),
    value=(2008, 2022),
)
filtered = ms_vmt[
    (ms_vmt["year"] >= year_range[0]) & (ms_vmt["year"] <= year_range[1])
]

color_map = {
    "California": "#e74c3c",
    "Colorado": "#3498db",
    "Massachusetts": "#2ecc71",
    "Minnesota": "#9b59b6",
    "Virginia": "#f39c12",
}

fig_ms = px.line(
    filtered,
    x="year",
    y="vmt_per_capita",
    color="state",
    color_discrete_map=color_map,
    markers=True,
    labels={"vmt_per_capita": "VMT per Capita (miles/year)", "year": "Year"},
)
fig_ms.update_layout(height=450, hovermode="x unified")
st.plotly_chart(fig_ms, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 4: Percent change from 2008 baseline
# ---------------------------------------------------------------------------
st.subheader("4. Percent Change in Per-Capita VMT Since 2008")
st.markdown(
    "Indexed to the SB 375 baseline year (2008) to enable apples-to-apples "
    "comparison of each state's trajectory."
)

pct_rows = []
for state, grp in ms_vmt.groupby("state"):
    grp = grp.sort_values("year").reset_index(drop=True)
    pct = pct_change_from_baseline(grp["vmt_per_capita"], grp["year"], 2008)
    for i, row in grp.iterrows():
        pct_rows.append({"year": row["year"], "state": state, "pct_change": pct.iloc[i]})

pct_df = pd.DataFrame(pct_rows)
pct_filtered = pct_df[
    (pct_df["year"] >= year_range[0]) & (pct_df["year"] <= year_range[1])
]

fig_pct = px.line(
    pct_filtered,
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
    st.dataframe(ms_vmt.pivot(index="year", columns="state", values="vmt_per_capita"))
