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

# ---------------------------------------------------------------------------
# Section 5: Policy Lever Simulator
# ---------------------------------------------------------------------------
import numpy as np

st.divider()
st.subheader("5. 🎛️ Policy Lever Simulator: Design Your Own Reform Package")
st.markdown(
    "Use the sliders below to explore how different transportation and land use "
    "policies could affect how much Californians drive — and how much carbon "
    "pollution results. Pull the levers, mix and match, and see what it would "
    "take to hit California's 2045 climate targets."
)

# ── Constants ─────────────────────────────────────────────────────────────
BASELINE_VMT = 24.3          # miles/day/person, 2025 baseline
BAU_2045 = 24.6              # slight increase under BAU
CA_POP = 39_000_000
EMFAC_FACTOR = 0.338         # kg CO2e per VMT
TARGET_2045 = 17.2           # 2045 carbon-neutrality target (mi/day)

# ── Lever definitions ─────────────────────────────────────────────────────
LEVERS = {
    "tod": {
        "plain": "Build more homes near transit stops",
        "tech": "Compact Development / TOD Intensity",
        "min": -15, "max": 0, "default": 0, "step": 1,
        "tooltip": "Concentrating housing and jobs near transit stations reduces how much people need to drive daily.",
        "source": "Handy & Boarnet 2014; PPIC 2021",
        "color": "#2ecc71",
        "chart_label": "Transit-Oriented Development",
    },
    "pricing": {
        "plain": "Price highways to reduce peak-hour traffic",
        "tech": "Pricing / Travel Demand Management (TDM)",
        "min": -12, "max": 0, "default": 0, "step": 1,
        "tooltip": "Charging drivers during peak hours shifts some trips to transit, carpools, or off-peak travel.",
        "source": "CARB SB 743 guidance; Litman 2022",
        "color": "#3498db",
        "chart_label": "Toll Pricing & TDM",
    },
    "land_use": {
        "plain": "Allow denser, mixed-use neighborhoods",
        "tech": "Zoning Reform / Land Use Intensification",
        "min": -10, "max": 0, "default": 0, "step": 1,
        "tooltip": "Allowing shops, offices, and homes to mix in the same neighborhood means shorter trips and less driving.",
        "source": "Cervero & Kockelman 1997; California HCD studies",
        "color": "#9b59b6",
        "chart_label": "Land Use Reform",
    },
    "transit": {
        "plain": "Expand and improve public transit",
        "tech": "Transit Network Expansion / Frequency Improvements",
        "min": -8, "max": 0, "default": 0, "step": 1,
        "tooltip": "More frequent, reliable transit gives people a real alternative to driving, especially for commute trips.",
        "source": "NCST 2022; TransForm California",
        "color": "#1abc9c",
        "chart_label": "Public Transit Expansion",
    },
    "highway": {
        "plain": "Build more highway lanes",
        "tech": "Highway Capacity Expansion (Induced Demand)",
        "min": 0, "max": 15, "default": 0, "step": 1,
        "tooltip": "Adding highway lanes generates new car trips over time — a well-documented phenomenon called induced demand. More lanes = more driving.",
        "source": "Duranton & Turner 2011; Caltrans NCST Induced Travel Calculator",
        "color": "#e74c3c",
        "chart_label": "Highway Expansion",
    },
    "active": {
        "plain": "Build protected bike lanes and safe sidewalks",
        "tech": "Active Transportation / Non-Motorized Infrastructure",
        "min": -5, "max": 0, "default": 0, "step": 1,
        "tooltip": "Protected bike lanes and connected pedestrian networks shift short trips away from cars.",
        "source": "Buehler & Pucher 2012; Caltrans ATP program evaluations",
        "color": "#f39c12",
        "chart_label": "Active Transportation",
    },
}

# ── Session state initialization ──────────────────────────────────────────
for key in LEVERS:
    if f"lever_{key}" not in st.session_state:
        st.session_state[f"lever_{key}"] = LEVERS[key]["default"]

