"""
pages/3_State_Framework_Comparison.py
--------------------------------------
Scored assessment of SB 375 vs. Colorado, Massachusetts, Minnesota, Virginia.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from src.data_processing import load_framework_scores, load_framework_details
from src.analysis import rank_frameworks, DIMENSION_WEIGHTS

st.set_page_config(
    page_title="State Framework Comparison", page_icon="🗺️", layout="wide"
)
st.title("🗺️ State Legislative Framework Comparison")
st.markdown(
    "Expert-coded assessment of five state frameworks across six policy dimensions "
    "directly relevant to SB 375 reform."
)

scores = load_framework_scores()
details = load_framework_details()
ranked = rank_frameworks(scores)

# ---------------------------------------------------------------------------
# Dimension descriptions
# ---------------------------------------------------------------------------
DIMENSION_INFO = {
    "binding_targets": ("Binding Targets", "Are GHG/VMT targets codified in statute with numerical milestones?", 0.25),
    "enforcement_accountability": ("Enforcement & Accountability", "Are there enforceable consequences (penalties, funding cuts, automatic rulemaking) for non-compliance?", 0.20),
    "equity_provisions": ("Equity Provisions", "Are disadvantaged/EJ communities explicitly protected with mandatory benefits?", 0.15),
    "data_monitoring": ("Data & Monitoring", "Is observed (not modeled) data used for compliance? Is there public dashboard reporting?", 0.15),
    "land_use_integration": ("Land-Use Integration", "Does the framework link transportation planning to binding land-use decisions?", 0.15),
    "funding_mechanisms": ("Funding Mechanisms", "Is there a dedicated, performance-linked funding stream for VMT/GHG reduction?", 0.10),
}

# ---------------------------------------------------------------------------
# Section 1: Radar chart
# ---------------------------------------------------------------------------
st.subheader("1. Multi-Dimensional Framework Scorecard")
st.markdown(
    "Each dimension is scored 0–10. Weights reflect their relative importance "
    "for SB 375 reform (shown in parentheses). Scores are expert-coded based on "
    "statutory language, regulatory guidance, and published program evaluations."
)

dim_cols = list(DIMENSION_WEIGHTS.keys())
dim_labels = [DIMENSION_INFO[d][0] for d in dim_cols]

color_map = {
    "California (SB 375)": "#e74c3c",
    "Colorado": "#3498db",
    "Massachusetts": "#2ecc71",
    "Minnesota": "#9b59b6",
    "Virginia": "#f39c12",
}

fig_radar = go.Figure()
for _, row in scores.iterrows():
    state = row["state"]
    values = [row[d] for d in dim_cols]
    values_closed = values + [values[0]]
    labels_closed = dim_labels + [dim_labels[0]]
    fig_radar.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=labels_closed,
            fill="toself",
            name=state,
            line=dict(color=color_map.get(state, "#aaa")),
            opacity=0.7,
        )
    )
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
    showlegend=True,
    height=550,
)
st.plotly_chart(fig_radar, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 2: Composite score ranking
# ---------------------------------------------------------------------------
st.subheader("2. Composite Policy Score Ranking")
st.markdown(
    "Weighted composite score = Σ (dimension score × weight). "
    "Massachusetts leads due to its binding targets and strong enforcement; "
    "California (SB 375) trails primarily on enforcement and funding."
)

fig_bar = px.bar(
    ranked,
    x="composite_score",
    y="state",
    orientation="h",
    color="state",
    color_discrete_map=color_map,
    labels={"composite_score": "Weighted Composite Score (0–10)", "state": ""},
    text="composite_score",
)
fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig_bar.update_layout(showlegend=False, height=360, xaxis_range=[0, 10])
st.plotly_chart(fig_bar, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 3: Dimension-by-dimension heatmap
# ---------------------------------------------------------------------------
st.subheader("3. Dimension-by-Dimension Heatmap")

import pandas as pd

heat_data = scores.set_index("state")[dim_cols].rename(
    columns={d: DIMENSION_INFO[d][0] for d in dim_cols}
)
fig_heat = px.imshow(
    heat_data,
    text_auto=True,
    color_continuous_scale="RdYlGn",
    zmin=0,
    zmax=10,
    aspect="auto",
    labels=dict(color="Score (0-10)"),
)
fig_heat.update_layout(height=350)
st.plotly_chart(fig_heat, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 4: Dimension weights and descriptions
# ---------------------------------------------------------------------------
st.subheader("4. Scoring Dimensions")

cols = st.columns(3)
for i, (dim, (label, desc, weight)) in enumerate(DIMENSION_INFO.items()):
    with cols[i % 3]:
        st.metric(label=f"{label}", value=f"Weight: {int(weight*100)}%")
        st.caption(desc)

# ---------------------------------------------------------------------------
# Section 5: Detailed provisions explorer
# ---------------------------------------------------------------------------
st.subheader("5. Detailed Provisions Explorer")
st.markdown(
    "Explore specific legislative provisions from each state and the "
    "recommended SB 375 reform language."
)

selected_state = st.selectbox(
    "Select a state to explore",
    options=details["state"].unique().tolist(),
)

state_details = details[details["state"] == selected_state]

for _, row in state_details.iterrows():
    prov_text = row["provision"]
    provision_preview = prov_text if len(prov_text) <= 60 else prov_text[:60] + "..."
    with st.expander(f"📌 {row['category']}: {provision_preview}"):
        st.markdown(f"**Provision:** {row['provision']}")
        st.markdown(f"**California Gap:** {row['california_gap']}")
        st.markdown(
            f"**🔑 Recommended SB 375 Reform Language:** {row['recommended_language']}"
        )
