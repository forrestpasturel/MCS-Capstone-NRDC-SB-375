import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os

st.set_page_config(page_title="Congestion Relief Verification", page_icon="🚗", layout="wide")

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.theme import apply_chart_style
from src.theme import inject_app_style
from src.data_access.loaders import load_pems
from src.analysis.metrics import compute_congestion_metrics

inject_app_style()

st.title("🚗 Pillar 2: The Congestion Relief Verification")
st.markdown(
        """
<div class="capstone-hero">
    <h2>Induced-Demand Verification</h2>
    <p>
        Validate whether post-expansion speed gains persist or erode over time, and connect that evidence
        to enforceable mitigation and screening policies.
    </p>
</div>
""",
        unsafe_allow_html=True,
)
st.markdown("Analyzing historical sensor data to identify evidence of induced demand and speed rebound post-expansion.")

st.sidebar.header("Filter Corridors")
palette = st.sidebar.selectbox("Chart color theme", ["Bold", "Set2", "Dark2"], index=0)
palette_map = {
    "Bold": px.colors.qualitative.Bold,
    "Set2": px.colors.qualitative.Set2,
    "Dark2": px.colors.qualitative.Dark2,
}
corridor = st.sidebar.selectbox(
    "Select Corridor Segment",
    ["I-80 PM Peak", "SR-99 Commute", "I-710 Freight"],
)

st.subheader(f"Analyzing {corridor}")

try:
    corridor_map = {
        "I-80 PM Peak": "I80",
        "SR-99 Commute": "SR99",
        "I-710 Freight": "I710",
    }
    selected_prefix = corridor_map[corridor]

    df_pems = load_pems()
    df_corridor = df_pems[df_pems["segment_id"].astype(str).str.startswith(selected_prefix)].copy()
    if df_corridor.empty:
        st.warning("No observed PeMS records were found for this corridor in the current dataset. Showing statewide sample instead.")
        df_corridor = df_pems.copy()

    metrics = compute_congestion_metrics(df_corridor)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pre-Expansion Speed", f"{metrics.get('pre_expansion_mph', 0):.1f} mph")
    c2.metric("Initial Relief Speed", f"{metrics.get('initial_relief_mph', 0):.1f} mph")
    c3.metric("3-Year Stabilized Speed", f"{metrics.get('stabilized_3yr_mph', 0):.1f} mph")
    c4.metric(
        label="Speed Rebound Erosion",
        value=f"{metrics.get('speed_erosion_pct', 0):.1f}%",
        delta="Target: < 10%",
        delta_color="off",
    )
    
    if metrics.get('speed_erosion_pct', 0) > 10:
        st.error(f"**Verification Failed:** Over {metrics.get('speed_erosion_pct', 0):.1f}% of gained speeds eroded. This constitutes 'induced travel'.")
    else:
        st.success("**Verification Passed:** Congestion relief was sustained.")

    # 1) Trend chart
    agg_speeds = df_corridor.groupby('date', as_index=False)['avg_speed_mph'].mean()
    agg_speeds['date'] = pd.to_datetime(agg_speeds['date'])
    agg_speeds['rolling_speed'] = agg_speeds['avg_speed_mph'].rolling(window=30, min_periods=1).mean()

    fig = px.line(
        agg_speeds,
        x="date",
        y=["avg_speed_mph", "rolling_speed"],
        title="Average Segment Speed Pre/Post Expansion",
        labels={"value": "Speed (mph)", "date": "Date", "variable": "Metric"},
        color_discrete_sequence=palette_map[palette],
    )
    fig.update_layout(legend_title_text="Series")
    expansion_date = agg_speeds['date'].iloc[len(agg_speeds)//2]
    fig.add_shape(
        type="line",
        x0=expansion_date,
        x1=expansion_date,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color="red", dash="dash"),
    )
    fig.add_annotation(
        x=expansion_date,
        y=1.02,
        xref="x",
        yref="paper",
        text="Expansion Complete",
        showarrow=False,
        font=dict(color="red"),
    )
    fig = apply_chart_style(fig, height=500)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Line chart notes: solid line = observed average speed; smoothed line = rolling trend used for persistence checks.")

    # 2) Phase comparison bars
    phase_plot = (
        df_corridor.groupby('phase', as_index=False)['avg_speed_mph']
        .mean()
        .rename(columns={'avg_speed_mph': 'avg_speed'})
    )
    phase_order = ["pre", "post", "year_3"]
    phase_plot['phase'] = pd.Categorical(phase_plot['phase'], categories=phase_order, ordered=True)
    phase_plot = phase_plot.sort_values('phase')

    fig_phase = px.bar(
        phase_plot,
        x='phase',
        y='avg_speed',
        text_auto='.1f',
        title='Average speed by project phase',
        labels={'phase': 'Project phase', 'avg_speed': 'Average speed (mph)'},
        color='phase',
        color_discrete_sequence=palette_map[palette],
    )
    fig_phase = apply_chart_style(fig_phase, height=420)
    st.plotly_chart(fig_phase, use_container_width=True)

    erosion = metrics.get('speed_erosion_pct', 0)
    initial_gain = metrics.get('initial_relief_gain_mph', 0)
    remaining_gain = metrics.get('remaining_relief_mph', 0)
    st.markdown("<div class='section-kicker'>TREND & IMPLICATIONS</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="insight-panel">
  <h4>Congestion trend analysis</h4>
  <p>
    Initial relief gain is estimated at <b>{initial_gain:.1f} mph</b>, with <b>{remaining_gain:.1f} mph</b> remaining by year 3,
    corresponding to <b>{erosion:.1f}%</b> erosion. Higher erosion indicates a stronger induced-demand signature and supports
    tighter mitigation or screening conditions before future capacity expansions proceed.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    # 3) Storytelling panel: induced-demand interpretation + policy analogs
    st.markdown("### Policy interpretation")
    st.markdown(
        """
- **Minnesota model**: requires recurring climate reporting tied to planning updates.
- **Colorado model**: links statewide targets to plan-level compliance checks.
- **Virginia model**: uses objective scoring to de-prioritize low-benefit capacity expansions.
- **Massachusetts model**: aligns programming with enforceable emissions trajectories.

Use this verification output as the trigger point for Pillar 2 mitigation requirements.
"""
    )

except Exception as e:
    import traceback
    st.error(f"Data loading failed: {e}")
    st.text(traceback.format_exc())