# ── Scenario presets ──────────────────────────────────────────────────────
PRESETS = {
    "Status Quo": {"tod": 0, "pricing": 0, "land_use": 0, "transit": 0, "highway": 5, "active": 0},
    "Scenario 1: CAP Moratorium": {"tod": -3, "pricing": 0, "land_use": -2, "transit": -2, "highway": 0, "active": 0},
    "Scenario 2: VMT Neutral Rule": {"tod": -6, "pricing": -5, "land_use": -4, "transit": -4, "highway": 0, "active": -3},
    "Scenario 3: Performance Floor": {"tod": -12, "pricing": -10, "land_use": -8, "transit": -7, "highway": 0, "active": -4},
}

# ── Preset and reset buttons ─────────────────────────────────────────────
st.markdown("**Scenario Presets** — click to auto-populate the sliders:")
preset_cols = st.columns(len(PRESETS) + 1)
for i, (preset_name, preset_vals) in enumerate(PRESETS.items()):
    if preset_cols[i].button(preset_name, key=f"preset_{i}", use_container_width=True):
        for key, val in preset_vals.items():
            st.session_state[f"lever_{key}"] = val
        st.rerun()

if preset_cols[-1].button("🔄 Reset All", key="reset_all", use_container_width=True):
    for key in LEVERS:
        st.session_state[f"lever_{key}"] = LEVERS[key]["default"]
    st.rerun()

st.markdown("---")

# ── Slider UI ────────────────────────────────────────────────────────────
lever_keys_col1 = ["tod", "pricing", "land_use"]
lever_keys_col2 = ["transit", "highway", "active"]

col_left, col_right = st.columns(2)

def render_lever(container, key):
    """Render a single lever slider inside the given container."""
    info = LEVERS[key]
    is_highway = (key == "highway")

    if is_highway:
        container.markdown(
            f"**⚠️ {info['plain']}**  \n"
            f"<span style='font-size:0.82em; color:#999;'>{info['tech']}</span>  \n"
            f"<span style='font-size:0.78em; color:#e74c3c;'>⚠️ This lever <b>increases</b> VMT (induced demand effect)</span>",
            unsafe_allow_html=True,
        )
    else:
        container.markdown(
            f"**{info['plain']}**  \n"
            f"<span style='font-size:0.82em; color:#999;'>{info['tech']}</span>",
            unsafe_allow_html=True,
        )

    val = container.slider(
        label=info["tooltip"],
        min_value=info["min"],
        max_value=info["max"],
        value=st.session_state[f"lever_{key}"],
        step=info["step"],
        format="%+d%%",
        key=f"lever_{key}",
        label_visibility="collapsed",
        help=info["tooltip"],
    )
    return val


with col_left:
    st.markdown("##### 🟢 VMT-Reducing Policies")
    for k in lever_keys_col1:
        render_lever(col_left, k)

with col_right:
    st.markdown("##### 🔴 Capacity & Mode Shift")
    for k in lever_keys_col2:
        render_lever(col_right, k)

# ── Read current slider values ────────────────────────────────────────────
lever_vals = {k: st.session_state[f"lever_{k}"] for k in LEVERS}
combined_pct = sum(lever_vals.values())  # net % VMT change

# ── Summary metrics ──────────────────────────────────────────────────────
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Net VMT Impact", f"{combined_pct:+d}%")
m2.metric("2045 Daily VMT/person",
          f"{BASELINE_VMT * (1 + combined_pct / 100):.1f} mi")
m3.metric("2045 Target", f"{TARGET_2045} mi/day")

gap_remaining = BASELINE_VMT * (1 + combined_pct / 100) - TARGET_2045
if gap_remaining <= 0:
    m4.metric("Target Gap", "✅ Met!", delta="Target achieved", delta_color="normal")
else:
    m4.metric("Target Gap", f"{gap_remaining:.1f} mi/day", delta="Above target",
              delta_color="inverse")

