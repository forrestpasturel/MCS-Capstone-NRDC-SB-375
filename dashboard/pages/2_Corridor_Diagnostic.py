import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sys, os

st.set_page_config(page_title="Corridor Diagnostic", page_icon="🗺️", layout="wide")

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from src.theme import apply_chart_style, inject_app_style
except ImportError:
    pass

if "inject_app_style" in globals():
    inject_app_style()

st.title("🗺️ The Diagnostic: Identifying the Failure")
st.markdown(
    """
<div class="capstone-hero">
  <h2>Spatial Opportunity Screening</h2>
  <p>
    Explore which California geographies show the strongest modeled VMT and GHG reduction potential
    under transferable policy strategies from peer states.
  </p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("""
Visualizing the implementation gap via actual ZCTA (Zip Code Tabulation Area) spatial layers. 
This dashboard cross-references regions with high **pollution_burden** against areas with large **VMT Gap Indexes** 
(representing cases where state investments fail to meet per-capita VMT reduction targets).
""")

MODEL_FACTORS = {
    "Minnesota (MN)": {"vmt": 0.22, "ghg": 0.18},
    "Colorado (CO)": {"vmt": 0.16, "ghg": 0.20},
    "Virginia (VA)": {"vmt": 0.12, "ghg": 0.14},
    "Massachusetts (MA)": {"vmt": 0.19, "ghg": 0.21},
}

# Load spatial data
try:
    df_spatial = pd.read_csv("data/app/ca_zcta_spatial.csv")
    regions = df_spatial['region'].unique().tolist()
    
    st.sidebar.header("Filter Diagnostic")
    selected_region = st.sidebar.selectbox("Select California Region", regions)
    selected_model = st.sidebar.selectbox("Apply out-of-state policy model", list(MODEL_FACTORS.keys()))
    adoption_strength = st.sidebar.slider("California implementation strength", 0, 100, 70, 5)
    color_scale_name = st.sidebar.selectbox(
        "Map color scale",
        ["RdYlGn_r", "Turbo", "Viridis", "Plasma"],
        index=0,
    )
    layer_view = st.sidebar.radio(
        "Spatial layer",
        [
            "Current VMT Gap",
            "VMT Reduction Potential",
            "GHG Reduction Potential",
            "Combined Opportunity Index",
        ],
    )
    st.sidebar.info("Integrating ZCTA spatial coordinates with Capstone `vmt_gap_index` and `pollution_burden`.")
    
    st.subheader(f"Per-Capita VMT Growth vs. Adopted SCS Targets: {selected_region}")
    
    # Filter dataset
    df_filtered = df_spatial[df_spatial['region'] == selected_region].copy()
    factor = MODEL_FACTORS[selected_model]
    alpha = adoption_strength / 100.0

    # Higher positive value = larger estimated reduction if model is adopted.
    df_filtered["vmt_reduction_potential"] = np.clip(df_filtered["vmt_gap_index"], 0, None) * factor["vmt"] * alpha
    df_filtered["ghg_reduction_potential"] = np.clip(df_filtered["ghg_per_capita"], 0, None) * factor["ghg"] * alpha
    df_filtered["combined_opportunity_index"] = (
        0.55 * df_filtered["vmt_reduction_potential"]
        + 0.45 * df_filtered["ghg_reduction_potential"]
    )

    color_metric = {
        "Current VMT Gap": "vmt_gap_index",
        "VMT Reduction Potential": "vmt_reduction_potential",
        "GHG Reduction Potential": "ghg_reduction_potential",
        "Combined Opportunity Index": "combined_opportunity_index",
    }[layer_view]
    
    # Render map
    fig = px.scatter_map(
        df_filtered, 
        lat="lat", lon="lon", 
        color=color_metric,
        size="pollution_burden",
        hover_name="zcta", 
        hover_data=[
            "pollution_burden",
            "vmt_gap_index",
            "ghg_per_capita",
            "traffic_density",
            "vmt_reduction_potential",
            "ghg_reduction_potential",
            "combined_opportunity_index",
        ],
        size_max=20, zoom=7,
        title=f"{layer_view} Overlay + Pollution Burden ({selected_region})",
        color_continuous_scale=color_scale_name,
        labels={
            "vmt_gap_index": "VMT Gap Index",
            "vmt_reduction_potential": "Modeled VMT Reduction Potential",
            "ghg_reduction_potential": "Modeled GHG Reduction Potential",
            "combined_opportunity_index": "Combined Opportunity Index",
            "pollution_burden": "Pollution Burden",
            "traffic_density": "Traffic Density",
            "ghg_per_capita": "GHG per Capita",
        },
    )
    
    if 'apply_chart_style' in globals():
        fig = apply_chart_style(fig, height=600)
    else:
        fig.update_layout(height=600)
        
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Map notes: marker size reflects pollution burden; color reflects selected policy layer. "
        "Switch the layer and model to observe how geographic priority changes under different policy assumptions."
    )
    
    # Metrics
    vmt_fail = len(df_filtered[df_filtered['vmt_gap_index'] > 0])
    total_zcta = len(df_filtered)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total ZCTAs Analyzed", f"{total_zcta}")
    col2.metric("Failed Reduction Targets", f"{vmt_fail}")
    fail_pct = (vmt_fail / total_zcta) * 100 if total_zcta > 0 else 0
    col3.metric("Failure Rate", f"{fail_pct:.1f}%")

    top5 = df_filtered.sort_values("combined_opportunity_index", ascending=False).head(5)
    est_vmt = top5["vmt_reduction_potential"].sum()
    est_ghg = top5["ghg_reduction_potential"].sum()
    st.info(
        f"Top 5 opportunity ZCTAs in {selected_region} under the {selected_model} at {adoption_strength}% implementation strength "
        f"show modeled aggregate potential of ~{est_vmt:.2f} VMT-index reduction units and ~{est_ghg:.2f} GHG-per-capita reduction units."
    )

    highest = top5.iloc[0]
    st.markdown("<div class='section-kicker'>TREND & IMPLICATIONS</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="insight-panel">
  <h4>Spatial trend interpretation</h4>
  <p>
    In <b>{selected_region}</b>, the leading priority geography is ZCTA <b>{highest['zcta']}</b> with a combined opportunity index of
    <b>{highest['combined_opportunity_index']:.2f}</b>. This suggests that pairing high-burden communities with stronger
    policy-transfer enforcement can deliver the largest first-wave reductions.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("#### Priority geography: highest modeled reduction potential")
    st.dataframe(
        top5[[
            "zcta",
            "pollution_burden",
            "vmt_gap_index",
            "ghg_per_capita",
            "vmt_reduction_potential",
            "ghg_reduction_potential",
            "combined_opportunity_index",
        ]],
        use_container_width=True,
    )
    
    if fail_pct > 50:
        st.error(f"**Pillar 1 Check:** {fail_pct:.1f}% of reporting block groups in {selected_region} signify rising per-capita VMT. **Triggering Corrective Action Moratorium.**")
    elif fail_pct > 25:
        st.warning(f"**Pillar 1 Check:** {fail_pct:.1f}% failure rate puts {selected_region} at high risk of triggering mitigation actions.")
    else:
        st.success(f"**Pillar 1 Check:** {selected_region} is substantially compliant.")

    with st.expander("Explore ZCTA Spatial Dataset"):
        st.dataframe(df_filtered)
        
except Exception as e:
    import traceback
    st.error(f"Error loading spatial datasets: {e}")
    st.text(traceback.format_exc())
