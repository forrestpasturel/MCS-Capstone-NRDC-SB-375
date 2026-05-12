import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

st.set_page_config(page_title="Policy Overview", page_icon="📜", layout="wide")

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.theme import apply_chart_style, inject_app_style
except ImportError:
    pass

if "inject_app_style" in globals():
    inject_app_style()
st.title("📜 Policy Overview: SB 1087 Guardrails")
st.markdown(
    """
<div class="capstone-hero">
  <h2>State Model Transfer Engine</h2>
  <p>
    Compare how importing peer-state policy architecture changes California's projected VMT and GHG trajectory.
    Tune implementation strength to test conservative and aggressive adoption pathways.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
California can improve outcomes by translating proven policy mechanics from
**Minnesota, Colorado, Virginia, and Massachusetts** into a California funding-and-accountability context.
Use the controls below to estimate VMT and transport-GHG reduction potential under different adoption strengths.
"""
)

st.markdown("### What each out-of-state policy does (plain English)")
pol1, pol2 = st.columns(2)
with pol1:
    st.markdown(
        """
**Minnesota (MN) — Ongoing climate accountability**  
Minnesota links transportation planning to recurring climate reporting and performance checks.

Source: [MnDOT Reducing Carbon from Transportation](https://www.dot.state.mn.us/sustainability/reducing-carbon.html)

**How California can apply it:**
- Require annual reporting on corridor VMT and emissions outcomes.
- Trigger corrective actions when performance worsens for multiple cycles.

**California-ready policy language (draft):**
> "CalSTA shall publish annual corridor performance updates and require corrective implementation plans when two consecutive reporting cycles show adverse VMT or GHG trends."
"""
    )
    st.markdown(
        """
**Colorado (CO) — Target-linked plan compliance**  
Colorado ties transportation planning to statewide GHG targets and requires plans to stay within those limits.

Sources: [Colorado SB21-260 (signed law)](https://leg.colorado.gov/sites/default/files/2021a_260_signed.pdf) · [CDOT GHG Transportation Planning Standard](https://www.codot.gov/programs/environmental/greenhouse-gas)

**How California can apply it:**
- Tie MPO and corridor investment programs to hard climate consistency tests.
- Require mitigation packages when projects increase modeled emissions.

**California-ready policy language (draft):**
> "State and regional transportation programming shall demonstrate consistency with adopted statewide emissions targets as a condition of discretionary funding eligibility."
"""
    )

with pol2:
    st.markdown(
        """
**Virginia (VA) — Objective project scoring**  
Virginia's SMART SCALE approach funds projects based on transparent, weighted scores rather than politics.

Source: [Virginia SMART SCALE](https://smartscale.org/)

**How California can apply it:**
- Expand climate-floor scoring statewide before funds are allocated.
- Prioritize projects with measurable VMT and safety benefits.

**California-ready policy language (draft):**
> "Projects seeking state funds shall receive an objective, published score across VMT, safety, equity, and emissions criteria, and projects below the climate-floor threshold shall be ineligible for award."
"""
    )
    st.markdown(
        """
**Massachusetts (MA) — Emissions-constrained programming**  
Massachusetts aligns transportation programming with enforceable emissions trajectories.

Source: [MassDOT agency portal](https://www.mass.gov/orgs/massachusetts-department-of-transportation)

**How California can apply it:**
- Set emissions guardrails for discretionary transportation dollars.
- Pause or redesign projects that move corridor emissions above policy limits.

**California-ready policy language (draft):**
> "Transportation projects that increase corridor emissions beyond adopted guardrails shall be paused pending redesign or full mitigation demonstration."
"""
    )

