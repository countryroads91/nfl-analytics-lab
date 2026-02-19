"""Sharp Sports Analysis — NFL Analytics Lab Home Page."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.db import query
from app.config import SHARED_CSS, COLORS, metric_card, page_footer

st.set_page_config(
    page_title="Sharp Sports Analysis — NFL Analytics Lab",
    page_icon="♞",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(SHARED_CSS, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# HERO SECTION — Elegant branded header with chess knight motif
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align: center; padding: 48px 0 28px;">
    <div style="display: inline-block; margin-bottom: 18px;">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="64" height="64">
            <defs>
                <linearGradient id="glow" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:#1A9B50;stop-opacity:1"/>
                    <stop offset="100%" style="stop-color:#145A32;stop-opacity:1"/>
                </linearGradient>
            </defs>
            <path d="M16 40h16v3H16zM14 38h20v3H14z" fill="#1A9B50" opacity="0.7"/>
            <path d="M18 38c0-6 2-10 2-14s-3-8-3-12c0-3 2-5 5-6 1 2 3 3 5 3 2 0 4-1 5-3 2 1 3 3 3 5 0 3-1 5-2 8s1 8 1 13c0 2-1 4-3 5H21c-2-1-3-3-3-5z" fill="url(#glow)"/>
            <circle cx="22" cy="14" r="1.5" fill="#FFFFFF"/>
            <path d="M20 18c1-1 3-1 5 0" stroke="#FFFFFF" stroke-width="0.8" fill="none" stroke-linecap="round"/>
        </svg>
    </div>
    <h1 style="font-size: 3.4rem; font-weight: 800; letter-spacing: -0.04em; margin: 0; color: #1C2833;
               background: linear-gradient(135deg, #1C2833 0%, #1A9B50 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        Sharp Sports Analysis
    </h1>
    <p style="font-size: 1.15rem; color: #566573; font-weight: 400; margin: 10px 0 0; letter-spacing: 0.02em;">
        Research-driven analytics for the modern sports bettor
    </p>
    <div style="width: 60px; height: 3px; background: linear-gradient(90deg, #1A9B50, #27AE60); margin: 20px auto 0; border-radius: 2px;"></div>
    <p style="color: #95A5A6; font-size: 0.88rem; margin-top: 16px; letter-spacing: 0.01em;">
        20 seasons &middot; 873K plays &middot; 5,324 games &middot; Armchair Analysis 2000–2019
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# KEY METRICS
# ═══════════════════════════════════════════════════════════════
st.markdown("### Database Overview")

try:
    games_data = query("SELECT COUNT(*) as n, MIN(seas) as min_s, MAX(seas) as max_s FROM games")
    plays_data = query("SELECT COUNT(*) as n FROM plays")
    pass_data = query("SELECT COUNT(*) as n FROM passes")
    rush_data = query("SELECT COUNT(*) as n FROM rushes")
    players_data = query("SELECT COUNT(*) as n FROM players")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(metric_card(
            "Games Analyzed",
            f"{games_data['n'].iloc[0]:,}",
            f"Seasons {int(games_data['min_s'].iloc[0])}–{int(games_data['max_s'].iloc[0])}",
            "", "pos"
        ), unsafe_allow_html=True)

    with col2:
        st.markdown(metric_card(
            "Total Plays",
            f"{plays_data['n'].iloc[0]:,}",
            "Play-by-play records",
            "", "pos"
        ), unsafe_allow_html=True)

    with col3:
        st.markdown(metric_card(
            "Pass Plays",
            f"{pass_data['n'].iloc[0]:,}",
            "With target & passer",
            "", "pos"
        ), unsafe_allow_html=True)

    with col4:
        st.markdown(metric_card(
            "Rush Plays",
            f"{rush_data['n'].iloc[0]:,}",
            "With direction & carrier",
            "", "pos"
        ), unsafe_allow_html=True)

    with col5:
        st.markdown(metric_card(
            "Players",
            f"{players_data['n'].iloc[0]:,}",
            "Bio & combine data",
            "", "pos"
        ), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error loading metrics: {e}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# DASHBOARD GUIDE
# ═══════════════════════════════════════════════════════════════
st.markdown("### Dashboard Suite")

dashboards = [
    ("📊", "Market & CLV Lab", "Track point spread accuracy, closing line value, and market inefficiencies across seasons."),
    ("⚡", "Efficiency Explorer", "Deep-dive EPA trends by team, season, and situation with uncertainty quantification."),
    ("🎯", "Passing Microstructure", "Decompose passing plays by depth, location, coverage, and pressure environment."),
    ("🏗️", "Trenches & Disruption", "Rush direction analysis, pressure generation, and line performance dynamics."),
    ("🎲", "Fourth Down Lab", "Expected points framework with coach tendency analysis and what-if simulator."),
    ("⚖️", "Penalties & Officiating", "Penalty distributions, EPA impact, and year-over-year team stability."),
    ("🔴", "Red Zone DNA", "Playcalling tendencies and conversion efficiency inside the 20-yard line."),
    ("🔮", "Model Workbench", "Elo ratings, EPA strength, spread prediction, and calibration diagnostics."),
]

cols = st.columns(4)
for i, (icon, title, desc) in enumerate(dashboards):
    with cols[i % 4]:
        st.markdown(f"""
        <div class="ssa-metric" style="min-height: 120px;">
            <div style="font-size: 1.5rem; margin-bottom: 6px;">{icon}</div>
            <div class="label">{title}</div>
            <div class="sub" style="margin-top: 6px; line-height: 1.4;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# ARCHITECTURE
