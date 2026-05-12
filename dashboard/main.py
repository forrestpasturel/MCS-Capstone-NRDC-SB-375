import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SB 1087 Dashboard", layout="wide", initial_sidebar_state="expanded")

try:
    from src.theme import apply_chart_style, inject_app_style
except ImportError:
    pass

if "inject_app_style" in globals():
    inject_app_style()

st.title("Strengthening SB 375: Guardrails for Performance-Based Funding")
st.markdown(
    """
<div class="capstone-hero">
  <h2>SB 1087 Interactive Policy Intelligence Hub</h2>
  <p>
    This capstone dashboard integrates diagnostics, congestion verification, climate-floor screening,
    and policy-transfer modeling to support evidence-based transportation funding reform in California.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
Welcome to the SB 1087 decision-support dashboard. This workspace links planning outcomes,
corridor-level diagnostics, congestion verification, and climate-floor scoring into one policy narrative.

Use this homepage as your executive briefing, then move through the tabs for deeper evidence.
"""
)

st.markdown("### Executive summary")
left, right = st.columns([2, 1])

with left:
    st.markdown(
        """
- **Problem:** California planning targets exist, but implementation still allows high-VMT investments.
- **Evidence:** Some corridors show post-expansion speed erosion, consistent with induced demand.
- **Policy transfer opportunity:** Minnesota, Colorado, Virginia, and Massachusetts provide enforceable design patterns.
- **Use case:** Quantify where California can gain the largest VMT and GHG reductions under transfer scenarios.
"""
    )

with right:
    st.info("Navigation order: **1 → 2 → 3 → 4 → 5** for full policy storyline.")

st.markdown("### Quick navigation")
nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.page_link("pages/1_Policy_Overview.py", label="Policy Overview", icon="📜")
    st.page_link("pages/2_Corridor_Diagnostic.py", label="Corridor Diagnostic", icon="🗺️")
with nav2:
    st.page_link("pages/3_Congestion_Relief.py", label="Congestion Relief", icon="🚗")
    st.page_link("pages/4_Climate_Floor_Scoring.py", label="Climate Floor", icon="⚖️")
with nav3:
    st.page_link("pages/5_Policy_Transfer_Calculator.py", label="Policy Transfer Calculator", icon="🧮")
    st.page_link("pages/6_Executive_Brief.py", label="Executive Brief", icon="🧾")

info1, info2, info3 = st.columns(3)
with info1:
    st.markdown(
        """
<div class="capstone-card">
  <div class="capstone-card-title">Policy Problem</div>
  <p class="capstone-card-body">Investment choices are not consistently constrained by VMT and GHG outcomes.</p>
</div>
""",
        unsafe_allow_html=True,
    )
with info2:
    st.markdown(
        """
<div class="capstone-card">
  <div class="capstone-card-title">Policy Mechanism</div>
  <p class="capstone-card-body">Corrective-action triggers, mitigation banking, and climate-floor scoring improve accountability.</p>
</div>
""",
        unsafe_allow_html=True,
    )