st.markdown("### Side-by-side policy comparison")
comparison_df = pd.DataFrame(
    [
        {
            "State model": "Minnesota",
            "What it does": "Recurring climate reporting tied to transportation planning",
            "Legal/administrative trigger": "Regular plan-performance review cycles",
            "Funding consequence": "Corrective actions when trends worsen",
            "Best California use-case": "Annual implementation-gap accountability",
        },
        {
            "State model": "Colorado",
            "What it does": "Requires plan-level consistency with GHG reduction targets",
            "Legal/administrative trigger": "SB21-260 + planning-standard compliance checks",
            "Funding consequence": "Revised project mix and mitigation when non-compliant",
            "Best California use-case": "Target-consistency gate before program adoption",
        },
        {
            "State model": "Virginia",
            "What it does": "Objective, weighted project scoring (SMART SCALE)",
            "Legal/administrative trigger": "Scoring threshold during project selection",
            "Funding consequence": "Low-scoring projects are deprioritized",
            "Best California use-case": "Statewide climate-floor eligibility scoring",
        },
        {
            "State model": "Massachusetts",
            "What it does": "Aligns project programming with emissions pathways",
            "Legal/administrative trigger": "Emissions-trajectory guardrail checks",
            "Funding consequence": "Projects can be paused/redesigned if non-aligned",
            "Best California use-case": "Emissions-constrained discretionary programming",
        },
    ]
)
st.dataframe(comparison_df, use_container_width=True)

