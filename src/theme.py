"""
Shared visual theme for the SB 1087 Capstone Dashboard.

Import helpers from here in every page so all charts stay consistent.
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# ---------------------------------------------------------------------------
# Brand palette
# ---------------------------------------------------------------------------
# Primary greens align with NRDC/environmental policy brand language.
# Accent orange/red surfaces policy gaps and risk signals.

NRDC_GREEN       = "#2E7D32"      # deep forest green  – primary highlight
NRDC_GREEN_LIGHT = "#66BB6A"      # mid green          – secondary fill
NRDC_TEAL        = "#00695C"      # teal               – complement
ACCENT_ORANGE    = "#E65100"      # deep orange        – gap / warning
ACCENT_RED       = "#C62828"      # deep red           – alert
NEUTRAL_DARK     = "#1A1A2E"      # near-black         – plot bg
NEUTRAL_MID      = "#2D3142"      # dark-slate         – gridlines
NEUTRAL_LIGHT    = "#E8F5E9"      # pale green         – chart bg
PAPER_WHITE      = "#FAFAFA"      # near-white         – paper bg

# Five-state palette (CA always first / darkest)
STATE_COLORS: dict[str, str] = {
    "CA": NRDC_GREEN,
    "CO": "#1565C0",   # cobalt blue
    "MA": "#6A1B9A",   # purple
    "MN": "#00838F",   # cyan-teal
    "VA": "#AD1457",   # magenta
}

PILLAR_COLORS: dict[str, str] = {
    "Pillar 1": ACCENT_RED,
    "Pillar 2": ACCENT_ORANGE,
    "Pillar 3": NRDC_TEAL,
    "Pillar 4": "#1565C0",
}

# 6-step diverging sequential for heatmaps
HEATMAP_SCALE = "YlGn"

# Plotly template name
TEMPLATE_NAME = "nrdc_sb1087"

# ---------------------------------------------------------------------------
# Register custom Plotly template
# ---------------------------------------------------------------------------

def _build_template() -> go.layout.Template:
    t = go.layout.Template()

    t.layout = go.Layout(
        font=dict(family="Inter, Arial, sans-serif", size=13, color="#1A1A2E"),
        title=dict(
            font=dict(size=17, color=NRDC_GREEN, family="Inter, Arial, sans-serif"),
            x=0.03,
            xanchor="left",
        ),
        paper_bgcolor=PAPER_WHITE,
        plot_bgcolor=NEUTRAL_LIGHT,
        colorway=[
            NRDC_GREEN, NRDC_TEAL, NRDC_GREEN_LIGHT,
            ACCENT_ORANGE, ACCENT_RED, "#1565C0", "#6A1B9A",
        ],
        xaxis=dict(
            showgrid=True,
            gridcolor="#C8E6C9",
            gridwidth=1,
            zeroline=False,
            linecolor="#A5D6A7",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#C8E6C9",
            gridwidth=1,
            zeroline=False,
            linecolor="#A5D6A7",
            tickfont=dict(size=11),
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#A5D6A7",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=60, r=30, t=60, b=50),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=NRDC_GREEN,
            font=dict(size=12, color="#1A1A2E"),
        ),
    )

    # Bar default style
    t.data.bar = [go.Bar(marker=dict(line=dict(width=0), opacity=0.9))]  # type: ignore[assignment]

    # Scatter default
    t.data.scatter = [go.Scatter(marker=dict(size=9, line=dict(width=1, color="white")))]  # type: ignore[assignment]

    return t


pio.templates[TEMPLATE_NAME] = _build_template()
pio.templates.default = TEMPLATE_NAME


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def apply_chart_style(
    fig: go.Figure,
    *,
    height: int = 420,
    show_legend: bool = True,
    legend_title: str | None = None,
) -> go.Figure:
    """Apply consistent post-processing tweaks to any Plotly figure."""
    fig.update_layout(
        height=height,
        showlegend=show_legend,
        legend_title_text=legend_title or "",
    )
    return fig


def gap_fill_scatter(
    x,
    y,
    fillcolor: str = "rgba(198, 40, 40, 0.15)",
) -> go.Scatter:
    """Return a transparent area-fill trace for the implementation gap."""
    return go.Scatter(
        x=x,
        y=y,
        mode="lines",
        fill="tonexty",
        fillcolor=fillcolor,
        line=dict(color="rgba(0,0,0,0)"),
        showlegend=False,
        hoverinfo="skip",
    )


def state_color(state: str) -> str:
    return STATE_COLORS.get(state, "#607D8B")


def pillar_color(pillar: str) -> str:
    return PILLAR_COLORS.get(pillar, "#607D8B")


def subsector_color_map() -> dict[str, str]:
    return {
        "light_duty_mmt":  NRDC_GREEN,
        "heavy_duty_mmt":  ACCENT_ORANGE,
        "aviation_mmt":    "#1565C0",
        "rail_mmt":        NRDC_TEAL,
        "marine_mmt":      "#6A1B9A",
    }


SUBSECTOR_LABELS: dict[str, str] = {
    "light_duty_mmt":  "Light-Duty",
    "heavy_duty_mmt":  "Heavy-Duty",
    "aviation_mmt":    "Aviation",
    "rail_mmt":        "Rail",
    "marine_mmt":      "Marine",
}


# ---------------------------------------------------------------------------
# Streamlit app-level styling helpers
# ---------------------------------------------------------------------------

APP_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 4rem !important;
        max-width: 900px !important;
    }

    /* Modern clean sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FAFAFA !important;
        border-right: 1px solid #EAEAEA !important;
    }
    
    section[data-testid="stSidebar"] .st-emotion-cache-16txtl3 {
        padding: 2rem 1rem !important;
    }

    /* Clean up the metric cards to look more minimal */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #EAEAEA;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
    }

    .capstone-hero {
        background: #FFFFFF;
        color: #111827;
        border-radius: 0;
        padding: 0 0 2rem 0;
        margin-bottom: 2rem;
        border-bottom: 2px solid #EAEAEA;
        box-shadow: none;
    }

    .capstone-hero h2 {
        margin: 0 0 0.5rem 0;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #111827;
    }

    .capstone-hero p {
        margin: 0;
        font-size: 1.125rem;
        color: #4B5563;
        line-height: 1.6;
        font-weight: 400;
    }

    .capstone-card {
        border: 1px solid #EAEAEA;
        border-radius: 8px;
        padding: 1.5rem;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.5rem;
    }

    .capstone-card-title {
        color: #111827;
        font-weight: 700;
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }

    .capstone-card-body {
        color: #4B5563;
        margin: 0;
        font-size: 1rem;
        line-height: 1.6;
    }

    .insight-panel {
        border-left: 4px solid #3B82F6;
        background: #EFF6FF;
        border-radius: 4px;
        padding: 1rem 1.25rem;
        margin: 1.5rem 0;
    }

    .insight-panel h4 {
        margin: 0 0 0.5rem 0;
        color: #1E3A8A;
        font-weight: 600;
    }

    .insight-panel p {
        margin: 0;
        color: #1E40AF;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .section-kicker {
        display: inline-block;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #6B7280;
        margin-bottom: 0.5rem;
    }

    .policy-link-list a {
        text-decoration: none;
        font-weight: 600;
        color: #2563EB;
    }

    .policy-link-list a:hover {
        text-decoration: underline;
    }

    /* Markdown text styling to match a modern document */
    .stMarkdown p, .stMarkdown li {
        font-size: 1.1rem;
        line-height: 1.7;
        color: #374151;
    }
    .stMarkdown h1 {
        font-size: 2.25rem;
        font-weight: 800;
        color: #111827;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stMarkdown h2 {
        font-size: 1.8rem;
        font-weight: 700;
        color: #111827;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .stMarkdown h3 {
        font-size: 1.4rem;
        font-weight: 600;
        color: #111827;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
</style>
"""


def inject_app_style() -> None:
    """Inject shared Streamlit CSS for polished page presentation."""
    try:
        import streamlit as st
        st.markdown(APP_CSS, unsafe_allow_html=True)
    except Exception:
        # Keep this no-op safe for non-Streamlit execution contexts.
        pass

DIMENSION_LABELS: dict[str, str] = {
    "planning_mandate_strength":  "Planning Mandate",
    "funding_accountability":      "Funding Accountability",
    "induced_demand_controls":     "Induced-Demand Controls",
    "equity_targeting":            "Equity Targeting",
    "monitoring_enforcement":      "Monitoring & Enforcement",
    "multimodal_investment":       "Multimodal Investment",
}
