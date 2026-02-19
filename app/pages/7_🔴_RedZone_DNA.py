"""Red Zone DNA — Sharp Sports Analysis."""
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

st.set_page_config(page_title="Red Zone DNA", layout="wide", initial_sidebar_state="expanded")
st.markdown(SHARED_CSS, unsafe_allow_html=True)

st.title("🔴 Red Zone DNA: Playcalling & Conversion Analysis")
st.markdown("""
**What this dashboard shows:** Offensive playcalling patterns and efficiency in critical scoring positions (yfog >= 80).
Why it matters: Red zone efficiency separates elite offenses from average ones. Identify which teams execute, which call predictably, and where edge exists.
""")

# ═══════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("Filters")
    seasons = st.multiselect(
        "Seasons",
        SEASON_RANGE,
        default=[2015, 2016, 2017, 2018, 2019],
        key="rz_seasons"
    )

    teams_df = query("SELECT DISTINCT off as team FROM plays WHERE off IS NOT NULL ORDER BY off")
    teams_list = teams_df['team'].tolist()
    selected_teams = st.multiselect(
        "Teams (leave empty for league view)",
        teams_list,
        key="rz_teams"
    )

    zone_type = st.radio(
        "Zone Definition",
        options=["Red Zone (yfog >= 80)", "Goal-to-Go (yfog >= 99)", "Inside the 5 (yfog >= 95)"],
        index=0,
        key="rz_zone_type"
    )

zone_map = {
    "Red Zone (yfog >= 80)": "yfog >= 80",
    "Goal-to-Go (yfog >= 99)": "yfog >= 99",
    "Inside the 5 (yfog >= 95)": "yfog >= 95"
}
zone_condition = zone_map[zone_type]

# ═══════════════════════════════════════════════════════════════
# A) RED ZONE EFFICIENCY OVERVIEW
# ═══════════════════════════════════════════════════════════════
st.header("A. Red Zone Efficiency Overview")

@st.cache_data
def get_rz_efficiency(seasons_tuple, zone_cond):
    """FIXED: Join plays with games to get seas column (plays doesn't have seas)."""
    sql = f"""
    SELECT
        p.off as team,
        g.seas as season,
        COUNT(*) as plays,
        SUM(CASE WHEN p.type = 'PASS' THEN 1 ELSE 0 END) as pass_plays,
        SUM(CASE WHEN p.type = 'RUSH' THEN 1 ELSE 0 END) as rush_plays,
        AVG(CASE WHEN p.succ='Y' THEN 1.0 ELSE 0.0 END) as success_rate,
        AVG(p.eps) as epa_per_play,
        COUNT(DISTINCT CASE WHEN p.pts > 0 THEN p.gid ELSE NULL END) as scoring_drives,
        COUNT(DISTINCT p.gid) as total_drives
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE {zone_cond}
        AND g.seas IN ({','.join(map(str, seasons_tuple))})
        AND p.off IS NOT NULL
        AND p.type IN ('PASS', 'RUSH')
    GROUP BY p.off, g.seas
    ORDER BY season DESC, epa_per_play DESC
    """
    return query(sql)

rz_efficiency = get_rz_efficiency(tuple(seasons), zone_condition)