# ═══════════════════════════════════════════════════════════════
st.markdown("### System Architecture")

st.markdown("""
<div class="ssa-info">
<strong>Data Pipeline:</strong> 27 CSV tables → Parquet → DuckDB (210 MB) with 50 canonical tables/views<br>
<strong>Coverage:</strong> 2000–2019 NFL seasons (20 complete regular seasons + playoffs)<br>
<strong>Key Tables:</strong> Plays (873K), Passes (360K), Rushes (290K), Drives (124K), Games (5,324)<br>
<strong>Core Metrics:</strong> EPA, success rate, explosive plays, pressure rates, penalty yards, betting lines<br>
<strong>Technology:</strong> Python + DuckDB + Streamlit + Plotly with custom CSS theming
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# RESEARCH FOUNDATION
# ═══════════════════════════════════════════════════════════════
st.markdown("### Research Foundation")

st.markdown("""
<div class="ssa-info">
Every dashboard is grounded in peer-reviewed research and industry best practices:<br><br>
<strong>EPA Framework</strong> — Carter & Machol (1971) → nflfastR (Horowitz, Yurko, et al.)<br>
<strong>Fourth Down Theory</strong> — Romer (2006), Burke & Quealy (NYT 4th Down Bot)<br>
<strong>Market Efficiency</strong> — Levitt (2004), CLV research (Pinnacle, Peabody)<br>
<strong>Team Strength Modeling</strong> — Glickman & Stern (Bayesian hierarchical approaches)<br>
<strong>Causal Inference</strong> — Injury impact, weather effects, rest advantages<br>
<strong>Evaluation Metrics</strong> — Brier score, calibration curves, Kelly criterion<br><br>
See the <strong>Glossary & Methods</strong> page for detailed methodology, citations, and data validation notes.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# GETTING STARTED
# ═══════════════════════════════════════════════════════════════
st.markdown("### Getting Started")

st.markdown("""
<div class="ssa-info">
<strong>For Bettors:</strong> Start with Market CLV Lab to identify undervalued spreads and totals, then deep-dive into matchup-specific metrics like EPA trends, penalty patterns, and red zone efficiency.<br><br>
<strong>For Analysts:</strong> Use the Model Workbench to understand team strength, calibration dynamics, and feature importance. Layer in situational splits (fourth down, penalties, efficiency by down/distance).<br><br>
<strong>For Researchers:</strong> All metrics include sample sizes and uncertainty estimates. Download raw data via SQL queries in the glossary section.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Footer
st.markdown(page_footer(), unsafe_allow_html=True)
