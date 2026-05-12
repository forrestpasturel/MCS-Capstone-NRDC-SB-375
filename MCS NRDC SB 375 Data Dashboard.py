import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

st.set_page_config(page_title="Climate Floor Scoring", page_icon="⚖️", layout="wide")

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.theme import apply_chart_style, inject_app_style
    from src.data_access.loaders import load_emfac_results
    from src.analysis.metrics import compute_climate_floor_score
except ImportError:
    pass

if "inject_app_style" in globals():
    inject_app_style()

st.title("⚖️ Pillar 3: The Climate Floor Scoring System")
st.markdown(
    """
<div class="capstone-hero">
  <h2>Objective Funding Eligibility Screen</h2>
  <p>
    Simulate project scoring outcomes under weighted VMT, safety, and emissions criteria
    to determine whether proposals pass California's modeled climate floor.
  </p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("Simulating a SMART SCALE-style project screening mechanism, mandating baseline climate utility logic.")

scenario = st.sidebar.radio("Active Scenario", ["EMFAC Baseline (Scenario A)", "Aggressive Transit (Scenario B)"])
bar_palette = st.sidebar.selectbox("Bar color theme", ["Set2", "Bold", "Pastel"], index=0)
bar_palette_map = {
    "Set2": px.colors.qualitative.Set2,
    "Bold": px.colors.qualitative.Bold,
    "Pastel": px.colors.qualitative.Pastel,
}

st.subheader(f"Evaluation: {scenario}")

try:
    scenario_id = "scenario_a" if "Scenario A" in scenario else "scenario_b"
    df_emfac = load_emfac_results(scenario_id)
    
    # Map the scenario timeline dataframe into project stats expected by the function
    start_vmt = df_emfac['vmt_index'].iloc[0]
    end_vmt = df_emfac['vmt_index'].iloc[-1]
    
    start_ghg = df_emfac['ghg_tons'].iloc[0]
    end_ghg = df_emfac['ghg_tons'].iloc[-1]
    
    project_stats = {
        'forecasted_vmt_delta_m': end_vmt - start_vmt,
        'safety_incidents': 1 if "Scenario B" in scenario else 5,
        'pm25_delta_tons': (end_ghg - start_ghg) / 1000.0
    }
    
    summary = compute_climate_floor_score(project_stats)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Score", f"{summary.get('total_score', 0):.1f}")
    col2.metric("VMT Reduction Weight", f"{summary.get('vmt_delta', 0):.2f}")
    col3.metric("Safety Indicator", f"{summary.get('safety_incidents', 0)}")
    col4.metric("Emissions Avoided", f"{-summary.get('pm25_delta_tons', 0):.2f}")

    if summary.get('total_score', 0) > 50:
         st.success(f"**Project Approved:** Score {summary.get('total_score', 0):.1f} meets minimum viability threshold.")
    else:
         st.error(f"**Project Rejected:** Score {summary.get('total_score', 0):.1f} violates Climate Floor mandates.")
         
    # Build a more rigorous Plotly bar chart
    score_df = pd.DataFrame({
        "Component": ["VMT Weight (40%)", "GHG Weight (30%)", "Safety Weight (30%)"],
        "Score": [summary.get("vmt_score", 0), summary.get("aq_score", 0), summary.get("safety_score", 0)]
    })
    
    fig = px.bar(
        score_df, 
        x="Component", 
        y="Score", 
        color="Component",
        title="Score Breakdown by Policy Mandate",
        text_auto=".2f",
        color_discrete_sequence=bar_palette_map[bar_palette],
        labels={"Component": "Policy Component", "Score": "Score Contribution"},
    )
    fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    fig = apply_chart_style(fig, height=450)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bar chart notes: positive component scores improve eligibility; weaker/negative components lower total score.")

    vmt_change = end_vmt - start_vmt
    ghg_change = end_ghg - start_ghg
    st.markdown("<div class='section-kicker'>TREND & IMPLICATIONS</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="insight-panel">
  <h4>Scenario interpretation</h4>
  <p>
    This scenario changes VMT index by <b>{vmt_change:+.2f}</b> and total GHG by <b>{ghg_change:+.1f} tons</b>
    over the modeled horizon. The climate-floor result (<b>{summary.get('total_score', 0):.1f}</b>) indicates
    whether the project profile should be considered fundable under performance-based eligibility rules.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

except Exception as e:
    import traceback
    st.error(f"Error loading EMFAC datasets: {e}")
    st.text(traceback.format_exc())