# ── VMT and GHG Calculations ─────────────────────────────────────────────
years = np.arange(2025, 2046)
n_years = len(years)

# BAU line: slight linear increase
bau_vmt = np.linspace(BASELINE_VMT, BAU_2045, n_years)

# CARB 2045 Target line: declining to target
target_vmt = np.linspace(BASELINE_VMT, TARGET_2045, n_years)

# Policy mix line: effect phases in gradually over 20 years
phase_in = (years - 2025) / 20.0
policy_vmt = BASELINE_VMT * (1 + (combined_pct / 100.0) * phase_in)

# GHG avoided per year (MMT CO2e)
vmt_avoided_daily = bau_vmt - policy_vmt  # mi/day/person
vmt_avoided_annual = vmt_avoided_daily * CA_POP * 365  # mi/year total
co2e_avoided_total = vmt_avoided_annual * EMFAC_FACTOR / 1e9  # MMT CO2e

# Per-lever GHG contributions (proportional allocation)
lever_ghg = {}
for k, info in LEVERS.items():
    val = lever_vals[k]
    if combined_pct != 0:
        share = val / combined_pct
    else:
        share = 0
    lever_ghg[k] = co2e_avoided_total * share

# ── CHART 1: VMT Trajectory ──────────────────────────────────────────────
st.markdown("---")
chart_left, chart_right = st.columns(2)

with chart_left:
    st.markdown(
        "##### Where Your Policy Mix Takes California\n"
        "<span style='font-size:0.82em; color:#888;'>Per-capita VMT projection based on "
        "literature-estimated effect sizes. Illustrative model — not a certified forecast.</span>",
        unsafe_allow_html=True,
    )

    fig_vmt = go.Figure()

    # Shaded gap region between BAU and policy
    fig_vmt.add_trace(go.Scatter(
        x=np.concatenate([years, years[::-1]]),
        y=np.concatenate([bau_vmt, policy_vmt[::-1]]),
        fill="toself",
        fillcolor="rgba(46,204,113,0.12)",
        line=dict(width=0),
        name="Gap Being Closed",
        showlegend=True,
        hoverinfo="skip",
    ))

    # BAU line
    fig_vmt.add_trace(go.Scatter(
        x=years, y=bau_vmt,
        name="Business as Usual",
        line=dict(color="#E8967A", width=2.5, dash="dash"),
        mode="lines",
    ))

    # CARB Target line
    fig_vmt.add_trace(go.Scatter(
        x=years, y=target_vmt,
        name="CARB 2045 Target",
        line=dict(color="#4A9B8E", width=2, dash="dash"),
        mode="lines",
    ))

    # Policy mix line
    fig_vmt.add_trace(go.Scatter(
        x=years, y=policy_vmt,
        name="Your Policy Mix",
        line=dict(color="#2ecc71", width=3.5),
        mode="lines",
    ))

    # Target annotation
    fig_vmt.add_hline(
        y=TARGET_2045, line_dash="dot", line_color="#4A9B8E",
        annotation_text=f"2045 Carbon Neutrality Target ({TARGET_2045} mi/day)",
        annotation_position="bottom right",
        annotation_font_size=10,
        annotation_font_color="#4A9B8E",
    )

    fig_vmt.update_layout(
        xaxis_title="Year",
        yaxis_title="Per-Capita VMT (miles/day/person)",
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=60, b=40),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
        xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
    )

    st.plotly_chart(fig_vmt, use_container_width=True)

