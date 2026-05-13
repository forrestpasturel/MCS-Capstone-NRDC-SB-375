"""
pages/5_Policy_Recommendations.py
----------------------------------
Consolidated SB 375 reform recommendations drawn from the multi-state analysis.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.data_processing import load_framework_details
from src.analysis import (
    DIMENSION_WEIGHTS,
    ghg_reduction_from_vmt,
    EMFAC_EMISSION_FACTOR_KG_PER_VMT,
)

st.set_page_config(
    page_title="Policy Recommendations", page_icon="💡", layout="wide"
)
st.title("💡 Policy Recommendations for SB 375 Reform")
st.markdown(
    "Specific reform proposals derived from the multi-state analysis, with "
    "source attribution, California implementation pathway, and estimated impact."
)

details = load_framework_details()

# ---------------------------------------------------------------------------
# Section 1: Reform priority matrix
# ---------------------------------------------------------------------------
st.subheader("1. Reform Priority Matrix")
st.markdown(
    "Six reform dimensions ranked by estimated impact on California's "
    "implementation gap, and by feasibility of near-term legislative adoption."
)

priority_data = {
    "Dimension": [
        "Binding Targets",
        "Enforcement & Accountability",
        "Equity Provisions",
        "Data & Monitoring",
        "Land-Use Integration",
        "Funding Mechanisms",
    ],
    "Estimated VMT Impact (%)": [4.5, 3.0, 1.5, 1.0, 5.0, 3.5],
    "Legislative Feasibility (1–10)": [6, 5, 8, 9, 4, 7],
    "Best State Model": [
        "Massachusetts GWSA",
        "Colorado SB 21-260",
        "Massachusetts GWSA / AB 1550",
        "Virginia SMART Scale",
        "Colorado / Virginia",
        "Colorado / Virginia",
    ],
}
priority_df = pd.DataFrame(priority_data)

fig_matrix = px.scatter(
    priority_df,
    x="Legislative Feasibility (1–10)",
    y="Estimated VMT Impact (%)",
    size="Estimated VMT Impact (%)",
    color="Dimension",
    text="Dimension",
    size_max=35,
    labels={
        "Legislative Feasibility (1–10)": "Legislative Feasibility (1 = harder, 10 = easier)",
        "Estimated VMT Impact (%)": "Estimated Per-Capita VMT Reduction (%)",
    },
)
fig_matrix.update_traces(textposition="top center")
fig_matrix.add_vline(x=6.5, line_dash="dash", line_color="gray", annotation_text="Near-term feasibility threshold")
fig_matrix.add_hline(y=3.0, line_dash="dash", line_color="gray", annotation_text="High-impact threshold")
fig_matrix.update_layout(height=480, showlegend=False)
st.plotly_chart(fig_matrix, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 2: Scenario: if all reforms adopted
# ---------------------------------------------------------------------------
st.subheader("2. Cumulative Impact Scenario")
st.markdown(
    "If California adopted reforms across all six dimensions, what is the "
    "estimated aggregate per-capita VMT reduction by 2035?"
)

total_impact = sum(priority_data["Estimated VMT Impact (%)"])
result = ghg_reduction_from_vmt(total_impact, 362.4)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Estimated VMT Reduction", f"{total_impact:.1f}%")
col2.metric("VMT Reduced (billion mi/yr)", f"{result['vmt_reduced_billion']:.1f} B")
col3.metric("Annual GHG Reduction", f"{result['ghg_reduced_mmt']:.1f} MMT CO₂e")
col4.metric(
    "Equivalent Passenger Cars Removed",
    f"{int(result['ghg_reduced_mmt'] * 1e6 / 4.6):,}",
)

# Waterfall chart of incremental impacts
fig_waterfall = go.Figure(
    go.Waterfall(
        orientation="v",
        measure=["absolute"] + ["relative"] * len(priority_data["Dimension"]) + ["total"],
        x=["2022 Baseline"] + priority_data["Dimension"] + ["2035 Reformed Target"],
        y=[9140, -411, -274, -137, -91, -457, -320, 0],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#e74c3c"}},
        decreasing={"marker": {"color": "#2ecc71"}},
        totals={"marker": {"color": "#3498db"}},
        text=[
            "9,140",
            "−411",
            "−274",
            "−137",
            "−91",
            "−457",
            "−320",
            f"≈{9140 - int(9140 * total_impact / 100):,}",
        ],
        textposition="outside",
    )
)
fig_waterfall.update_layout(
    yaxis_title="Per-Capita VMT (miles/year)",
    title="Incremental Per-Capita VMT Reduction by Reform Dimension",
    height=480,
)
st.plotly_chart(fig_waterfall, use_container_width=True)

# ---------------------------------------------------------------------------
# Section 3: Reform action table
# ---------------------------------------------------------------------------
st.subheader("3. Recommended Reform Actions")
st.markdown(
    "Each recommendation includes the source state, the California implementation "
    "pathway, and draft statutory language."
)

# Group by category
categories = details["category"].unique()
source_color = {
    "California (SB 375)": "🔴",
    "Colorado": "🔵",
    "Massachusetts": "🟢",
    "Minnesota": "🟣",
    "Virginia": "🟠",
}

# Deduplicate by category + recommended_language
recs = (
    details[details["state"] != "California (SB 375)"]
    .drop_duplicates(subset=["category", "recommended_language"])
    .copy()
)

for cat in sorted(recs["category"].unique()):
    cat_recs = recs[recs["category"] == cat]
    n = len(cat_recs)
    suffix = "s" if n > 1 else ""
    with st.expander(f"📌 {cat} ({n} recommendation{suffix})"):
        for _, row in cat_recs.iterrows():
            icon = source_color.get(row["state"], "⚪")
            st.markdown(f"**{icon} Source: {row['state']}**")
            st.markdown(f"*California Gap:* {row['california_gap']}")
            st.markdown(
                f"**Recommended SB 375 Reform Language:**\n\n> {row['recommended_language']}"
            )
            st.divider()

# ---------------------------------------------------------------------------
# Section 4: Implementation roadmap
# ---------------------------------------------------------------------------
st.subheader("4. Phased Implementation Roadmap")

roadmap = {
    "Phase": ["Phase 1 (2025–2026)", "Phase 2 (2027–2028)", "Phase 3 (2029–2032)"],
    "Legislative Priority": [
        "Data & Monitoring; Equity Provisions",
        "Binding Targets; Funding Mechanisms",
        "Enforcement & Accountability; Land-Use Integration",
    ],
    "Key Action": [
        "Mandate CBG-level VMT monitoring dashboard (Caltrans) + SCS equity screen",
        "Codify statewide transport GHG sub-target; establish VMT Reduction Trust Fund",
        "CARB automatic rulemaking trigger; limited MPO zoning pre-emption for TOD",
    ],
    "Source Model": [
        "Virginia SMART Scale; Massachusetts GWSA",
        "Massachusetts GWSA; Colorado SB 21-260",
        "Colorado SB 21-260; Virginia SMART Scale",
    ],
}

st.table(pd.DataFrame(roadmap).set_index("Phase"))

st.success(
    "**Capstone Conclusion:** The multi-state analysis demonstrates that California's "
    "SB 375 framework, while pioneering, lacks the enforcement teeth, observed-data "
    "accountability, and performance-based funding linkages present in comparable "
    "state programs.  The reforms prioritized above — particularly binding sectoral "
    "sub-targets (Massachusetts model), automatic regulatory backstops (Colorado "
    "model), and a transparent VMT-weighted project scoring system (Virginia model) — "
    "are individually feasible and collectively capable of closing the SB 375 "
    "implementation gap by 2035."
)