with info3:
    st.markdown(
        """
<div class="capstone-card">
  <div class="capstone-card-title">Decision Utility</div>
  <p class="capstone-card-body">Scenario comparisons reveal where out-of-state models can deliver maximum California benefit.</p>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("### Live indicators")
try:
    df_ca_vmt = pd.read_csv("data/app/ca_vmt_targets_actual.csv")
    df_ghg = pd.read_csv("data/app/ca_transport_ghg_subsectors.csv")
    df_zcta = pd.read_csv("data/app/ca_zcta_spatial.csv")

    latest_vmt = df_ca_vmt.sort_values("year").iloc[-1]
    target_gap = float(latest_vmt["actual_vmt_index"] - latest_vmt["target_vmt_index"])
    latest_ghg_total = float(
        df_ghg.sort_values("year").iloc[-1][["light_duty_mmt", "heavy_duty_mmt", "aviation_mmt", "rail_mmt", "marine_mmt"]].sum()
    )
    high_gap_share = float((df_zcta["vmt_gap_index"] > 0).mean() * 100)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest actual VMT index", f"{latest_vmt['actual_vmt_index']:.1f}")
    c2.metric("VMT index gap vs target", f"{target_gap:.1f}")
    c3.metric("Latest transport GHG (MMT)", f"{latest_ghg_total:.1f}")
    c4.metric("ZCTAs above VMT gap threshold", f"{high_gap_share:.1f}%")

    st.sidebar.header("Main Page Visual Controls")
    palette_name = st.sidebar.selectbox("Main page chart theme", ["Bold", "Set2", "Safe"], index=0)
    palette = {
        "Bold": px.colors.qualitative.Bold,
        "Set2": px.colors.qualitative.Set2,
        "Safe": px.colors.qualitative.Safe,
    }[palette_name]

    st.markdown("### Dynamic visuals")
    vis1, vis2 = st.columns(2)

    with vis1:
        vmt_long = df_ca_vmt.melt(
            id_vars=["year"],
            value_vars=["actual_vmt_index", "target_vmt_index"],
            var_name="series",
            value_name="vmt_index",
        )
        fig_vmt = px.line(
            vmt_long,
            x="year",
            y="vmt_index",
            color="series",
            markers=True,
            color_discrete_sequence=palette,
            title="California VMT Index: Actual vs Target Trajectory",
            labels={
                "year": "Year",
                "vmt_index": "VMT Index (2008 = 100)",
                "series": "Series",
            },
        )
        fig_vmt.update_layout(legend_title_text="Series")
        if "apply_chart_style" in globals():
            fig_vmt = apply_chart_style(fig_vmt, height=420)
        st.plotly_chart(fig_vmt, use_container_width=True)

    with vis2:
        ghg_long = df_ghg.melt(
            id_vars=["year"],
            value_vars=["light_duty_mmt", "heavy_duty_mmt", "aviation_mmt", "rail_mmt", "marine_mmt"],
            var_name="subsector",
            value_name="ghg_mmt",
        )
        fig_ghg = px.area(
            ghg_long,
            x="year",
            y="ghg_mmt",
            color="subsector",
            color_discrete_sequence=palette,
            title="California Transport GHG Composition by Subsector",
            labels={
                "year": "Year",
                "ghg_mmt": "Emissions (MMT)",
                "subsector": "Subsector",
            },
        )
        fig_ghg.update_layout(legend_title_text="Subsector")
        if "apply_chart_style" in globals():
            fig_ghg = apply_chart_style(fig_ghg, height=420)
        st.plotly_chart(fig_ghg, use_container_width=True)

    hotspot = (
        df_zcta.groupby("region", as_index=False)
        .agg(
            zcta_count=("zcta", "count"),
            avg_vmt_gap=("vmt_gap_index", "mean"),
            avg_ghg_pc=("ghg_per_capita", "mean"),
        )
        .sort_values("avg_vmt_gap", ascending=False)
    )
    hotspot["hotspot_index"] = 0.6 * hotspot["avg_vmt_gap"] + 0.4 * hotspot["avg_ghg_pc"]

    fig_hotspot = px.bar(
        hotspot,
        x="region",
        y="hotspot_index",
        color="hotspot_index",
        color_continuous_scale="Turbo",
        title="Regional Hotspot Index (VMT Gap + GHG Intensity)",
        labels={
            "region": "California Region",
            "hotspot_index": "Composite Hotspot Index",
        },
        hover_data={
            "zcta_count": True,
            "avg_vmt_gap": ":.2f",
            "avg_ghg_pc": ":.2f",
            "hotspot_index": ":.2f",
        },
    )
    if "apply_chart_style" in globals():
        fig_hotspot = apply_chart_style(fig_hotspot, height=440)
    st.plotly_chart(fig_hotspot, use_container_width=True)

    # Trend + implication narrative
    vmt_series = df_ca_vmt.sort_values("year")
    recent_vmt_delta = float(vmt_series.iloc[-1]["actual_vmt_per_capita"] - vmt_series.iloc[0]["actual_vmt_per_capita"])
    ghg_recent = df_ghg.sort_values("year")
    ghg_total = ghg_recent[["light_duty_mmt", "heavy_duty_mmt", "aviation_mmt", "rail_mmt", "marine_mmt"]].sum(axis=1)
    ghg_delta = float(ghg_total.iloc[-1] - ghg_total.iloc[0])
    top_hotspot = hotspot.sort_values("hotspot_index", ascending=False).iloc[0]

    st.markdown("<div class='section-kicker'>TREND & IMPLICATIONS</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="insight-panel">
  <h4>What the current evidence suggests</h4>
  <p>
    California's observed per-capita VMT changed by <b>{recent_vmt_delta:+.2f}</b> over the available period,
    while modeled transport GHG totals changed by <b>{ghg_delta:+.2f} MMT</b>. The highest composite hotspot is
    currently <b>{top_hotspot['region']}</b>, indicating where integrated VMT-gap and GHG-focused interventions are
    likely to generate the strongest marginal policy return.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )
except Exception as e:
    st.warning(f"Could not compute live indicators: {e}")

st.markdown("### Dashboard structure")
st.markdown(
    """
1. **Policy Overview** — state-to-state transfer modeling, VMT/GHG scenario deltas, framework comparison.
2. **Corridor Diagnostic** — spatial opportunity mapping (ZCTA), including transfer-based reduction potential layers.
3. **Congestion Relief Verification** — pre/post/year-3 speed dynamics and induced-demand verification.
4. **Climate Floor Scoring** — project-level screening logic with weighted policy criteria.
5. **Policy Transfer Calculator** — downloadable scenario tables and one-click briefing export.
"""
)

with st.expander("Methodology and interpretation notes"):
    st.markdown(
        """
- **Live indicators** are sourced from app-level datasets in [data/app](data/app).
- **Hotspot Index** combines regional VMT gap and GHG intensity as: $0.6 \cdot \text{VMT Gap} + 0.4 \cdot \text{GHG per Capita}$.
- **Scenario pages** operationalize policy-transfer assumptions from Minnesota, Colorado, Virginia, and Massachusetts.
- Use this page as briefing context; use Pages 2–5 for detailed policy diagnostics and downloadable outputs.
"""
    )

with st.expander("Usability tips"):
    st.markdown(
        """
- Use the sidebar controls to change model, color theme, and projection horizon.
- Read the **TREND & IMPLICATIONS** panel under each figure for plain-language interpretation.
- Use the **Policy Transfer Calculator** tab to export brief-ready CSV and markdown outputs.
- Use **Executive Brief** when presenting to non-technical audiences.
"""
    )

st.caption("Tip: If charts seem stale, refresh the browser tab after switching scenarios.")
