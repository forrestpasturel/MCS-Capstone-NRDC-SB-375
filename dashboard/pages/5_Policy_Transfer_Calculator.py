import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Policy Transfer Calculator", page_icon="🧮", layout="wide")

try:
    from src.theme import inject_app_style
except ImportError:
    pass

if "inject_app_style" in globals():
    inject_app_style()
st.title("🧮 Policy Transfer Calculator")
st.markdown(
    """
<div class="capstone-hero">
  <h2>Scenario Export Workbench</h2>
  <p>
    Generate region-level and ZCTA-level policy transfer outputs, then export briefing-ready
    summaries to support stakeholder communication and policy memo drafting.
  </p>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("Estimate California VMT and GHG reduction potential by region and ZCTA under MN/CO/VA/MA-style implementation.")

MODEL_FACTORS = {
    "Minnesota (MN)": {"vmt": 0.22, "ghg": 0.18},
    "Colorado (CO)": {"vmt": 0.16, "ghg": 0.20},
    "Virginia (VA)": {"vmt": 0.12, "ghg": 0.14},
    "Massachusetts (MA)": {"vmt": 0.19, "ghg": 0.21},
}


def _to_markdown_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, r in df.iterrows():
        vals = [str(r[c]) for c in cols]
        rows.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep] + rows)

try:
    df = pd.read_csv("data/app/ca_zcta_spatial.csv")

    st.sidebar.header("Scenario Controls")
    selected_model = st.sidebar.selectbox("Policy model", list(MODEL_FACTORS.keys()))
    adoption_strength = st.sidebar.slider("Implementation strength", 0, 100, 70, 5)
    calc_palette = st.sidebar.selectbox("Chart color theme", ["Set2", "Bold", "Safe"], index=0)
    calc_palette_map = {
        "Set2": px.colors.qualitative.Set2,
        "Bold": px.colors.qualitative.Bold,
        "Safe": px.colors.qualitative.Safe,
    }
    region_filter = st.sidebar.multiselect("Region filter", sorted(df["region"].unique().tolist()), default=sorted(df["region"].unique().tolist()))

    alpha = adoption_strength / 100.0
    factor = MODEL_FACTORS[selected_model]

    scoped = df[df["region"].isin(region_filter)].copy()
    scoped["vmt_reduction_potential"] = np.clip(scoped["vmt_gap_index"], 0, None) * factor["vmt"] * alpha
    scoped["ghg_reduction_potential"] = np.clip(scoped["ghg_per_capita"], 0, None) * factor["ghg"] * alpha
    scoped["combined_opportunity_index"] = 0.55 * scoped["vmt_reduction_potential"] + 0.45 * scoped["ghg_reduction_potential"]

    summary = (
        scoped.groupby("region", as_index=False)
        .agg(
            zcta_count=("zcta", "count"),
            vmt_reduction_potential=("vmt_reduction_potential", "sum"),
            ghg_reduction_potential=("ghg_reduction_potential", "sum"),
            avg_opportunity=("combined_opportunity_index", "mean"),
        )
        .sort_values("avg_opportunity", ascending=False)
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Selected model", selected_model)
    c2.metric("Scoped ZCTAs", f"{len(scoped):,}")
    c3.metric("Top region (opportunity)", summary.iloc[0]["region"] if not summary.empty else "N/A")

    fig = px.bar(
        summary,
        x="region",
        y=["vmt_reduction_potential", "ghg_reduction_potential"],
        barmode="group",
        title="Modeled regional reduction potential",
        labels={
            "value": "Reduction potential units",
            "region": "California Region",
            "variable": "Reduction Metric",
        },
        color_discrete_sequence=calc_palette_map[calc_palette],
    )
    fig.update_layout(legend_title_text="Metric")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Grouped bars compare modeled VMT and GHG potential by region under the selected policy model.")

    st.markdown("### Download regional and ZCTA scenarios")
    st.dataframe(summary, use_container_width=True)

    st.download_button(
        label="Download region summary CSV",
        data=summary.to_csv(index=False).encode("utf-8"),
        file_name="policy_transfer_region_summary.csv",
        mime="text/csv",
    )

    top_zcta = scoped.sort_values("combined_opportunity_index", ascending=False).head(25)
    st.dataframe(top_zcta[[
        "zcta",
        "region",
        "vmt_gap_index",
        "ghg_per_capita",
        "vmt_reduction_potential",
        "ghg_reduction_potential",
        "combined_opportunity_index",
    ]], use_container_width=True)

    st.download_button(
        label="Download top ZCTA opportunities CSV",
        data=top_zcta.to_csv(index=False).encode("utf-8"),
        file_name="policy_transfer_top_zcta.csv",
        mime="text/csv",
    )

    st.markdown("<div class='section-kicker'>TREND & IMPLICATIONS</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="insight-panel">
  <h4>Scenario interpretation</h4>
  <p>
    Under the current settings, <b>{summary.iloc[0]['region'] if not summary.empty else 'N/A'}</b> ranks highest in modeled opportunity.
    This indicates where implementation pilots could yield the most visible first-year policy impact.
    Use the CSV exports to prioritize phased deployment and stakeholder engagement geography.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("### One-click briefing export")
    lead_region = summary.iloc[0]["region"] if not summary.empty else "N/A"
    lead_vmt = float(summary.iloc[0]["vmt_reduction_potential"]) if not summary.empty else 0.0
    lead_ghg = float(summary.iloc[0]["ghg_reduction_potential"]) if not summary.empty else 0.0
    top10 = top_zcta[[
        "zcta",
        "region",
        "vmt_reduction_potential",
        "ghg_reduction_potential",
        "combined_opportunity_index",
    ]].head(10).copy()
    top10 = top10.round(3)
    top10_table_md = _to_markdown_table(top10)

    briefing_md = f"""# SB 1087 Policy Transfer Brief (Draft)

## Scenario
- Model selected: {selected_model}
- California implementation strength: {adoption_strength}%
- Regions included: {', '.join(region_filter) if region_filter else 'None'}

## Key findings
- Total scoped ZCTAs: {len(scoped):,}
- Highest-opportunity region: {lead_region}
- Regional potential in top region:
  - VMT reduction potential: {lead_vmt:.2f}
  - GHG reduction potential: {lead_ghg:.2f}

## Top ZCTA opportunities
{top10_table_md}

## Interpretation
This draft estimates where California could capture the highest co-benefits from transferring out-of-state policy architecture into SB 1087 implementation and funding rules.
"""

    st.download_button(
        label="Download policy brief (Markdown)",
        data=briefing_md.encode("utf-8"),
        file_name="sb1087_policy_transfer_brief.md",
        mime="text/markdown",
    )

    st.text_area("Briefing preview", briefing_md, height=260)

    with st.expander("Model assumptions and caveats"):
        st.markdown(
            """
- Reduction potentials are policy-transfer proxies for comparative decision support, not deterministic forecasts.
- Results are sensitive to implementation strength and selected model factors.
- Use this module for prioritization and communication; use engineering/environmental review for project-level validation.
"""
        )

except Exception as e:
    st.error(f"Failed to build policy transfer calculator: {e}")
