"""Penalties & Officiating Analysis — Sharp Sports Analysis."""
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

# Team mapping for full names
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

st.set_page_config(page_title="Penalties & Officiating", layout="wide", initial_sidebar_state="expanded")
st.markdown(SHARED_CSS, unsafe_allow_html=True)

st.title("⚖️ Penalties, Officiating & Hidden Yards")
st.markdown("""
**What this dashboard shows:** Penalty patterns, officiating consistency, and EPA impact of penalties across 20 seasons.
Why it matters: Teams that draw fewer penalties gain field position and momentum. Year-to-year penalty rates reveal disciplinary culture.
""")

# ═══════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("Filters")
    season_range = st.slider("Season Range", min_value=2000, max_value=2019, value=(2010, 2019), step=1)
    selected_teams = st.multiselect("Select Teams (blank=all)",
                                    options=sorted(pd.Series(TEAM_COLORS.keys()).unique()),
                                    default=[])
    penalty_accepted_only = st.checkbox("Accepted Penalties Only", value=True)

# ═══════════════════════════════════════════════════════════════
# A) PENALTY OVERVIEW
# ═══════════════════════════════════════════════════════════════
st.header("A. Penalty Overview")

@st.cache_data
def load_games_count(season_min, season_max):
    """Load games per season."""
    sql = """
    SELECT
        g.seas,
        COUNT(DISTINCT g.gid) AS game_count
    FROM games g
    WHERE g.seas >= ? AND g.seas <= ?
    GROUP BY g.seas
    """
    return query(sql, (season_min, season_max))


@st.cache_data
def load_all_penalties(season_min, season_max, selected_teams_tuple):
    """Load all penalties (accepted, declined, offsetting)."""
    sql = """
    SELECT
        pen.uid,
        pen.pid,
        pen.ptm AS penalized_team,
        pen."desc" AS penalty_desc,
        pen.cat AS category,
        pen.pey AS penalty_yards,
        pen.act AS action,
        g.seas AS season
    FROM penalties pen
    JOIN plays p ON pen.pid = p.pid
    JOIN games g ON p.gid = g.gid
    WHERE g.seas >= ? AND g.seas <= ?
    """
    return query(sql, (season_min, season_max))


@st.cache_data
def load_penalties(season_min, season_max, selected_teams_tuple, penalty_accepted_only_val):
    """Load penalty data. Fixed: use p.ptso/p.ptsd from plays, not g.ptso (games doesn't have it).
    Fixed: use quotes around desc as it's a SQL reserved word.
    Fixed: accept filter values as explicit parameters for proper cache invalidation."""
    sql = """
    SELECT
        pen.uid,
        pen.pid,
        pen.ptm AS penalized_team,
        pen."desc" AS penalty_desc,
        pen.cat AS category,
        pen.pey AS penalty_yards,
        pen.act AS action,
        g.seas AS season,
        p.off AS offensive_team,
        p.def AS defensive_team,
        p.type AS play_type,
        p.dwn AS down,
        p.qtr AS quarter,
        p.ptso,
        p.ptsd
    FROM penalties pen
    JOIN plays p ON pen.pid = p.pid
    JOIN games g ON p.gid = g.gid
    WHERE g.seas >= ? AND g.seas <= ?
    """
    return query(sql, (season_min, season_max))

penalties_df = load_penalties(
    season_range[0],
    season_range[1],
    tuple(selected_teams) if selected_teams else (),
    penalty_accepted_only
)