MODEL_STATES = ["MN", "CO", "VA", "MA"]
STATE_LABELS = {
    "MN": "Minnesota model",
    "CO": "Colorado model",
    "VA": "Virginia model",
    "MA": "Massachusetts model",
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
    df_framework = pd.read_csv("data/app/state_framework_dimensions.csv")

    st.sidebar.header("Policy Transfer Scenario")
    color_theme = st.sidebar.selectbox(
        "Chart color theme",
        ["Bold", "Cool", "Warm"],
        index=0,
    )
    color_map = {
        "Bold": px.colors.qualitative.Bold,
        "Cool": px.colors.qualitative.Set2,
        "Warm": px.colors.qualitative.Pastel,
    }[color_theme]

    model_state = st.sidebar.selectbox(
        "Out-of-state policy model",
        MODEL_STATES,
        format_func=lambda s: f"{s} — {STATE_LABELS[s]}",
    )
    adoption_strength = st.sidebar.slider("California implementation strength", 0, 100, 70, 5)
    projection_end_year = st.sidebar.slider("Projection horizon", 2030, 2045, 2035)

    alpha = adoption_strength / 100.0

    ca_vmt_2024 = float(df_ca_vmt.sort_values("year").iloc[-1]["actual_vmt_per_capita"])
    ca_ghg_2024 = float(df_ca_ghg_sub.sort_values("year").iloc[-1][["light_duty_mmt", "heavy_duty_mmt", "aviation_mmt", "rail_mmt", "marine_mmt"]].sum())

    ca_vmt_annual = _annualized_change(df_vmt_state, "CA", "vmt_per_capita")
    ca_ghg_annual = _annualized_change(df_ghg_state, "CA", "ghg_per_capita_transport")
    model_vmt_annual = _annualized_change(df_vmt_state, model_state, "vmt_per_capita")
    model_ghg_annual = _annualized_change(df_ghg_state, model_state, "ghg_per_capita_transport")

    blended_vmt_annual = (1 - alpha) * ca_vmt_annual + alpha * model_vmt_annual
    blended_ghg_annual = (1 - alpha) * ca_ghg_annual + alpha * model_ghg_annual

    years = list(range(2024, projection_end_year + 1))
    projection = pd.DataFrame({"year": years})
    projection["CA_baseline_vmt"] = ca_vmt_2024 + (projection["year"] - 2024) * ca_vmt_annual
    projection["CA_policy_transfer_vmt"] = ca_vmt_2024 + (projection["year"] - 2024) * blended_vmt_annual

    ghg_per_capita_2022_ca = float(df_ghg_state[(df_ghg_state["state"] == "CA") & (df_ghg_state["year"] == 2022)]["ghg_per_capita_transport"].iloc[0])
    projection["CA_baseline_ghg_mmt"] = ca_ghg_2024 * (
        (ghg_per_capita_2022_ca + (projection["year"] - 2024) * ca_ghg_annual) / ghg_per_capita_2022_ca
    )
    projection["CA_policy_transfer_ghg_mmt"] = ca_ghg_2024 * (
        (ghg_per_capita_2022_ca + (projection["year"] - 2024) * blended_ghg_annual) / ghg_per_capita_2022_ca
    )

    final_row = projection.iloc[-1]
    vmt_avoided = float(final_row["CA_baseline_vmt"] - final_row["CA_policy_transfer_vmt"])
    ghg_avoided = float(final_row["CA_baseline_ghg_mmt"] - final_row["CA_policy_transfer_ghg_mmt"])

    m1, m2, m3 = st.columns(3)
    m1.metric("Selected model", f"{model_state} ({STATE_LABELS[model_state]})")
    m2.metric("Projected VMT/capita improvement", f"{vmt_avoided:.2f}")
    m3.metric("Projected statewide GHG avoided (MMT)", f"{ghg_avoided:.2f}")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        vmt_plot = projection.melt(
            id_vars=["year"],
            value_vars=["CA_baseline_vmt", "CA_policy_transfer_vmt"],
            var_name="scenario",
            value_name="vmt_per_capita",
        )
        fig_vmt = px.line(
            vmt_plot,
            x="year",
            y="vmt_per_capita",
            color="scenario",
            title="California VMT per Capita: Baseline vs Policy-Transfer Scenario",
            labels={"vmt_per_capita": "VMT per Capita", "year": "Year", "scenario": "Scenario"},
            color_discrete_sequence=color_map,
        )
        fig_vmt.update_traces(mode="lines+markers")
        fig_vmt.update_layout(legend_title_text="Scenario")
        if "apply_chart_style" in globals():
            fig_vmt = apply_chart_style(fig_vmt, height=430)
        st.plotly_chart(fig_vmt, use_container_width=True)

    with chart_col2:
        ghg_plot = projection.melt(
            id_vars=["year"],
            value_vars=["CA_baseline_ghg_mmt", "CA_policy_transfer_ghg_mmt"],
            var_name="scenario",
            value_name="ghg_mmt",
        )
        fig_ghg = px.line(
            ghg_plot,
            x="year",
            y="ghg_mmt",
            color="scenario",
            title="California Transport GHG: Baseline vs Policy-Transfer Scenario",
            labels={"ghg_mmt": "Transport GHG (MMT)", "year": "Year", "scenario": "Scenario"},
            color_discrete_sequence=color_map,
        )
        fig_ghg.update_traces(mode="lines+markers")
        fig_ghg.update_layout(legend_title_text="Scenario")
        if "apply_chart_style" in globals():
            fig_ghg = apply_chart_style(fig_ghg, height=430)
        st.plotly_chart(fig_ghg, use_container_width=True)

        baseline_end_vmt = float(final_row["CA_baseline_vmt"])
        policy_end_vmt = float(final_row["CA_policy_transfer_vmt"])
        baseline_end_ghg = float(final_row["CA_baseline_ghg_mmt"])
        policy_end_ghg = float(final_row["CA_policy_transfer_ghg_mmt"])

        st.markdown("<div class='section-kicker'>FIGURE INTERPRETATION</div>", unsafe_allow_html=True)
        st.markdown(
                f"""
<div class="insight-panel">
    <h4>Trend interpretation</h4>
    <p>
        By {projection_end_year}, the baseline pathway reaches <b>{baseline_end_vmt:.2f}</b> VMT/capita and
        <b>{baseline_end_ghg:.2f} MMT</b> transport GHG, while the {STATE_LABELS[model_state]} pathway reaches
        <b>{policy_end_vmt:.2f}</b> VMT/capita and <b>{policy_end_ghg:.2f} MMT</b>. This implies that stronger adoption
        shifts both mobility and emissions curves in the intended policy direction.
    </p>
</div>
""",
                unsafe_allow_html=True,
        )

    st.markdown("### Cross-state policy transfer potential")
    scenario_rows = []
    for s in MODEL_STATES:
        s_vmt_annual = _annualized_change(df_vmt_state, s, "vmt_per_capita")
        s_ghg_annual = _annualized_change(df_ghg_state, s, "ghg_per_capita_transport")
        blend_vmt = (1 - alpha) * ca_vmt_annual + alpha * s_vmt_annual
        blend_ghg = (1 - alpha) * ca_ghg_annual + alpha * s_ghg_annual

        end_vmt_baseline = ca_vmt_2024 + (projection_end_year - 2024) * ca_vmt_annual
        end_vmt_policy = ca_vmt_2024 + (projection_end_year - 2024) * blend_vmt

        end_ghg_baseline = ca_ghg_2024 * ((ghg_per_capita_2022_ca + (projection_end_year - 2024) * ca_ghg_annual) / ghg_per_capita_2022_ca)
        end_ghg_policy = ca_ghg_2024 * ((ghg_per_capita_2022_ca + (projection_end_year - 2024) * blend_ghg) / ghg_per_capita_2022_ca)

        scenario_rows.append(
            {
                "state_model": s,
                "vmt_reduction_potential": end_vmt_baseline - end_vmt_policy,
                "ghg_reduction_potential_mmt": end_ghg_baseline - end_ghg_policy,
            }
        )

    df_scenarios = pd.DataFrame(scenario_rows)
    fig_compare = go.Figure()
    fig_compare.add_trace(
        go.Bar(
            x=df_scenarios["state_model"],
            y=df_scenarios["vmt_reduction_potential"],
            name="VMT/capita improvement (lower is better)",
        )
    )
    fig_compare.add_trace(
        go.Bar(
            x=df_scenarios["state_model"],
            y=df_scenarios["ghg_reduction_potential_mmt"],
            name="GHG avoided (MMT, higher is better)",
            yaxis="y2",
        )
    )
    fig_compare.update_layout(
        title="Potential reductions if California adopts each model",
        xaxis_title="State policy model",
        yaxis_title="Modeled VMT/capita improvement",
        yaxis2=dict(title="GHG avoided (MMT)", overlaying="y", side="right"),
        barmode="group",
        legend_title_text="Metric",
    )
    if "apply_chart_style" in globals():
        fig_compare = apply_chart_style(fig_compare, height=440)
    st.plotly_chart(fig_compare, use_container_width=True)

    best_row = df_scenarios.sort_values("ghg_reduction_potential_mmt", ascending=False).iloc[0]
    st.caption(
        f"Best modeled GHG performer at current adoption strength: {best_row['state_model']} with "
        f"~{best_row['ghg_reduction_potential_mmt']:.2f} MMT avoided."
    )

    st.markdown("### Why these models matter in California")
    framework_plot = df_framework[df_framework["state"].isin(["CA", "MN", "CO", "VA", "MA"])].melt(
        id_vars=["state"], var_name="dimension", value_name="score"
    )
    fig_framework = px.line_polar(
        framework_plot,
        r="score",
        theta="dimension",
        color="state",
        line_close=True,
        title="Policy architecture comparison: California vs peer models",
        color_discrete_sequence=color_map,
    )
    if "apply_chart_style" in globals():
        fig_framework = apply_chart_style(fig_framework, height=520)
    st.plotly_chart(fig_framework, use_container_width=True)

    st.markdown("<div class='section-kicker'>POLICY IMPLICATION</div>", unsafe_allow_html=True)
    st.markdown(
        """
<div class="insight-panel">
  <h4>Implementation implication</h4>
  <p>
    The strongest outcomes come from combining target-setting with enforceable funding consequences.
    Use this page to identify which peer-state architecture should anchor California's next statutory update,
    then validate affected geographies in the Corridor Diagnostic and Policy Transfer Calculator tabs.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.info(
        f"At {adoption_strength}% implementation strength, importing the {STATE_LABELS[model_state]} into California's funding rules projects "
        f"~{vmt_avoided:.2f} lower VMT/capita and ~{ghg_avoided:.2f} MMT lower transport GHG by {projection_end_year}, relative to the current trajectory."
    )

except Exception as e:
    st.error(f"Failed to load comparative state data: {e}")