if len(rz_efficiency) > 0:
    col1, col2, col3, col4 = st.columns(4)

    league_success_rate = rz_efficiency['success_rate'].mean()
    league_epa = rz_efficiency['epa_per_play'].mean()
    league_scoring_rate = rz_efficiency['scoring_drives'].sum() / rz_efficiency['total_drives'].sum()
    total_plays = rz_efficiency['plays'].sum()

    with col1:
        st.markdown(metric_card(
            "Lg Avg Success Rate",
            f"{league_success_rate:.1%}",
            "All teams & seasons", "", "pos"
        ), unsafe_allow_html=True)

    with col2:
        st.markdown(metric_card(
            "Lg Avg EPA/Play",
            f"{league_epa:.2f}",
            "Expected pts added", "", "pos"
        ), unsafe_allow_html=True)

    with col3:
        st.markdown(metric_card(
            "Lg Scoring Rate",
            f"{league_scoring_rate:.1%}",
            "TD or FG per drive", "", "pos"
        ), unsafe_allow_html=True)

    with col4:
        st.markdown(metric_card(
            "Total Plays",
            f"{int(total_plays):,}",
            "Analyzed", "", "pos"
        ), unsafe_allow_html=True)

    # Team ranking by EPA/play
    if len(selected_teams) == 0:
        rz_by_team = rz_efficiency.groupby('team').agg({
            'plays': 'sum',
            'success_rate': 'mean',
            'epa_per_play': 'mean',
            'scoring_drives': 'sum',
            'total_drives': 'sum'
        }).reset_index()
        rz_by_team['scoring_rate'] = rz_by_team['scoring_drives'] / rz_by_team['total_drives']
        rz_by_team = rz_by_team.sort_values('epa_per_play', ascending=False)
    else:
        rz_by_team = rz_efficiency[rz_efficiency['team'].isin(selected_teams)].copy()

    # Add team names
    rz_by_team['team_name'] = rz_by_team['team'].map(lambda x: TEAM_FULL_NAMES.get(x, x))

    fig_epa = px.bar(
        rz_by_team.sort_values('epa_per_play', ascending=True),
        y='team_name',
        x='epa_per_play',
        orientation='h',
        labels={'epa_per_play': 'EPA per Play', 'team_name': 'Team'},
        title=f"Red Zone EPA per Play (n={int(rz_by_team['plays'].sum())} plays)",
        color='epa_per_play',
        color_continuous_scale=['#FF6B6B', '#FFB347', '#2ECC71']
    )
    fig_epa.update_layout(**CHART_LAYOUT, height=400, xaxis_title='EPA per Play', yaxis_title='', showlegend=False)
    st.plotly_chart(fig_epa, use_container_width=True)

    st.subheader("Red Zone Stats by Team")
    display_df = rz_by_team[['team_name', 'plays', 'success_rate', 'epa_per_play', 'scoring_rate']].copy()
    display_df.columns = ['Team', 'Plays', 'Success Rate', 'EPA/Play', 'Scoring Rate']
    display_df['Success Rate'] = display_df['Success Rate'].apply(lambda x: f"{x:.1%}")
    display_df['EPA/Play'] = display_df['EPA/Play'].apply(lambda x: f"{x:.2f}")
    display_df['Scoring Rate'] = display_df['Scoring Rate'].apply(lambda x: f"{x:.1%}")
    display_df['Plays'] = display_df['Plays'].astype(int)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════
# B) PLAYCALLING TENDENCIES IN RED ZONE
# ═══════════════════════════════════════════════════════════════
st.header("B. Playcalling Tendencies in Red Zone")

@st.cache_data
def get_playcall_heatmap(seasons_tuple, zone_cond, teams_tuple=None):
    team_filter = ""
    if teams_tuple and len(teams_tuple) > 0:
        teams_str = "', '".join(teams_tuple)
        team_filter = f" AND p.off IN ('{teams_str}')"

    sql = f"""
    SELECT
        p.dwn as down,
        p.ytg as yards_to_go,
        SUM(CASE WHEN p.type = 'PASS' THEN 1 ELSE 0 END) as passes,
        SUM(CASE WHEN p.type = 'RUSH' THEN 1 ELSE 0 END) as rushes,
        COUNT(*) as total_plays
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE {zone_cond}
        AND g.seas IN ({','.join(map(str, seasons_tuple))})
        AND p.off IS NOT NULL
        AND p.type IN ('PASS', 'RUSH')
        AND p.dwn IS NOT NULL
        AND p.ytg IS NOT NULL
        AND p.ytg <= 10
        {team_filter}
    GROUP BY p.dwn, p.ytg
    ORDER BY p.dwn, p.ytg
    """
    df = query(sql)
    df['pass_rate'] = df['passes'] / (df['passes'] + df['rushes'])
    return df

playcall_data = get_playcall_heatmap(tuple(seasons), zone_condition, tuple(selected_teams) if selected_teams else None)

