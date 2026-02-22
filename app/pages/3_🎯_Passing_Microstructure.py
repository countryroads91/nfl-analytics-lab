"""Passing Game Microstructure - QB Profiles, Target Distribution, and Pressure Analysis"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.db import query
from app.config import COLORS, TEAM_COLORS, SEASON_RANGE, SHARED_CSS, CHART_LAYOUT, metric_card, page_footer

st.set_page_config(page_title="Passing Microstructure", layout="wide", initial_sidebar_state="expanded")
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Team full names mapping
TEAM_FULL_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "JAC": "Jacksonville Jaguars", "KC": "Kansas City Chiefs", "LAC": "LA Chargers",
    "LA": "LA Rams", "LAR": "LA Rams", "LV": "Las Vegas Raiders", "OAK": "Oakland Raiders",
    "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings", "NE": "New England Patriots",
    "NO": "New Orleans Saints", "NYG": "New York Giants", "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers", "SF": "San Francisco 49ers",
    "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans",
    "WAS": "Washington", "SD": "San Diego Chargers", "STL": "St. Louis Rams",
}

st.title("🎯 Passing Game Microstructure")
st.markdown("Depth, location, pressure analysis, QB profiles, and target distribution. Essential for understanding passing efficiency by situation.")

# Intro section
st.markdown('<div class="ssa-info"><strong>Why this matters:</strong> Bettors and analysts need to understand WHERE quarterbacks target receivers and HOW pressure affects performance. This dashboard breaks down passing microstructure by depth (short/intermediate/deep), direction (left/middle/right), and pressure context. Focus on EPA/play and success rates to evaluate QB and WR efficiency.</div>', unsafe_allow_html=True)

st.divider()

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
with st.sidebar:
    st.header("Filters")
    season_select = st.selectbox("Season", options=sorted(SEASON_RANGE, reverse=True), index=0)

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_data
def load_pass_data(season_select):
    """Load comprehensive passing data with EPA and success metrics."""
    sql = """
    SELECT
        pa.psr, pa.trg, pa.loc, pa.yds, pa.comp, pa.spk,
        p.gid, p.epa, p.succ, p.pid, p.detail,
        g.seas, g.v, g.h,
        psr_pl.pname as psr_name,
        trg_pl.pname as trg_name
    FROM passes pa
    JOIN plays p ON pa.pid = p.pid
    JOIN games g ON p.gid = g.gid
    LEFT JOIN players psr_pl ON pa.psr = psr_pl.player
    LEFT JOIN players trg_pl ON pa.trg = trg_pl.player
    WHERE g.seas = ?
    """
    return query(sql, [season_select])

@st.cache_data
def load_sack_data(season_select):
    """Load sack data for pressure analysis."""
    sql = """
    SELECT
        s.qb, s.sk, s.value,
        p.gid, p.epa, p.detail,
        g.seas,
        qb_pl.pname as qb_name,
        sk_pl.pname as sk_name
    FROM sacks s
    JOIN plays p ON s.pid = p.pid
    JOIN games g ON p.gid = g.gid
    LEFT JOIN players qb_pl ON s.qb = qb_pl.player
    LEFT JOIN players sk_pl ON s.sk = sk_pl.player
    WHERE g.seas = ?
    """
    return query(sql, [season_select])

@st.cache_data
def load_play_totals(season_select):
    """Load all plays to compute dropback totals."""
    sql = """
    SELECT
        p.gid, p.pid, p.off, p.type, p.detail, p.epa
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE g.seas = ? AND p.type IN ('PASS', 'SACK')
    """
    return query(sql, [season_select])

@st.cache_data
def load_player_names():
    """Load player names for QB matching."""
    sql = """
    SELECT DISTINCT player, pname, pos1
    FROM players
    WHERE (pos1 = 'QB' OR pos1 LIKE '%QB%') AND player IS NOT NULL
    """
    return query(sql)

passes_df = load_pass_data(season_select)
sacks_df = load_sack_data(season_select)
plays_df = load_play_totals(season_select)
players_df = load_player_names()

# Build qb_options: list of passer codes (used in Section D & E dropdowns)
qb_options = sorted(passes_df['psr'].dropna().unique().tolist())

# Parse location into depth and direction IMMEDIATELY after loading
def parse_location(loc):
    if pd.isna(loc):
        return "Unknown", "Unknown"
    loc_str = str(loc).upper()

    # Determine depth
    if 'D' in loc_str:
        depth = "Deep"
    elif 'I' in loc_str:
        depth = "Intermediate"
    else:
        depth = "Short"

    # Determine direction
    if 'L' in loc_str:
        direction = "Left"
    elif 'R' in loc_str:
        direction = "Right"
    else:
        direction = "Middle"

    return depth, direction

passes_df[['depth_cat', 'direction_cat']] = passes_df['loc'].apply(
    lambda x: pd.Series(parse_location(x))
)

# ============================================================================
# METRIC CARDS
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

league_comp = (passes_df['comp'] == 1).sum() / len(passes_df) * 100 if len(passes_df) > 0 else 0

# Average depth of target (estimate from location)
def location_depth(loc):
    if pd.isna(loc):
        return np.nan
    loc_str = str(loc).upper()
    if 'D' in loc_str:  # Deep
        return 15
    elif 'I' in loc_str:  # Intermediate
        return 10
    else:  # Short
        return 3

passes_df['depth_est'] = passes_df['loc'].apply(location_depth)
avg_depth = passes_df['depth_est'].mean()

# Sack rate
total_dropbacks = len(plays_df[plays_df['type'].isin(['PASS', 'SACK'])])
total_sacks = len(sacks_df)
sack_rate = (total_sacks / total_dropbacks * 100) if total_dropbacks > 0 else 0

# Explosive pass rate
exp_pass_rate = (passes_df['yds'] >= 20).sum() / len(passes_df) * 100 if len(passes_df) > 0 else 0

with col1:
    st.markdown(metric_card("League Comp %", f"{league_comp:.1f}%"), unsafe_allow_html=True)

with col2:
    st.markdown(metric_card("Avg Depth (yds)", f"{avg_depth:.1f}"), unsafe_allow_html=True)

with col3:
    st.markdown(metric_card("Sack Rate %", f"{sack_rate:.1f}%"), unsafe_allow_html=True)

with col4:
    st.markdown(metric_card("Explosive 20+ %", f"{exp_pass_rate:.1f}%"), unsafe_allow_html=True)

st.divider()

# ============================================================================
# SECTION A: PASSING DEPTH/LOCATION MATRIX
# ============================================================================
st.header("A) Passing Depth/Location Matrix")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> High completion % and EPA on deep balls indicate a strong passing game. Short, intermediate, and deep routes target different defensive weaknesses. Compare across directions to see if offenses have directional tendencies.</div>', unsafe_allow_html=True)

col_a1, col_a2 = st.columns(2)

with col_a1:
    depth_metric = st.radio("Metric", ["Completion %", "EPA/Attempt"], horizontal=True)

with col_a2:
    # Build passer lookup: code -> display name
    passer_lookup = {}
    for psr_code in sorted(passes_df['psr'].dropna().unique()):
        rows = passes_df[passes_df['psr'] == psr_code]
        psr_name = rows['psr_name'].iloc[0] if len(rows) > 0 and pd.notna(rows['psr_name'].iloc[0]) else None
        display = psr_name if psr_name else psr_code
        passer_lookup[psr_code] = display
    passer_display_options = ["All Teams"] + [passer_lookup[c] for c in sorted(passer_lookup.keys())]
    passer_code_options = ["All Teams"] + sorted(passer_lookup.keys())
    passer_idx = st.selectbox("Passer", range(len(passer_display_options)),
                              format_func=lambda i: passer_display_options[i], key="passer_depth")
    passer_filter = passer_code_options[passer_idx]

# Filter passes
depth_passes = passes_df.copy()
if passer_filter != "All Teams":
    depth_passes = depth_passes[depth_passes['psr'] == passer_filter]

# Build heatmap data
if depth_metric == "Completion %":
    hm_data = depth_passes.groupby(['depth_cat', 'direction_cat']).agg({
        'comp': lambda x: (x == 1).sum() / len(x) * 100 if len(x) > 0 else 0,
        'pid': 'count'
    }).reset_index()
    hm_data.columns = ['Depth', 'Direction', 'Metric', 'Count']
else:  # EPA/Attempt
    hm_data = depth_passes.groupby(['depth_cat', 'direction_cat']).agg({
        'epa': 'mean',
        'pid': 'count'
    }).reset_index()
    hm_data.columns = ['Depth', 'Direction', 'Metric', 'Count']

# Pivot for heatmap
hm_pivot = hm_data.pivot(index='Depth', columns='Direction', values='Metric')
count_pivot = hm_data.pivot(index='Depth', columns='Direction', values='Count')

# Reorder
depth_order = ['Short', 'Intermediate', 'Deep']
dir_order = ['Left', 'Middle', 'Right']
hm_pivot = hm_pivot.reindex(depth_order).reindex(dir_order, axis=1)
count_pivot = count_pivot.reindex(depth_order).reindex(dir_order, axis=1)

fig_hm_depth = go.Figure(data=go.Heatmap(
    z=hm_pivot.values,
    x=hm_pivot.columns,
    y=hm_pivot.index,
    colorscale="RdYlGn",
    text=[[f"{hm_pivot.iloc[i, j]:.1f}%<br>(n={count_pivot.iloc[i, j]:.0f})"
           for j in range(len(hm_pivot.columns))]
          for i in range(len(hm_pivot))],
    texttemplate='%{text}',
    textfont={"size": 11},
    colorbar=dict(title=depth_metric)
))

fig_hm_depth.update_layout(**CHART_LAYOUT, height=400, title=f"Passing {depth_metric} by Depth & Direction")
st.plotly_chart(fig_hm_depth, use_container_width=True)

st.divider()

# ============================================================================
# SECTION B: QB PROFILE CARDS
# ============================================================================
st.header("B) QB Profile Cards")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Individual QB performance relative to league average. High EPA/attempt indicates efficient QB play. Target depth and direction distribution reveal play-calling tendencies and receiver routes.</div>', unsafe_allow_html=True)

qb_list = sorted(passes_df['psr'].dropna().unique())
qb_display_list = []
for qb_code in qb_list:
    rows = passes_df[passes_df['psr'] == qb_code]
    qb_name = rows['psr_name'].iloc[0] if len(rows) > 0 and pd.notna(rows['psr_name'].iloc[0]) else None
    qb_display_list.append(qb_name if qb_name else qb_code)
qb_idx = st.selectbox("Select Quarterback", range(len(qb_list)),
                       format_func=lambda i: qb_display_list[i], key="qb_profile")
selected_qb = qb_list[qb_idx]
selected_qb_name = qb_display_list[qb_idx]

qb_passes = passes_df[passes_df['psr'] == selected_qb].copy()

if len(qb_passes) > 0:
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)

    qb_comp = (qb_passes['comp'] == 1).sum() / len(qb_passes) * 100
    qb_epa = qb_passes['epa'].mean()
    qb_ypa = qb_passes['yds'].mean()
    qb_depth = qb_passes['depth_est'].mean()

    with col_b1:
        st.markdown(metric_card("Comp %", f"{qb_comp:.1f}%", delta=f"{qb_comp - league_comp:.1f}%"), unsafe_allow_html=True)

    with col_b2:
        st.markdown(metric_card("EPA/Attempt", f"{qb_epa:.3f}"), unsafe_allow_html=True)

    with col_b3:
        st.markdown(metric_card("Yards/Attempt", f"{qb_ypa:.2f}"), unsafe_allow_html=True)

    with col_b4:
        st.markdown(metric_card("Avg Depth", f"{qb_depth:.1f} yds"), unsafe_allow_html=True)

    # QB depth distribution
    col_b_dist1, col_b_dist2 = st.columns(2)

    with col_b_dist1:
        # Depth distribution
        depth_dist = qb_passes['depth_cat'].value_counts()
        fig_qb_depth = go.Figure(data=[go.Pie(
            labels=depth_dist.index,
            values=depth_dist.values,
            marker=dict(colors=[COLORS['accent'], COLORS['accent2'], COLORS['warn']])
        )])
        fig_qb_depth.update_layout(**CHART_LAYOUT, height=350, title=f"{selected_qb_name} - Target Depth Distribution")
        st.plotly_chart(fig_qb_depth, use_container_width=True)

    with col_b_dist2:
        # Direction distribution
        dir_dist = qb_passes['direction_cat'].value_counts()
        fig_qb_dir = go.Figure(data=[go.Pie(
            labels=dir_dist.index,
            values=dir_dist.values,
            marker=dict(colors=[COLORS['accent'], COLORS['neutral'], COLORS['accent2']])
        )])
        fig_qb_dir.update_layout(**CHART_LAYOUT, height=350, title=f"{selected_qb_name} - Target Direction Distribution")
        st.plotly_chart(fig_qb_dir, use_container_width=True)

    # QB vs League comparison radar
    st.subheader(f"{selected_qb_name} vs League Average")

    # Normalize metrics to 0-100 scale for radar
    qb_metrics = {
        'Comp%': qb_comp,
        'Yards/Attempt': qb_ypa * 10,  # Scale up for visibility
        'EPA/Attempt': (qb_epa + 0.5) * 100,  # Shift and scale
        'Success Rate': (qb_passes['succ'] == 'Y').sum() / len(qb_passes) * 100,
    }

    league_metrics = {
        'Comp%': league_comp,
        'Yards/Attempt': passes_df['yds'].mean() * 10,
        'EPA/Attempt': (passes_df['epa'].mean() + 0.5) * 100,
        'Success Rate': (passes_df['succ'] == 'Y').sum() / len(passes_df) * 100,
    }

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[qb_metrics[k] for k in qb_metrics.keys()],
        theta=list(qb_metrics.keys()),
        fill='toself',
        name=selected_qb_name,
        line=dict(color=COLORS['accent']),
        fillcolor='rgba(26, 155, 80, 0.2)'
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[league_metrics[k] for k in league_metrics.keys()],
        theta=list(league_metrics.keys()),
        fill='toself',
        name='League Avg',
        line=dict(color=COLORS['neutral']),
        fillcolor='rgba(41, 128, 185, 0.15)'
    ))

    fig_radar.update_layout(**CHART_LAYOUT, height=450, polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    st.plotly_chart(fig_radar, use_container_width=True)

else:
    st.warning(f"No passing data available for {selected_qb_name} in {season_select}")

st.divider()

# ============================================================================
# SECTION C: PRESSURE IMPACT
# ============================================================================
st.header("C) Pressure Impact")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Significant EPA drops under pressure (typically -0.5 to -1.5 EPA/play) indicate vulnerable QB or weak pass protection. Teams with elite pass rush show positive sack totals and low opponent EPA.</div>', unsafe_allow_html=True)

col_c1, col_c2 = st.columns(2)

# Sack rate by team
sack_plays = plays_df[plays_df['type'].isin(['PASS', 'SACK'])].copy()
team_sacks = sack_plays.groupby('off').agg({
    'pid': 'count',
}).reset_index()
team_sacks.columns = ['Team', 'Total Dropbacks']

sack_counts = sacks_df.groupby('sk').size().reset_index(name='Sacks')
sack_counts.columns = ['Team', 'Sacks']

# Merge
team_pressure = team_sacks.merge(sack_counts, left_on='Team', right_on='Team', how='left')
team_pressure['Sacks'] = team_pressure['Sacks'].fillna(0)
team_pressure['Sack Rate %'] = (team_pressure['Sacks'] / team_pressure['Total Dropbacks'] * 100)
team_pressure = team_pressure.sort_values('Sack Rate %', ascending=False)

with col_c1:
    st.subheader("Sack Rate by Team (Defense)")
    st.dataframe(
        team_pressure[['Team', 'Sack Rate %', 'Sacks', 'Total Dropbacks']].style.format({
            'Sack Rate %': '{:.2f}%',
            'Sacks': '{:.0f}',
            'Total Dropbacks': '{:.0f}'
        }),
        use_container_width=True,
        height=400
    )

with col_c2:
    # Sack rate bar chart
    fig_sack = go.Figure()
    fig_sack.add_trace(go.Bar(
        x=team_pressure['Team'],
        y=team_pressure['Sack Rate %'],
        marker=dict(color=COLORS['accent']),
        text=[f"{x:.2f}%" for x in team_pressure['Sack Rate %']],
        textposition='auto'
    ))

    fig_sack.update_layout(**CHART_LAYOUT, height=400, title="Defensive Sack Rate", xaxis_title="Team", yaxis_title="Sack Rate %", showlegend=False)
    st.plotly_chart(fig_sack, use_container_width=True)

# Pressure vs clean pocket EPA
st.subheader("EPA: Pressured vs Clean Pocket")

# Identify pressured plays (simple: plays with sacks, or low EPA on pass plays)
pressured_epa = sacks_df['epa'].mean()
clean_pass = passes_df['epa'].mean()

col_pres1, col_pres2 = st.columns(2)

with col_pres1:
    fig_pressure_epa = go.Figure()
    fig_pressure_epa.add_trace(go.Bar(
        x=['Clean Pocket', 'Under Pressure'],
        y=[clean_pass, pressured_epa],
        marker=dict(color=[COLORS['positive'], COLORS['negative']]),
        text=[f"{clean_pass:.3f}", f"{pressured_epa:.3f}"],
        textposition='auto'
    ))

    fig_pressure_epa.update_layout(**CHART_LAYOUT, height=350, title="EPA/Play: Pressure Impact", yaxis_title="EPA/Play", showlegend=False)
    st.plotly_chart(fig_pressure_epa, use_container_width=True)

with col_pres2:
    st.markdown(metric_card("EPA Differential", f"{clean_pass - pressured_epa:.3f}", sub="Worse under pressure"), unsafe_allow_html=True)

st.divider()

# ============================================================================
# SECTION D: TARGET DISTRIBUTION
# ============================================================================
st.header("D) Target Distribution")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Bubble size = total yards. Efficient receivers are those with high targets AND high yards per catch. EPA/target shows whether the receiver is a net positive or negative for offensive efficiency.</div>', unsafe_allow_html=True)

target_team = st.selectbox("Select Team for Target Analysis",
                          ["All Teams"] + qb_options,
                          key="target_team")

if target_team != "All Teams":
    target_passes = passes_df[passes_df['psr'] == target_team].copy()
else:
    target_passes = passes_df.copy()

# Top receivers
receivers = target_passes.groupby('trg').agg({
    'pid': 'count',
    'yds': ['sum', 'mean'],
    'comp': lambda x: (x == 1).sum(),
    'epa': 'mean',
    'trg_name': 'first'
}).reset_index()
receivers.columns = ['Receiver', 'Targets', 'Total Yards', 'Yards/Catch', 'Catches', 'EPA/Target', 'Receiver Name']
receivers['Catch Rate %'] = (receivers['Catches'] / receivers['Targets'] * 100)
# Use receiver names if available, otherwise use codes
receivers['Receiver Display'] = receivers.apply(
    lambda x: f"{x['Receiver']} - {x['Receiver Name']}" if x['Receiver Name'] and x['Receiver Name'] != x['Receiver'] else x['Receiver'],
    axis=1
)
receivers = receivers.sort_values('Targets', ascending=False).head(15)

col_d1, col_d2 = st.columns(2)

with col_d1:
    st.subheader("Top Receivers by Targets")
    # Use receiver names where available
    receivers['Display Name'] = receivers.apply(
        lambda x: x['Receiver Name'] if pd.notna(x['Receiver Name']) and x['Receiver Name'] else x['Receiver'], axis=1)
    st.dataframe(
        receivers[['Display Name', 'Targets', 'Catches', 'Catch Rate %', 'Total Yards', 'EPA/Target']].rename(
            columns={'Display Name': 'Player'}).style.format({
            'Catch Rate %': '{:.1f}%',
            'EPA/Target': '{:.3f}'
        }),
        use_container_width=True,
        height=400
    )

with col_d2:
    # Bubble chart: targets vs yards per target
    fig_bubble = go.Figure()
    fig_bubble.add_trace(go.Scatter(
        x=receivers['Targets'],
        y=receivers['Yards/Catch'],
        mode='markers',
        marker=dict(
            size=receivers['Total Yards'] / 50,  # Size by total yards
            color=receivers['EPA/Target'],
            colorscale="RdYlGn",
            colorbar=dict(title="EPA/Target"),
            line=dict(width=1, color=COLORS['accent'])
        ),
        text=receivers['Receiver Display'],
        hovertemplate='<b>%{text}</b><br>Targets: %{x}<br>Yards/Catch: %{y:.2f}<extra></extra>'
    ))

    fig_bubble.update_layout(**CHART_LAYOUT, height=400, title="Target Distribution: Volume vs Efficiency", xaxis_title="Targets", yaxis_title="Yards per Catch", hovermode='closest')
    st.plotly_chart(fig_bubble, use_container_width=True)

st.divider()

# ============================================================================
# SECTION E: PLAY EXPLORER
# ============================================================================
st.header("E) Pass Play Explorer")

st.markdown('<div class="ssa-info"><strong>How to use:</strong> Filter by passer, receiver, location, and yard range to drill into specific play types. Sort by EPA to find highest-value plays. EPA > 0 means the play was more efficient than average.</div>', unsafe_allow_html=True)

col_e_filter1, col_e_filter2, col_e_filter3, col_e_filter4 = st.columns(4)

with col_e_filter1:
    explorer_passer_options = ["All"] + qb_options
    explorer_passer = st.selectbox("Passer", explorer_passer_options,
                                  key="explorer_passer")

with col_e_filter2:
    # Create receiver options with names
    receiver_options = ["All"]
    for rcv_code in sorted(passes_df['trg'].dropna().unique()):
        rcv_name = passes_df[passes_df['trg'] == rcv_code]['trg_name'].iloc[0] if len(passes_df[passes_df['trg'] == rcv_code]) > 0 else rcv_code
        rcv_display = f"{rcv_code} - {rcv_name}" if rcv_name and rcv_name != rcv_code else rcv_code
        receiver_options.append(rcv_code)
    explorer_receiver = st.selectbox("Receiver", receiver_options,
                                    key="explorer_receiver")

with col_e_filter3:
    explorer_location = st.selectbox("Location", ["All"] + sorted(passes_df['loc'].dropna().unique()),
                                    key="explorer_location")

with col_e_filter4:
    explorer_yards_min = st.number_input("Min Yards", value=-20, step=5)
    explorer_yards_max = st.number_input("Max Yards", value=80, step=5)

# Apply filters
explorer_df = passes_df.copy()

if explorer_passer != "All":
    explorer_df = explorer_df[explorer_df['psr'] == explorer_passer]

if explorer_receiver != "All":
    explorer_df = explorer_df[explorer_df['trg'] == explorer_receiver]

if explorer_location != "All":
    explorer_df = explorer_df[explorer_df['loc'] == explorer_location]

explorer_df = explorer_df[(explorer_df['yds'] >= explorer_yards_min) & (explorer_df['yds'] <= explorer_yards_max)]

# Display plays — use names instead of codes
explorer_df['Passer'] = explorer_df['psr_name'].fillna(explorer_df['psr'])
explorer_df['Receiver'] = explorer_df['trg_name'].fillna(explorer_df['trg'])
display_cols = ['gid', 'Passer', 'Receiver', 'loc', 'yds', 'comp', 'epa', 'detail']
available_cols = [c for c in display_cols if c in explorer_df.columns]

st.dataframe(
    explorer_df[available_cols].sort_values('epa', ascending=False).head(200).style.format({
        'yds': '{:.0f}',
        'epa': '{:.3f}',
        'comp': lambda x: 'Complete' if x == 1 else 'Incomplete'
    }),
    use_container_width=True,
    height=500
)

st.caption(f"Showing {len(explorer_df)} pass plays matching filters (limited to first 200)")

st.markdown(page_footer(), unsafe_allow_html=True)