if not penalties_df.empty:
    if penalty_accepted_only:
        penalties_df = penalties_df[penalties_df['action'] == 'A']

    # Apply team filter if selected
    if selected_teams:
        penalties_df = penalties_df[penalties_df['penalized_team'].isin(selected_teams)]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card(
            "Total Penalties",
            f"{len(penalties_df):,}",
            f"Seasons {season_range[0]}–{season_range[1]}",
            "", "pos"
        ), unsafe_allow_html=True)

    with col2:
        total_yards = penalties_df['penalty_yards'].sum()
        st.markdown(metric_card(
            "Total Penalty Yards",
            f"{int(total_yards):,}",
            f"{total_yards / len(penalties_df):.1f} per penalty",
            "", "pos"
        ), unsafe_allow_html=True)

    with col3:
        most_penalized = penalties_df['penalized_team'].value_counts().index[0]
        count = penalties_df['penalized_team'].value_counts().values[0]
        st.markdown(metric_card(
            "Most Penalized Team",
            most_penalized,
            f"{count} penalties",
            "", "neg"
        ), unsafe_allow_html=True)

    with col4:
        most_common = penalties_df['penalty_desc'].value_counts().index[0]
        count = penalties_df['penalty_desc'].value_counts().values[0]
        st.markdown(metric_card(
            "Most Common Penalty",
            most_common[:25] if len(most_common) > 25 else most_common,
            f"{count} occurrences",
            "", "pos"
        ), unsafe_allow_html=True)

    # Apply team filter to penalties for display
    display_penalties_df = penalties_df.copy()
    if selected_teams:
        display_penalties_df = display_penalties_df[display_penalties_df['penalized_team'].isin(selected_teams)]

    # Top 20 penalties
    penalty_counts = display_penalties_df['penalty_desc'].value_counts().head(20)
    fig = px.bar(
        x=penalty_counts.values,
        y=penalty_counts.index,
        orientation='h',
        title="Top 20 Most Common Penalties",
        labels={'x': 'Frequency', 'y': 'Penalty Type'},
        color=penalty_counts.values,
        color_continuous_scale=[(0, COLORS['accent']), (1, COLORS['accent3'])]
    )
    fig.update_layout(**CHART_LAYOUT, height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# B) PENALTIES BY TEAM
# ═══════════════════════════════════════════════════════════════
st.header("B. Penalties by Team")

if not penalties_df.empty:
    games_per_season = load_games_count(season_range[0], season_range[1])

    # Use filtered penalties_df for calculations
    working_penalties_df = penalties_df.copy()
    if selected_teams:
        working_penalties_df = working_penalties_df[working_penalties_df['penalized_team'].isin(selected_teams)]

    penalties_per_game = working_penalties_df.groupby(['season', 'penalized_team']).agg({
        'uid': 'count',
        'penalty_yards': 'sum'
    }).reset_index()
    penalties_per_game.columns = ['season', 'team', 'penalty_count', 'penalty_yards']

    penalties_per_game = penalties_per_game.merge(
        games_per_season.rename(columns={'seas': 'season'}),
        on='season',
        how='left'
    )
    penalties_per_game['penalties_per_game'] = penalties_per_game['penalty_count'] / penalties_per_game['game_count']
    penalties_per_game['yards_per_game'] = penalties_per_game['penalty_yards'] / penalties_per_game['game_count']

    # Map team codes to full names for display
    penalties_per_game['team_name'] = penalties_per_game['team'].map(TEAM_FULL_NAMES)

    latest_season_penalties = penalties_per_game[penalties_per_game['season'] == season_range[1]].sort_values('penalties_per_game', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            latest_season_penalties.head(16),
            x='team_name',
            y='penalties_per_game',
            title=f"Penalties per Game by Team ({season_range[1]})",
            labels={'team_name': 'Team', 'penalties_per_game': 'Penalties/Game'},
            color='penalties_per_game',
            color_continuous_scale=[(0, COLORS['positive']), (1, COLORS['negative'])]
        )
        fig.update_layout(**CHART_LAYOUT, height=450, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            latest_season_penalties.head(16),
            x='team_name',
            y='yards_per_game',
            title=f"Penalty Yards per Game by Team ({season_range[1]})",
            labels={'team_name': 'Team', 'yards_per_game': 'Yards/Game'},
            color='yards_per_game',
            color_continuous_scale=[(0, COLORS['positive']), (1, COLORS['negative'])]
        )
        fig.update_layout(**CHART_LAYOUT, height=450, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# C) PENALTY TRENDS BY SEASON
# ═══════════════════════════════════════════════════════════════
st.header("C. Penalty Trends by Season")

if not penalties_df.empty and len(penalties_per_game) > 0:
    season_trends = penalties_per_game.groupby('season').agg({
        'penalties_per_game': 'mean',
        'yards_per_game': 'mean'
    }).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(x=season_trends['season'], y=season_trends['penalties_per_game'],
                   name='Penalties/Game', mode='lines+markers',
                   line=dict(color=COLORS['accent'], width=3)),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=season_trends['season'], y=season_trends['yards_per_game'],
                   name='Yards/Game', mode='lines+markers',
                   line=dict(color=COLORS['accent3'], width=3)),
        secondary_y=True,
    )
    fig.update_layout(**CHART_LAYOUT, height=400, title="League-Wide Penalty Trends",
                      hovermode='x unified')
    fig.update_yaxes(title_text="Penalties/Game", secondary_y=False)
    fig.update_yaxes(title_text="Yards/Game", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# D) SITUATIONAL ANALYSIS
# ═══════════════════════════════════════════════════════════════
st.header("D. Situational Analysis")

if not penalties_df.empty:
    penalties_df['score_diff'] = penalties_df['ptso'] - penalties_df['ptsd']
    penalties_df['score_bucket'] = pd.cut(
        penalties_df['score_diff'],
        bins=[-100, -8, -1, 1, 8, 100],
        labels=['Losing 8+', 'Losing 1-7', 'Tied', 'Winning 1-7', 'Winning 8+']
    )

    situation_heatmap = penalties_df.groupby(['down', 'quarter']).size().reset_index(name='penalty_count')
    pivot_down_qtr = situation_heatmap.pivot(index='down', columns='quarter', values='penalty_count').fillna(0)

    fig = px.imshow(
        pivot_down_qtr,
        title="Penalty Frequency by Down & Quarter",
        labels=dict(x='Quarter', y='Down', color='Count'),
        color_continuous_scale='Viridis',
        aspect='auto'
    )
    fig.update_layout(**CHART_LAYOUT, height=400)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        score_penalties = penalties_df['score_bucket'].value_counts().sort_index()
        fig = px.bar(
            x=score_penalties.index.astype(str),
            y=score_penalties.values,
            title="Penalties by Score Differential",
            labels={'x': 'Game Situation', 'y': 'Penalty Count'},
            color=score_penalties.values,
            color_continuous_scale=[(0, COLORS['accent']), (1, COLORS['accent3'])]
        )
        fig.update_layout(**CHART_LAYOUT, height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        down_penalties = penalties_df['down'].value_counts().sort_index()
        fig = px.bar(
            x=down_penalties.index.astype(str),
            y=down_penalties.values,
            title="Penalties by Down",
            labels={'x': 'Down', 'y': 'Penalty Count'},
            color=down_penalties.values,
            color_continuous_scale=[(0, COLORS['accent']), (1, COLORS['accent3'])]
        )
        fig.update_layout(**CHART_LAYOUT, height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# E) YEAR-OVER-YEAR STABILITY
# ═══════════════════════════════════════════════════════════════
st.header("E. Year-over-Year Stability")

if not penalties_df.empty and len(penalties_per_game) > 1:
    penalties_by_team_year = penalties_per_game.pivot_table(
        index='team',
        columns='season',
        values='penalties_per_game',
        aggfunc='first'
    )

    if penalties_by_team_year.shape[1] >= 2:
        seasons_list = sorted(penalties_by_team_year.columns)
        year_idx = st.selectbox(
            "Compare Consecutive Seasons",
            options=range(len(seasons_list)-1),
            format_func=lambda x: f"{seasons_list[x]} vs {seasons_list[x+1]}"
        )

        year1_season = seasons_list[year_idx]
        year2_season = seasons_list[year_idx + 1]

        comparison_data = penalties_by_team_year[[year1_season, year2_season]].dropna()

        if len(comparison_data) > 0:
            correlation = comparison_data[year1_season].corr(comparison_data[year2_season])

            fig = px.scatter(
                comparison_data.reset_index(),
                x=year1_season,
                y=year2_season,
                text='team',
                title=f"Penalty Consistency: {year1_season} vs {year2_season} (Corr: {correlation:.2f})",
                labels={year1_season: f'Penalties/Game {year1_season}', year2_season: f'Penalties/Game {year2_season}'}
            )
            fig.update_traces(textposition='top center', marker=dict(size=10, color=COLORS['accent']))
            fig.update_layout(**CHART_LAYOUT, height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# F) PENALTY TYPE DEEP DIVE
# ═══════════════════════════════════════════════════════════════
st.header("F. Penalty Type Deep Dive & Acceptance Rates")

if not penalties_df.empty:
    all_penalties = load_all_penalties(
        season_range[0],
        season_range[1],
        tuple(selected_teams) if selected_teams else ()
    )

    # Apply team filter if selected
    if selected_teams:
        all_penalties = all_penalties[all_penalties['penalized_team'].isin(selected_teams)]

    col1, col2 = st.columns(2)

    with col1:
        action_counts = all_penalties['action'].value_counts()
        action_labels = {'A': 'Accepted', 'D': 'Declined', 'O': 'Offsetting'}
        action_counts.index = action_counts.index.map(lambda x: action_labels.get(x, x))

        fig = px.pie(
            values=action_counts.values,
            names=action_counts.index,
            title="Penalty Outcome Distribution",
            color_discrete_map={
                'Accepted': COLORS['accent'],
                'Declined': COLORS['negative'],
                'Offsetting': COLORS['warn']
            }
        )
        fig.update_layout(**CHART_LAYOUT, height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        declined_penalties = all_penalties[all_penalties['action'] == 'D']['penalty_desc'].value_counts().head(10)
        fig = px.bar(
            x=declined_penalties.values,
            y=declined_penalties.index,
            orientation='h',
            title="Most Commonly Declined Penalties",
            labels={'x': 'Count', 'y': 'Penalty Type'},
            color=declined_penalties.values,
            color_continuous_scale=[(0, COLORS['accent']), (1, COLORS['accent3'])]
        )
        fig.update_layout(**CHART_LAYOUT, height=450, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Acceptance Rate by Penalty Type")
    penalty_acceptance = all_penalties.groupby('penalty_desc').agg({
        'action': ['count', lambda x: (x == 'A').sum()]
    }).reset_index()
    penalty_acceptance.columns = ['penalty_desc', 'total', 'accepted']
    penalty_acceptance['acceptance_rate'] = (penalty_acceptance['accepted'] / penalty_acceptance['total'] * 100).round(1)
    penalty_acceptance = penalty_acceptance.sort_values('acceptance_rate', ascending=False).head(15)

    fig = px.bar(
        penalty_acceptance,
        x='penalty_desc',
        y='acceptance_rate',
        title="Top 15 Penalties by Acceptance Rate",
        labels={'penalty_desc': 'Penalty Type', 'acceptance_rate': 'Acceptance Rate (%)'},
        color='acceptance_rate',
        color_continuous_scale=[(0, COLORS['negative']), (1, COLORS['positive'])]
    )
    fig.update_layout(**CHART_LAYOUT, height=450, xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(page_footer(), unsafe_allow_html=True)