if len(playcall_data) > 0:
    pivot_data = playcall_data.pivot_table(
        index='down',
        columns='yards_to_go',
        values='pass_rate',
        fill_value=np.nan
    )

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=pivot_data.values * 100,
            x=pivot_data.columns,
            y=pivot_data.index,
            colorscale='RdYlGn_r',
            text=np.round(pivot_data.values * 100, 0),
            texttemplate='%{text:.0f}%',
            textfont={"size": 10},
            colorbar=dict(title="Pass Rate %"),
            zmin=0,
            zmax=100
        )
    )
    fig_heatmap.update_layout(
        **CHART_LAYOUT,
        height=400,
        title=f"Pass Rate by Down & Yards to Go ({zone_type})",
        xaxis_title="Yards to Go",
        yaxis_title="Down"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    pass_by_down = playcall_data.groupby('down').apply(
        lambda x: x['passes'].sum() / (x['passes'].sum() + x['rushes'].sum())
    ).reset_index()
    pass_by_down.columns = ['down', 'pass_rate']

    fig_down = px.bar(
        pass_by_down.sort_values('down'),
        x='down',
        y='pass_rate',
        labels={'down': 'Down', 'pass_rate': 'Pass Rate'},
        title=f"Pass Rate by Down ({zone_type})",
        color='pass_rate',
        color_continuous_scale=['#E74C3C', '#F39C12', '#2ECC71'],
        text='pass_rate'
    )
    fig_down.update_traces(texttemplate='%{y:.1%}', textposition='auto')
    fig_down.update_layout(**CHART_LAYOUT, height=350, yaxis_tickformat='.0%', showlegend=False)
    st.plotly_chart(fig_down, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# C) GOAL-TO-GO ANALYSIS
# ═══════════════════════════════════════════════════════════════
st.header("C. Goal-to-Go Analysis (Inside the 1-Yard Line)")

@st.cache_data
def get_goal_to_go_stats(seasons_tuple, teams_tuple=None):
    team_filter = ""
    if teams_tuple and len(teams_tuple) > 0:
        teams_str = "', '".join(teams_tuple)
        team_filter = f" AND p.off IN ('{teams_str}')"

    sql = f"""
    SELECT
        p.type,
        CASE WHEN p.type = 'RUSH' THEN p.dir ELSE 'PASS' END as play_direction,
        COUNT(*) as attempts,
        SUM(CASE WHEN p.yds >= 1 AND (p.type = 'PASS' OR (p.type = 'RUSH' AND (p.kne IS NULL OR p.kne != 'Y'))) THEN 1 ELSE 0 END) as successful,
        ROUND(100.0 * SUM(CASE WHEN p.yds >= 1 AND (p.type = 'PASS' OR (p.type = 'RUSH' AND (p.kne IS NULL OR p.kne != 'Y'))) THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate,
        ROUND(AVG(p.eps), 2) as avg_epa
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE p.yfog >= 99
        AND g.seas IN ({','.join(map(str, seasons_tuple))})
        AND p.off IS NOT NULL
        AND p.type IN ('PASS', 'RUSH')
        {team_filter}
    GROUP BY p.type, play_direction
    ORDER BY attempts DESC
    """
    return query(sql)

gtg_stats = get_goal_to_go_stats(tuple(seasons), tuple(selected_teams) if selected_teams else None)

if len(gtg_stats) > 0:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Success Rate by Play Type")
        gtg_type = gtg_stats.groupby('type').agg({
            'attempts': 'sum',
            'successful': 'sum',
            'avg_epa': 'mean'
        }).reset_index()
        gtg_type['success_rate'] = gtg_type['successful'] / gtg_type['attempts']

        fig_gtg = px.bar(
            gtg_type,
            x='type',
            y='success_rate',
            labels={'type': 'Play Type', 'success_rate': 'Success Rate'},
            title=f"Goal-to-Go Success Rate (n={int(gtg_type['attempts'].sum())} plays)",
            color='success_rate',
            color_continuous_scale=['#E74C3C', '#2ECC71'],
            text='success_rate'
        )
        fig_gtg.update_traces(texttemplate='%{y:.1%}', textposition='auto')
        fig_gtg.update_layout(**CHART_LAYOUT, height=350, yaxis_tickformat='.0%', showlegend=False)
        st.plotly_chart(fig_gtg, use_container_width=True)

    with col2:
        st.subheader("Rush Direction (Goal-to-Go)")
        rush_dir = gtg_stats[gtg_stats['type'] == 'RUSH'].copy()
        if len(rush_dir) > 0:
            rush_dir = rush_dir.sort_values('attempts', ascending=True)
            fig_dir = px.bar(
                rush_dir,
                y='play_direction',
                x='attempts',
                orientation='h',
                labels={'play_direction': 'Direction', 'attempts': 'Attempts'},
                title=f"Goal-to-Go Rush Attempts by Direction",
                color='attempts',
                color_continuous_scale=['#3498DB', '#2ECC71'],
                text='success_rate'
            )
            fig_dir.update_traces(texttemplate='%{text:.0%}', textposition='auto')
            fig_dir.update_layout(**CHART_LAYOUT, height=350, showlegend=False)
            st.plotly_chart(fig_dir, use_container_width=True)
        else:
            st.info("No rushing plays in goal-to-go situations for selected filters.")

# ═══════════════════════════════════════════════════════════════
# D) RED ZONE SCORING BREAKDOWN
# ═══════════════════════════════════════════════════════════════
st.header("D. Red Zone Scoring Breakdown")

@st.cache_data
def get_rz_scoring(seasons_tuple, teams_tuple=None):
    team_filter = ""
    if teams_tuple and len(teams_tuple) > 0:
        teams_str = "', '".join(teams_tuple)
        team_filter = f" AND d.tname IN ('{teams_str}')"

    drive_sql = f"""
    SELECT
        COUNT(CASE WHEN d.res = 'TD' THEN 1 END) as td_drives,
        COUNT(CASE WHEN d.res = 'FG' THEN 1 END) as fg_drives,
        COUNT(CASE WHEN d.res IN ('PUNT', 'INT', 'FUMBLE', 'DOWNS') THEN 1 END) as no_score,
        COUNT(*) as total_drives
    FROM drives d
    JOIN games g ON d.gid = g.gid
    WHERE d.yfog >= 80
        AND g.seas IN ({','.join(map(str, seasons_tuple))})
        AND d.tname IS NOT NULL
        {team_filter}
    """
    return query(drive_sql)

drive_scoring = get_rz_scoring(tuple(seasons), tuple(selected_teams) if selected_teams else None)

if len(drive_scoring) > 0:
    col1, col2, col3, col4 = st.columns(4)

    total_drives = drive_scoring['total_drives'].iloc[0]
    td_drives = drive_scoring['td_drives'].iloc[0]
    fg_drives = drive_scoring['fg_drives'].iloc[0]
    no_score = drive_scoring['no_score'].iloc[0]

    with col1:
        st.markdown(metric_card(
            "TD Drives",
            f"{int(td_drives):,}",
            f"{td_drives/total_drives:.1%} of drives",
            "", "pos"
        ), unsafe_allow_html=True)

    with col2:
        st.markdown(metric_card(
            "FG Drives",
            f"{int(fg_drives):,}",
            f"{fg_drives/total_drives:.1%} of drives",
            "", "pos"
        ), unsafe_allow_html=True)

    with col3:
        st.markdown(metric_card(
            "No Score",
            f"{int(no_score):,}",
            f"{no_score/total_drives:.1%} of drives",
            "", "neg"
        ), unsafe_allow_html=True)

    with col4:
        st.markdown(metric_card(
            "Total Drives",
            f"{int(total_drives):,}",
            "Red zone entries", "", "pos"
        ), unsafe_allow_html=True)

    score_types = ['TD', 'FG', 'No Score']
    score_counts = [td_drives, fg_drives, no_score]
    colors_pie = [COLORS['accent'], COLORS['gold'], COLORS['negative']]

    fig_pie = go.Figure(data=[go.Pie(
        labels=score_types,
        values=score_counts,
        marker=dict(colors=colors_pie),
        textposition='inside',
        textinfo='label+percent'
    )])
    fig_pie.update_layout(
        **CHART_LAYOUT,
        title="Red Zone Drive Outcomes",
        height=400
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# E) RED ZONE PLAYER PERFORMANCE
# ═══════════════════════════════════════════════════════════════
st.header("E. Red Zone Player Performance")

@st.cache_data
def get_rz_receivers(seasons_tuple, teams_tuple=None, limit=15):
    team_filter = ""
    if teams_tuple and len(teams_tuple) > 0:
        teams_str = "', '".join(teams_tuple)
        team_filter = f" AND p.off IN ('{teams_str}')"

    sql = f"""
    SELECT
        ps.trg as player_code,
        pl.pname as player_name,
        COUNT(*) as targets,
        SUM(CASE WHEN ps.comp = 1 THEN 1 ELSE 0 END) as catches,
        ROUND(100.0 * SUM(CASE WHEN ps.comp = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as catch_rate,
        SUM(ps.yds) as yards,
        SUM(CASE WHEN p.pts > 0 THEN 1 ELSE 0 END) as tds,
        ROUND(AVG(p.eps), 2) as epa_per_target
    FROM plays p
    JOIN games g ON p.gid = g.gid
    INNER JOIN passes ps ON p.pid = ps.pid
    LEFT JOIN players pl ON ps.trg = pl.player
    WHERE p.yfog >= 80
        AND g.seas IN ({','.join(map(str, seasons_tuple))})
        AND p.off IS NOT NULL
        AND ps.trg IS NOT NULL
        {team_filter}
    GROUP BY ps.trg, pl.pname
    HAVING COUNT(*) >= 3
    ORDER BY targets DESC
    LIMIT {limit}
    """
    return query(sql)

@st.cache_data
def get_rz_rushers(seasons_tuple, teams_tuple=None, limit=15):
    team_filter = ""
    if teams_tuple and len(teams_tuple) > 0:
        teams_str = "', '".join(teams_tuple)
        team_filter = f" AND p.off IN ('{teams_str}')"

    sql = f"""
    SELECT
        p.bc as player_code,
        pl.pname as player_name,
        COUNT(*) as attempts,
        SUM(p.yds) as yards,
        ROUND(AVG(p.yds), 2) as avg_yards,
        SUM(CASE WHEN p.succ = 'Y' THEN 1 ELSE 0 END) as successful,
        ROUND(100.0 * SUM(CASE WHEN p.succ = 'Y' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate,
        SUM(CASE WHEN p.pts > 0 THEN 1 ELSE 0 END) as tds,
        ROUND(AVG(p.eps), 2) as epa_per_carry
    FROM plays p
    JOIN games g ON p.gid = g.gid
    LEFT JOIN players pl ON p.bc = pl.player
    WHERE p.yfog >= 80
        AND p.type = 'RUSH'
        AND g.seas IN ({','.join(map(str, seasons_tuple))})
        AND p.off IS NOT NULL
        AND p.bc IS NOT NULL
        {team_filter}
    GROUP BY p.bc, pl.pname
    HAVING COUNT(*) >= 3
    ORDER BY attempts DESC
    LIMIT {limit}
    """
    return query(sql)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Red Zone Receivers")
    receivers = get_rz_receivers(tuple(seasons), tuple(selected_teams) if selected_teams else None, limit=12)
    if len(receivers) > 0:
        display_rec = receivers.copy()
        display_rec = display_rec[['player_name', 'targets', 'catches', 'catch_rate', 'yards', 'tds', 'epa_per_target']]
        display_rec.columns = ['Player', 'Targets', 'Catches', 'Catch %', 'Yards', 'TDs', 'EPA/Target']
        st.dataframe(display_rec, use_container_width=True, hide_index=True)
    else:
        st.info("No receiver data for selected filters.")

with col2:
    st.subheader("Top Red Zone Rushers")
    rushers = get_rz_rushers(tuple(seasons), tuple(selected_teams) if selected_teams else None, limit=12)
    if len(rushers) > 0:
        display_rush = rushers.copy()
        display_rush = display_rush[['player_name', 'attempts', 'yards', 'avg_yards', 'success_rate', 'tds', 'epa_per_carry']]
        display_rush.columns = ['Player', 'Attempts', 'Yards', 'Avg/Carry', 'Success %', 'TDs', 'EPA/Carry']
        st.dataframe(display_rush, use_container_width=True, hide_index=True)
    else:
        st.info("No rusher data for selected filters.")

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(page_footer(), unsafe_allow_html=True)