# ── CHART 2: GHG Stacked Bar ─────────────────────────────────────────────
with chart_right:
    st.markdown(
        "##### Estimated Emissions Avoided vs. Business as Usual\n"
        "<span style='font-size:0.82em; color:#888;'>Based on EMFAC2021 fleet average "
        "emission factor (0.338 kg CO₂e/VMT). Illustrative only.</span>",
        unsafe_allow_html=True,
    )

    # Select milestone years for the bar chart
    milestone_years = [2025, 2030, 2035, 2040, 2045]
    milestone_indices = [int(y - 2025) for y in milestone_years]
    milestone_labels = [str(y) for y in milestone_years]

    fig_ghg = go.Figure()

    for k in LEVERS:
        info = LEVERS[k]
        bar_values = [lever_ghg[k][i] for i in milestone_indices]
        fig_ghg.add_trace(go.Bar(
            x=milestone_labels,
            y=bar_values,
            name=info["chart_label"],
            marker_color=info["color"],
            hovertemplate=f"{info['chart_label']}: %{{y:.2f}} MMT CO₂e<extra></extra>",
        ))

    # Add total labels
    totals = [co2e_avoided_total[i] for i in milestone_indices]
    fig_ghg.add_trace(go.Scatter(
        x=milestone_labels,
        y=[t + 0.3 if t > 0 else t - 0.3 for t in totals],
        text=[f"{t:.1f} MMT" for t in totals],
        mode="text",
        textfont=dict(size=11, color="#333"),
        showlegend=False,
        hoverinfo="skip",
    ))

    fig_ghg.update_layout(
        barmode="relative",
        xaxis_title="Year",
        yaxis_title="Cumulative CO₂e Avoided (MMT)",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=10)),
        margin=dict(t=60, b=40),
        plot_bgcolor="white",
        yaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
        xaxis=dict(gridcolor="rgba(0,0,0,0.06)"),
    )

    st.plotly_chart(fig_ghg, use_container_width=True)


# ── Methodology expander ─────────────────────────────────────────────────
with st.expander("📖 Methodology & Assumptions (for researchers and planners)"):
    st.markdown(
        """
**Policy Lever Effect Sizes**

| Lever | VMT Range | Literature Source | Notes |
|---|---|---|---|
| Transit-Oriented Development | −5% to −15% | Handy & Boarnet 2014; PPIC 2021 | Per-household effect; aggregate depends on scale of deployment |
| Toll Pricing & TDM | −4% to −12% | CARB SB 743 guidance; Litman 2022 | Strongest in congested urban corridors |
| Land Use Reform | 0% to −10% | Cervero & Kockelman 1997; CA HCD | Long-term structural effect; 10+ year lag |
| Public Transit Expansion | −2% to −8% | NCST 2022; TransForm California | Dependent on service quality and frequency |
| Highway Expansion | 0% to +15% | Duranton & Turner 2011; Caltrans/NCST | VMT elasticity of ~1.0 (induced demand) |
| Active Transportation | 0% to −5% | Buehler & Pucher 2012; Caltrans ATP | Primarily affects short trips (<3 mi) |

**Modeling Assumptions**

- Effects are modeled as **linear and additive** for illustrative purposes. In reality, 
  policy interactions are nonlinear — combining transit investment with TOD yields 
  compounding benefits, while highway expansion can partially offset other gains. This 
  simplification overstates certainty but preserves directional accuracy.

- **Induced demand** from highway expansion is modeled using a VMT elasticity of approximately 
  1.0, consistent with Duranton & Turner (2011) — meaning a 10% increase in highway capacity 
  generates roughly 10% more driving within a few years.

- **Phase-in period:** All policy effects are assumed to phase in linearly over 20 years 
  (2025–2045), reflecting real-world implementation lag from planning to construction to 
  behavioral change.

- **GHG conversion** uses the CARB EMFAC2021 statewide fleet-average emission factor of 
  **0.338 kg CO₂e per vehicle-mile traveled**. This factor will decline over time as EVs 
  penetrate the fleet, meaning GHG savings from VMT reduction will diminish relative to 
  technology-driven gains. This tool does not model fleet turnover.

- **Population** is held constant at 39 million for simplicity.

**Disclaimer**

This tool is designed for **policy communication and education**. Effect sizes are drawn 
from peer-reviewed literature but do not constitute a certified traffic or emissions model. 
For official data, see [CARB's SB 375 Dashboard](https://ww2.arb.ca.gov/our-work/programs/sustainable-communities-climate-protection-program/dashboard).
        """
    )
