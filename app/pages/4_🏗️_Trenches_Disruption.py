"""Trenches & Disruption - O-Line vs Pass Rush Analysis, Run Front Performance"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.db import query
from app.config import COLORS, TEAM_COLORS, SEASON_RANGE, SHARED_CSS, CHART_LAYOUT, metric_card, page_footer

st.set_page_config(page_title="Trenches & Disruption", layout="wide", initial_sidebar_state="expanded")
st.markdown(SHARED_CSS, unsafe_allow_html=True)

st.title("🏗️ Trenches & Disruption")
st.markdown("O-Line vs Pass Rush | Run Front Analysis | Tackle Leaders | Line Play Excellence")

st.markdown('<div class="ssa-info"><strong>Why this matters:</strong> Elite betting requires understanding line play. Sack rates reveal O-line quality and pass rush strength. Run direction analysis exposes run blocking tendencies. This dashboard tracks disruption (pass rush), pass protection (sacks allowed), and gap discipline (run direction). Key metrics for DFS and season props.</div>', unsafe_allow_html=True)

st.divider()

# Team name mapping
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

# Sidebar filters
st.sidebar.header("Filters")
season_range = st.sidebar.slider("Season Range", min_value=2000, max_value=2019, value=(2010, 2019), step=1)
selected_teams = st.sidebar.multiselect("Select Teams (blank=all)",
                                        options=sorted(pd.Series(TEAM_COLORS.keys()).unique()),
                                        default=[])

team_ids = ','.join([f"'{t}'" for t in selected_teams])
team_filter_clause = f"AND p.off IN ({team_ids})" if selected_teams else ""

# ==================== A) PRESSURE & SACK DASHBOARD ====================
st.header("A) Pressure & Sack Dashboard")

st.markdown('<div class="ssa-info"><strong>Metric guide:</strong> Sacks Allowed (offense perspective) = pass protection quality. Sacks Generated (defense perspective) = pass rush effectiveness. Higher sack rates = weaker pass blocking or elite pass rush.</div>', unsafe_allow_html=True)

@st.cache_data
def load_sack_stats(season_min, season_max):
    sql = """
    SELECT
        g.seas AS season,
        s.qb,
        s.sk,
        s.value,
        s.ydsl,
        p.off AS offense,
        p.def AS defense
    FROM sacks s
    JOIN plays p ON s.pid = p.pid
    JOIN games g ON p.gid = g.gid
    WHERE g.seas >= ? AND g.seas <= ?
    """
    return query(sql, (season_min, season_max))

sack_data = load_sack_stats(season_range[0], season_range[1])

@st.cache_data
def load_pass_attempts(season_min, season_max):
    sql = """
    SELECT
        g.seas AS season,
        p.off AS team,
        COUNT(*) AS pass_attempts
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE p.type = 'PASS' AND g.seas >= ? AND g.seas <= ?
    GROUP BY g.seas, p.off
    """
    return query(sql, (season_min, season_max))

pass_attempts = load_pass_attempts(season_range[0], season_range[1])

# Sacks allowed (offense perspective) and generated (defense perspective)
sacks_allowed = sack_data.groupby(['season', 'offense']).agg({
    'value': 'sum',
    'ydsl': 'sum'
}).reset_index()
sacks_allowed.columns = ['season', 'team', 'sacks_allowed', 'yards_lost']

sacks_generated = sack_data.groupby(['season', 'defense']).agg({
    'value': 'sum',
    'ydsl': 'sum'
}).reset_index()
sacks_generated.columns = ['season', 'team', 'sacks_generated', 'yards_lost']

# Merge with pass attempts to get sack rates
sacks_allowed = sacks_allowed.merge(pass_attempts, left_on=['season', 'team'], right_on=['season', 'team'], how='left')
sacks_allowed['sack_rate_allowed'] = (sacks_allowed['sacks_allowed'] / sacks_allowed['pass_attempts'] * 100).round(2)

# For sacks generated, we need opponent pass attempts
sacks_generated = sacks_generated.merge(pass_attempts.rename(columns={'team': 'opponent_team', 'pass_attempts': 'opp_pass_attempts'}),
                                        left_on=['season'], right_on=['season'], how='left')
sacks_generated['sack_rate_generated'] = (sacks_generated['sacks_generated'] / sacks_generated['opp_pass_attempts'] * 100).round(2)

# Get latest season average sack rate
if not sacks_allowed.empty:
    league_avg_sack_rate = (sacks_allowed[sacks_allowed['season'] == season_range[1]]['sack_rate_allowed'].mean())
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(metric_card("League Avg Sack Rate", f"{league_avg_sack_rate:.2f}%"), unsafe_allow_html=True)

    # Top pass rush defense
    top_pass_rush = sacks_generated[sacks_generated['season'] == season_range[1]].nlargest(1, 'sacks_generated')
    if not top_pass_rush.empty:
        with col2:
            st.markdown(metric_card("Top Pass Rush", top_pass_rush['team'].values[0],
                                   sub=f"{top_pass_rush['sacks_generated'].values[0]:.1f} sacks"), unsafe_allow_html=True)

    # Best O-line (lowest sack rate allowed)
    best_oline = sacks_allowed[sacks_allowed['season'] == season_range[1]].nsmallest(1, 'sack_rate_allowed')
    if not best_oline.empty:
        with col3:
            st.markdown(metric_card("Best O-Line", best_oline['team'].values[0],
                                   sub=f"{best_oline['sack_rate_allowed'].values[0]:.2f}%"), unsafe_allow_html=True)

    with col4:
        st.markdown(metric_card("Total Sacks", int(sacks_generated[sacks_generated['season'] == season_range[1]]['sacks_generated'].sum())), unsafe_allow_html=True)

# Dual bar chart
latest_season_sacks = sacks_allowed[sacks_allowed['season'] == season_range[1]].sort_values('sacks_allowed', ascending=False).head(16)
sacks_gen_filtered = sacks_generated[sacks_generated['season'] == season_range[1]].set_index('team')

fig = go.Figure()
fig.add_trace(go.Bar(
    x=latest_season_sacks['team'],
    y=latest_season_sacks['sacks_allowed'],
    name='Sacks Allowed (Offense)',
    marker=dict(color=COLORS['negative'])
))

for team in latest_season_sacks['team']:
    if team in sacks_gen_filtered.index:
        fig.add_trace(go.Bar(
            x=[team],
            y=[sacks_gen_filtered.loc[team, 'sacks_generated']],
            name='Sacks Generated (Defense)' if team == latest_season_sacks['team'].iloc[0] else '',
            marker=dict(color=COLORS['positive']),
            showlegend=(team == latest_season_sacks['team'].iloc[0])
        ))

fig.update_layout(**CHART_LAYOUT, height=500,
    title=f"Sacks Allowed vs Generated ({season_range[1]})",
    barmode='group',
    xaxis_title="Team",
    yaxis_title="Sacks",
    hovermode='x unified'
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==================== B) PASS RUSH LEADERS ====================
st.header("B) Pass Rush Leaders")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Sack value is weighted (full sack = 1, half sack = 0.5). Top edge rushers and interior linemen dominate here. Track players year-over-year for consistency.</div>', unsafe_allow_html=True)

@st.cache_data
def load_pass_rush_leaders(season_min, season_max):
    sql = """
    SELECT
        g.seas AS season,
        s.sk AS player_code,
        COALESCE(pl.pname, s.sk) AS player_name,
        SUM(s.value) AS total_sack_value,
        COUNT(*) AS sack_count,
        SUM(s.ydsl) AS total_yards_lost,
        ROUND(SUM(s.ydsl) / COUNT(*), 2) AS avg_yards_lost_per_sack
    FROM sacks s
    LEFT JOIN players pl ON s.sk = pl.player
    JOIN plays py ON s.pid = py.pid
    JOIN games g ON py.gid = g.gid
    WHERE g.seas >= ? AND g.seas <= ?
    GROUP BY g.seas, s.sk, pl.pname
    HAVING COUNT(*) > 0
    ORDER BY season DESC, total_sack_value DESC
    """
    return query(sql, (season_min, season_max))

rush_leaders = load_pass_rush_leaders(season_range[0], season_range[1])

if not rush_leaders.empty:
    # Get top 20 for latest season
    latest_rush = rush_leaders[rush_leaders['season'] == season_range[1]].head(20)

    fig = px.bar(
        latest_rush.sort_values('total_sack_value', ascending=True),
        x='total_sack_value',
        y='player_name',
        orientation='h',
        color='total_sack_value',
        color_continuous_scale=[(0, COLORS['accent']), (1, COLORS['accent3'])],
        title=f"Top 20 Pass Rushers ({season_range[1]})",
        labels={'total_sack_value': 'Total Sack Value', 'player_name': 'Player'},
        hover_data=['sack_count', 'avg_yards_lost_per_sack']
    )
    fig.update_layout(**CHART_LAYOUT, height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Sortable table
    st.subheader("Full Pass Rush Leaders Table")
    table_data = rush_leaders[rush_leaders['season'] == season_range[1]][
        ['player_name', 'season', 'total_sack_value', 'sack_count', 'avg_yards_lost_per_sack']
    ].sort_values('total_sack_value', ascending=False)
    table_data.columns = ['Player', 'Season', 'Total Sacks', 'Sack Count', 'Avg Yards Lost']
    st.dataframe(table_data, use_container_width=True, hide_index=True)

st.divider()

# ==================== C) RUN DIRECTION ANALYSIS ====================
st.header("C) Run Direction Analysis")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Success rate = plays that achieve first down or touchdown. Dominant run directions indicate strong run blocking. Low success rates suggest weak run game or elite run defense.</div>', unsafe_allow_html=True)

st.sidebar.subheader("Run Direction Filters")
run_direction_down = st.sidebar.multiselect("Down", [1, 2, 3, 4], default=[1, 2, 3])

@st.cache_data
def load_run_direction_stats(season_min, season_max):
    sql = """
    SELECT
        g.seas AS season,
        r.dir,
        p.off AS team,
        AVG(r.yds) AS avg_yards,
        COUNT(*) AS rush_count,
        SUM(CASE WHEN r.succ = 1 THEN 1 ELSE 0 END) AS successful_rushes
    FROM rushes r
    JOIN plays p ON r.pid = p.pid
    JOIN games g ON p.gid = g.gid
    WHERE g.seas >= ? AND g.seas <= ? AND r.dir IS NOT NULL
    GROUP BY g.seas, r.dir, p.off
    ORDER BY season DESC, team, r.dir
    """
    return query(sql, (season_min, season_max))

run_dir_stats = load_run_direction_stats(season_range[0], season_range[1])

if not run_dir_stats.empty:
    run_dir_stats['success_rate'] = (run_dir_stats['successful_rushes'] / run_dir_stats['rush_count'] * 100).round(2)

    # Overall by direction
    latest_by_dir = run_dir_stats[run_dir_stats['season'] == season_range[1]].groupby('dir').agg({
        'avg_yards': 'mean',
        'success_rate': 'mean',
        'rush_count': 'sum'
    }).reset_index().sort_values('avg_yards', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(
            latest_by_dir,
            x='dir',
            y='avg_yards',
            title=f"Avg Yards by Run Direction ({season_range[1]})",
            labels={'dir': 'Direction', 'avg_yards': 'Avg Yards'},
            color='avg_yards',
            color_continuous_scale=[(0, COLORS['negative']), (1, COLORS['positive'])]
        )
        fig1.update_layout(**CHART_LAYOUT, height=400, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(
            latest_by_dir,
            x='dir',
            y='success_rate',
            title=f"Success Rate by Direction ({season_range[1]})",
            labels={'dir': 'Direction', 'success_rate': 'Success Rate (%)'},
            color='success_rate',
            color_continuous_scale=[(0, COLORS['negative']), (1, COLORS['positive'])]
        )
        fig2.update_layout(**CHART_LAYOUT, height=400, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    # Heatmap: team x direction
    st.subheader("Run Direction Performance Heatmap")
    pivot_data = run_dir_stats[run_dir_stats['season'] == season_range[1]].pivot_table(
        index='team',
        columns='dir',
        values='avg_yards',
        aggfunc='mean'
    ).fillna(0)

    fig3 = px.imshow(
        pivot_data,
        title=f"Avg Yards per Rush by Team & Direction ({season_range[1]})",
        color_continuous_scale='RdYlGn',
        aspect='auto'
    )
    fig3.update_layout(**CHART_LAYOUT, height=600)
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ==================== D) O-LINE vs D-LINE MATCHUPS ====================
st.header("D) O-Line vs D-Line Matchups (Team Comparison)")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Team 1 vs Team 2 head-to-head comparison of pass protection, run blocking, and rushing ability. Use to evaluate strength of schedule and betting edges.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    team1 = st.selectbox("Team 1", options=sorted(TEAM_COLORS.keys()), index=0)
with col2:
    team2 = st.selectbox("Team 2", options=sorted(TEAM_COLORS.keys()), index=1)

if team1 and team2:
    @st.cache_data
    def get_team_matchup_stats(t1, t2, season_min, season_max):
        sql = """
        SELECT
            CASE WHEN p.off = ? THEN 'Team 1' ELSE 'Team 2' END AS perspective,
            CASE WHEN p.off = ? THEN ? ELSE ? END AS team,
            AVG(r.yds) AS avg_rush_yards,
            100.0 * SUM(CASE WHEN r.succ = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS rush_success_rate
        FROM rushes r
        JOIN plays p ON r.pid = p.pid
        JOIN games g ON p.gid = g.gid
        WHERE p.off IN (?, ?) AND g.seas >= ? AND g.seas <= ?
        GROUP BY perspective, team
        """
        return query(sql, (t1, t1, t1, t2, t1, t2, season_min, season_max))

    try:
        matchup_stats = get_team_matchup_stats(team1, team2, season_range[0], season_range[1])
        if not matchup_stats.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                avg_yds_1 = matchup_stats[matchup_stats['perspective']=='Team 1']['avg_rush_yards'].values
                if len(avg_yds_1) > 0:
                    st.markdown(metric_card(f"{team1} Avg Run Yards", f"{avg_yds_1[0]:.2f}"), unsafe_allow_html=True)
            with col2:
                avg_yds_2 = matchup_stats[matchup_stats['perspective']=='Team 2']['avg_rush_yards'].values
                if len(avg_yds_2) > 0:
                    st.markdown(metric_card(f"{team2} Avg Run Yards", f"{avg_yds_2[0]:.2f}"), unsafe_allow_html=True)
            with col3:
                st.write("")
    except Exception as e:
        st.info("Matchup data not fully available for selected teams.")

st.divider()

# ==================== E) TACKLE LEADERS ====================
st.header("E) Tackle Leaders")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Total tackles = all tackles (solo + combined). High tackle totals indicate strong defensive positioning and gap assignment. Track for DFS and consistency props.</div>', unsafe_allow_html=True)

@st.cache_data
def load_tackle_leaders(season_min, season_max):
    sql = """
    SELECT
        ds.game,
        ds.player AS player_code,
        COALESCE(pl.pname, ds.player) AS player_name,
        COALESCE(ds.solo, 0) + COALESCE(ds.comb, 0) AS total_tackles,
        ds.solo,
        ds.comb,
        ds.sck,
        ds.saf,
        ds.year
    FROM defense_stats ds
    LEFT JOIN players pl ON ds.player = pl.player
    WHERE ds.year >= ? AND ds.year <= ?
    ORDER BY ds.year DESC, total_tackles DESC
    """
    return query(sql, (season_min, season_max))

tackle_leaders = load_tackle_leaders(season_range[0], season_range[1])

if not tackle_leaders.empty:
    # Top 20 for latest season
    latest_tackles = tackle_leaders[tackle_leaders['year'] == season_range[1]].head(20)

    fig = px.bar(
        latest_tackles.sort_values('total_tackles', ascending=True),
        x='total_tackles',
        y='player_name',
        orientation='h',
        color='total_tackles',
        color_continuous_scale=[(0, COLORS['accent']), (1, COLORS['accent3'])],
        title=f"Top 20 Tacklers ({season_range[1]})",
        labels={'total_tackles': 'Total Tackles', 'player_name': 'Player'},
        hover_data=['solo', 'comb', 'sck', 'saf']
    )
    fig.update_layout(**CHART_LAYOUT, height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.subheader("Full Tackle Leaders Table")
    table_data = tackle_leaders[tackle_leaders['year'] == season_range[1]].head(50).copy()
    table_data = table_data[['game', 'player_name', 'total_tackles', 'solo', 'comb', 'sck', 'saf', 'year']]
    table_data.columns = ['Game', 'Player', 'Total Tackles', 'Solo', 'Combined', 'Sacks', 'Safeties', 'Year']
    st.dataframe(table_data, use_container_width=True, hide_index=True)

st.markdown(page_footer(), unsafe_allow_html=True)
