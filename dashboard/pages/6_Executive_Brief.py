import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Executive Brief", page_icon="🧾", layout="wide")

try:
    from src.theme import apply_chart_style, inject_app_style
except ImportError:
    pass

if "inject_app_style" in globals():
    inject_app_style()

st.title("🧾 Executive Brief: What the Data Means")

st.markdown(
    """
<div class="capstone-hero">
  <h2>Plain-Language Policy Summary</h2>
  <p>
    This page translates technical model outputs into practical takeaways: where California can reduce driving demand (VMT),
    where transport emissions can drop fastest, and what out-of-state policies seem most transferable.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("### Quick guide to the peer-state models")
st.markdown(
        """
- **Minnesota:** continuous climate performance reporting tied to transportation planning updates.  
    [Policy reference](https://www.dot.state.mn.us/sustainability/reducing-carbon.html)  
    **California use:** require annual implementation-gap checks and automatic corrective plans.

- **Colorado:** transportation plans must align with statewide GHG targets.  
    [Policy references](https://www.codot.gov/programs/environmental/greenhouse-gas) · [SB21-260 signed law](https://leg.colorado.gov/sites/default/files/2021a_260_signed.pdf)  
    **California use:** require target-consistency tests before funding approval.

- **Virginia:** projects are selected through objective, weighted scoring (SMART SCALE style).  
    [Policy reference](https://smartscale.org/)  
    **California use:** formalize climate-floor scoring as a hard eligibility gate.

- **Massachusetts:** programming is constrained by enforceable emissions pathways.  
    [Policy reference](https://www.mass.gov/orgs/massachusetts-department-of-transportation)  
    **California use:** attach emissions guardrails and redesign triggers to funded projects.
"""
)

matrix = pd.DataFrame(
    {
        "State": ["Minnesota", "Colorado", "Virginia", "Massachusetts"],
        "Primary mechanism": [
            "Ongoing reporting + corrective planning",
            "Target-linked planning compliance",
            "Objective weighted scoring",
            "Emissions-constrained programming",
        ],
        "California application": [
            "Annual implementation-gap triggers",
            "Hard climate consistency checks",
            "Climate-floor project eligibility",
            "Guardrail-based funding redesign",
        ],
    }
)
st.dataframe(matrix, use_container_width=True)

MODEL_STATES = ["MN", "CO", "VA", "MA"]
MODEL_LABELS = {
    "MN": "Minnesota",
    "CO": "Colorado",
    "VA": "Virginia",
    "MA": "Massachusetts",
}


def _annualized_change(df: pd.DataFrame, state: str, value_col: str, start_year: int = 2016, end_year: int = 2022) -> float:
    subset = df[(df["state"] == state) & (df["year"].isin([start_year, end_year]))].sort_values("year")
    if len(subset) < 2:
        return 0.0
    return (subset[value_col].iloc[-1] - subset[value_col].iloc[0]) / (end_year - start_year)


try:
    df_vmt_state = pd.read_csv("data/app/state_vmt_per_capita.csv")
    df_ghg_state = pd.read_csv("data/app/state_ghg_per_capita.csv")
    df_ca_vmt = pd.read_csv("data/app/ca_vmt_targets_actual.csv")
    df_ca_ghg_sub = pd.read_csv("data/app/ca_transport_ghg_subsectors.csv")
    df_zcta = pd.read_csv("data/app/ca_zcta_spatial.csv")

    st.sidebar.header("Executive Scenario")
    selected_model = st.sidebar.selectbox(
        "Primary model to spotlight",
        MODEL_STATES,
        format_func=lambda s: f"{s} — {MODEL_LABELS[s]}",
    )
    adoption_strength = st.sidebar.slider("Implementation strength", 0, 100, 70, 5)
    horizon = st.sidebar.slider("Projection horizon", 2030, 2045, 2035)

    alpha = adoption_strength / 100.0

    # Anchors
    ca_vmt_2024 = float(df_ca_vmt.sort_values("year").iloc[-1]["actual_vmt_per_capita"])
    ca_ghg_2024 = float(df_ca_ghg_sub.sort_values("year").iloc[-1][["light_duty_mmt", "heavy_duty_mmt", "aviation_mmt", "rail_mmt", "marine_mmt"]].sum())
    ghg_pc_2022_ca = float(df_ghg_state[(df_ghg_state["state"] == "CA") & (df_ghg_state["year"] == 2022)]["ghg_per_capita_transport"].iloc[0])

    ca_vmt_annual = _annualized_change(df_vmt_state, "CA", "vmt_per_capita")
    ca_ghg_annual = _annualized_change(df_ghg_state, "CA", "ghg_per_capita_transport")

    rows = []
    for s in MODEL_STATES:
        s_vmt_annual = _annualized_change(df_vmt_state, s, "vmt_per_capita")
        s_ghg_annual = _annualized_change(df_ghg_state, s, "ghg_per_capita_transport")

        blend_vmt = (1 - alpha) * ca_vmt_annual + alpha * s_vmt_annual
        blend_ghg = (1 - alpha) * ca_ghg_annual + alpha * s_ghg_annual

        base_vmt_end = ca_vmt_2024 + (horizon - 2024) * ca_vmt_annual
        policy_vmt_end = ca_vmt_2024 + (horizon - 2024) * blend_vmt

        base_ghg_end = ca_ghg_2024 * ((ghg_pc_2022_ca + (horizon - 2024) * ca_ghg_annual) / ghg_pc_2022_ca)
        policy_ghg_end = ca_ghg_2024 * ((ghg_pc_2022_ca + (horizon - 2024) * blend_ghg) / ghg_pc_2022_ca)

        rows.append(
            {
                "state_model": s,
                "state_name": MODEL_LABELS[s],
                "vmt_improvement": base_vmt_end - policy_vmt_end,
                "ghg_avoided_mmt": base_ghg_end - policy_ghg_end,
            }
        )

    df_compare = pd.DataFrame(rows).sort_values("ghg_avoided_mmt", ascending=False)

    # Selected model metrics
    sel = df_compare[df_compare["state_model"] == selected_model].iloc[0]
    hot = (
        df_zcta.groupby("region", as_index=False)
        .agg(avg_vmt_gap=("vmt_gap_index", "mean"), avg_ghg_pc=("ghg_per_capita", "mean"), zcta_count=("zcta", "count"))
    )
    hot["hotspot_index"] = 0.6 * hot["avg_vmt_gap"] + 0.4 * hot["avg_ghg_pc"]
    top_region = hot.sort_values("hotspot_index", ascending=False).iloc[0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spotlight model", MODEL_LABELS[selected_model])
    m2.metric("Modeled VMT improvement", f"{sel['vmt_improvement']:.2f} per-capita units")
    m3.metric("Modeled GHG avoided", f"{sel['ghg_avoided_mmt']:.2f} MMT")
    m4.metric("Top intervention region", top_region["region"])

    st.markdown("<div class='section-kicker'>IN PLAIN ENGLISH</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="insight-panel">
  <h4>What this means for non-technical audiences</h4>
  <p>
    If California applies <b>{MODEL_LABELS[selected_model]}</b>-style rules at <b>{adoption_strength}% strength</b>,
    the model suggests lower driving growth and lower transportation emissions by <b>{horizon}</b> compared with business-as-usual.
    The biggest near-term gains are likely where VMT gaps and emissions burdens overlap — currently led by <b>{top_region['region']}</b>.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        fig_compare = px.bar(
            df_compare,
            x="state_name",
            y="vmt_improvement",
            color="state_name",
            title="Estimated VMT improvement if California adopts each model",
            labels={
                "state_name": "Out-of-state model",
                "vmt_improvement": "Modeled VMT improvement (per-capita units)",
            },
            text_auto=".2f",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        if "apply_chart_style" in globals():
            fig_compare = apply_chart_style(fig_compare, height=430)
        st.plotly_chart(fig_compare, use_container_width=True)
        st.caption("Higher bars mean stronger modeled reduction in per-capita VMT growth.")

    with c2:
        fig_ghg = px.bar(
            df_compare,
            x="state_name",
            y="ghg_avoided_mmt",
            color="ghg_avoided_mmt",
            color_continuous_scale="Viridis",
            title="Estimated statewide transport GHG avoided",
            labels={
                "state_name": "Out-of-state model",
                "ghg_avoided_mmt": "GHG avoided (MMT)",
            },
            text_auto=".2f",
        )
        if "apply_chart_style" in globals():
            fig_ghg = apply_chart_style(fig_ghg, height=430)
        st.plotly_chart(fig_ghg, use_container_width=True)
        st.caption("Higher bars mean larger modeled climate benefit.")

    fig_hot = px.bar(
        hot.sort_values("hotspot_index", ascending=False),
        x="region",
        y="hotspot_index",
        color="hotspot_index",
        color_continuous_scale="Turbo",
        title="Where policy transfer may have strongest near-term effect",
        labels={
            "region": "California region",
            "hotspot_index": "Composite need/opportunity index",
        },
        hover_data={"avg_vmt_gap": ":.2f", "avg_ghg_pc": ":.2f", "zcta_count": True},
    )
    if "apply_chart_style" in globals():
        fig_hot = apply_chart_style(fig_hot, height=430)
    st.plotly_chart(fig_hot, use_container_width=True)

    st.markdown("### Trends, analysis, and implications")
    st.markdown(
        """
- **Trend:** California's planning-to-delivery gap remains visible where VMT growth and burden overlap.
- **Analysis:** The state-model comparison shows no single silver bullet; strongest outcomes come from enforceability + consistent monitoring.
- **Implication:** Early implementation should focus on top hotspot regions while aligning eligibility rules with climate-floor thresholds.
- **Action:** Use the Policy Transfer Calculator tab to export region-ready talking points and implementation priorities.
"""
    )

    with st.expander("How to read this page"):
        st.markdown(
            """
1. Pick a model and implementation strength in the sidebar.
2. Read the KPI cards for top-line potential.
3. Use the model comparison charts to compare options.
4. Use the regional hotspot chart to identify where to start.
5. Move to the Policy Transfer Calculator for exports.
"""
        )

except Exception as e:
    st.error(f"Failed to build executive brief: {e}")
