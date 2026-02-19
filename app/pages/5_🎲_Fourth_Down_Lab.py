"""Fourth Down Lab - High-Leverage Decisions, Risk Analysis & Decision Theory"""
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

st.set_page_config(page_title="Fourth Down Lab", layout="wide", initial_sidebar_state="expanded")
st.markdown(SHARED_CSS, unsafe_allow_html=True)

st.title("🎲 Fourth Down Lab")
st.markdown("High-Leverage Decisions, Risk Analysis & Historical Success Rates")

st.markdown('<div class="ssa-info"><strong>Why this matters:</strong> Fourth down decisions are among the highest-leverage moments in football. Bettors profit by understanding optimal go-for-it thresholds. This dashboard reveals how teams actually decide vs. game theory optimal, success rates by situation (field position, yards to go, score differential), and historical aggressiveness. Essential for live betting and game script prediction.</div>', unsafe_allow_html=True)

st.divider()

# Team code to full name mapping
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

def team_to_full_name(team_code):
    """Convert team code to full name, with fallback to code itself."""
    return TEAM_FULL_NAMES.get(team_code, team_code)

# Sidebar filters
st.sidebar.header("Filters")
season_range = st.sidebar.slider("Season Range", min_value=2000, max_value=2019, value=(2010, 2019), step=1)
selected_teams = st.sidebar.multiselect("Select Teams (blank=all)",
                                        options=sorted(pd.Series(TEAM_COLORS.keys()).unique()),
                                        default=[])

# ==================== A) FOURTH DOWN DECISION OVERVIEW ====================
st.header("A) Fourth Down Decision Overview")

st.markdown('<div class="ssa-info"><strong>Metric guide:</strong> Go-For-It Rate = % of 4th downs where team attempts play instead of punt/FG. Success Rate = plays that achieve first down or TD. Score differential helps explain aggressiveness (losing teams go for it more).</div>', unsafe_allow_html=True)

@st.cache_data
def load_fourth_down_decisions(season_start, season_end, team_filter):
    """Load fourth down data with explicit filter parameters.

    Args:
        season_start: Start season
        season_end: End season
        team_filter: Tuple of team codes to filter on (empty tuple = all teams)
    """
    sql = """
    SELECT
        p.gid,
        g.seas AS season,
        p.off AS team,
        p.type,
        p.dwn,
        p.ytg,
        p.yfog,
        p.qtr,
        p.succ,
        p.fd,
        p.ptso,
        p.ptsd,
        p.pid
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE p.dwn = 4 AND g.seas >= ? AND g.seas <= ?
    ORDER BY g.seas DESC, p.gid
    """
    params = [season_start, season_end]

    df = query(sql, params)

    # Apply team filter if specified
    if team_filter:
        df = df[df['team'].isin(team_filter)]

    return df

# Convert selected_teams list to tuple for hashability in cache
team_filter_tuple = tuple(selected_teams) if selected_teams else ()
fourth_downs = load_fourth_down_decisions(season_range[0], season_range[1], team_filter_tuple)

if not fourth_downs.empty:
    # Classify decisions
    fourth_downs['decision'] = fourth_downs['type'].apply(
        lambda x: 'Punt' if x == 'PUNT' else ('Field Goal' if x == 'FGXP' else 'Go for It')
    )

    # Score differential - USE ptso and ptsd from plays table (not games)
    fourth_downs['score_diff'] = fourth_downs['ptso'] - fourth_downs['ptsd']

    # Field position buckets
    def field_pos_bucket(yfog):
        if pd.isna(yfog):
            return 'Unknown'
        if yfog <= 25:
            return 'Own 1-25'
        elif yfog <= 50:
            return 'Own 26-50'
        elif yfog <= 75:
            return 'Opp 49-25'
        else:
            return 'Opp 24-1'

    fourth_downs['field_pos_bucket'] = fourth_downs['yfog'].apply(field_pos_bucket)

    # Metric cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card("Total 4th Downs", str(len(fourth_downs))), unsafe_allow_html=True)
    with col2:
        go_for_it_rate = (len(fourth_downs[fourth_downs['decision'] == 'Go for It']) / len(fourth_downs) * 100)
        st.markdown(metric_card("Go-For-It Rate", f"{go_for_it_rate:.1f}%"), unsafe_allow_html=True)
    with col3:
        go_for_it_success = fourth_downs[fourth_downs['decision'] == 'Go for It']
        if len(go_for_it_success) > 0:
            success_pct = (len(go_for_it_success[go_for_it_success['succ'] == 'Y']) / len(go_for_it_success) * 100)
            st.markdown(metric_card("Go-For-It Success %", f"{success_pct:.1f}%"), unsafe_allow_html=True)
    with col4:
        punts = fourth_downs[fourth_downs['decision'] == 'Punt']
        st.markdown(metric_card("Total Punts", str(len(punts))), unsafe_allow_html=True)

    # Decision rates by field position
    decision_by_fp = fourth_downs.groupby(['field_pos_bucket', 'decision']).size().unstack(fill_value=0)
    decision_pct = decision_by_fp.div(decision_by_fp.sum(axis=1), axis=0) * 100

    fig = px.bar(
        decision_pct.reset_index().melt(id_vars='field_pos_bucket', var_name='decision', value_name='percentage'),
        x='field_pos_bucket',
        y='percentage',
        color='decision',
        title="4th Down Decision Rates by Field Position",
        barmode='stack',
        labels={'field_pos_bucket': 'Field Position', 'percentage': 'Percentage (%)'},
        color_discrete_map={
            'Punt': COLORS['negative'],
            'Field Goal': COLORS['warn'],
            'Go for It': COLORS['positive']
        }
    )
    fig.update_layout(**CHART_LAYOUT, height=450)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==================== B) GO-FOR-IT SUCCESS RATE ====================
st.header("B) Go-For-It Success Rate by Yards to Go")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Success rate should decrease with yards to go. Odds drop significantly at 3+ yards. Teams most successful on 4th-and-1 and 4th-and-2 (>70% success). Use to evaluate when aggressive calls are justified.</div>', unsafe_allow_html=True)

go_for_it_plays = fourth_downs[fourth_downs['decision'] == 'Go for It'].copy()

if len(go_for_it_plays) > 0:
    # Cap ytg at 5+ for grouping
    go_for_it_plays['ytg_bucket'] = go_for_it_plays['ytg'].apply(
        lambda x: f'{x}' if x <= 5 else '5+'
    )

    # Compute success: succ is VARCHAR ('Y' or NULL from plays table)
    success_by_ytg = go_for_it_plays.groupby('ytg_bucket').agg({
        'succ': lambda x: (x == 'Y').sum(),  # Count successes
        'fd': 'sum'
    }).reset_index()
    success_by_ytg['total_attempts'] = go_for_it_plays.groupby('ytg_bucket').size().values
    success_by_ytg.columns = ['ytg_bucket', 'success_count', 'fd_count', 'total_attempts']
    success_by_ytg['success_rate'] = (success_by_ytg['success_count'] / success_by_ytg['total_attempts'] * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=success_by_ytg['ytg_bucket'],
        y=success_by_ytg['success_rate'],
        marker=dict(color=success_by_ytg['success_rate'], colorscale=[(0, COLORS['negative']), (1, COLORS['positive'])]),
        text=[f"{row['success_rate']:.1f}%<br>n={int(row['total_attempts'])}" for _, row in success_by_ytg.iterrows()],
        textposition='outside',
        hovertemplate='<b>Yards to Go: %{x}</b><br>Success Rate: %{customdata[0]:.1f}%<br>Attempts: %{customdata[1]}<extra></extra>',
        customdata=success_by_ytg[['success_rate', 'total_attempts']].values
    ))
    fig.update_layout(**CHART_LAYOUT, height=450,
        title="Go-For-It Success Rate by Yards to Go",
        xaxis_title="Yards to Go",
        yaxis_title="Success Rate (%)",
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==================== C) FOURTH DOWN AGGRESSIVENESS RANKING ====================
st.header("C) Fourth Down Aggressiveness Ranking")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Reasonable 4th downs = ytg <= 5 AND past midfield (yfog >= 40). Aggressive teams go for it >40% of time. Shows coaching philosophy independent of score/time pressure.</div>', unsafe_allow_html=True)

# "Reasonable" 4th downs: ytg <= 5, yfog >= 40 (past midfield)
reasonable_4th = fourth_downs[
    (fourth_downs['ytg'] <= 5) &
    (fourth_downs['yfog'] >= 40)
].copy()

if len(reasonable_4th) > 0:
    aggression_by_team = reasonable_4th.groupby(['season', 'team']).agg({
        'decision': lambda x: (x == 'Go for It').sum() / len(x) * 100,
        'pid': 'count'
    }).reset_index()
    aggression_by_team.columns = ['season', 'team', 'go_for_it_rate', 'reasonable_4th_count']

    # Get latest season
    latest_aggression = aggression_by_team[aggression_by_team['season'] == season_range[1]].sort_values('go_for_it_rate', ascending=False)

    if not latest_aggression.empty:
        # Success rate for those go-for-its
        go_for_it_by_team = reasonable_4th[reasonable_4th['decision'] == 'Go for It'].groupby(['season', 'team']).agg({
            'succ': lambda x: (x == 'Y').sum()
        }).reset_index()
        go_for_it_by_team['attempt_count'] = reasonable_4th[reasonable_4th['decision'] == 'Go for It'].groupby(['season', 'team']).size().values
        go_for_it_by_team.columns = ['season', 'team', 'success_count', 'attempt_count']
        go_for_it_by_team['success_rate'] = (go_for_it_by_team['success_count'] / go_for_it_by_team['attempt_count'] * 100).round(1)

        latest_aggression = latest_aggression.merge(
            go_for_it_by_team[go_for_it_by_team['season'] == season_range[1]][['team', 'success_rate']],
            on='team',
            how='left'
        )

        # Convert team codes to full names for display
        latest_aggression_display = latest_aggression.copy()
        latest_aggression_display['team_full_name'] = latest_aggression_display['team'].apply(team_to_full_name)

        fig = px.scatter(
            latest_aggression_display,
            x='go_for_it_rate',
            y='success_rate',
            text='team_full_name',
            title=f"Go-For-It Aggressiveness vs Success Rate ({season_range[1]})<br><sub>Reasonable 4th downs: ytg ≤ 5, yfog ≥ 40</sub>",
            labels={'go_for_it_rate': 'Go-For-It Rate (%)', 'success_rate': 'Success Rate (%)'},
            size='reasonable_4th_count',
            size_max=40
        )
        fig.update_traces(textposition='top center')
        fig.update_layout(**CHART_LAYOUT, height=500, hovermode='closest')
        st.plotly_chart(fig, use_container_width=True)

        # Ranking table
        st.subheader("Aggressiveness Rankings")
        ranking_table = latest_aggression[['team', 'go_for_it_rate', 'success_rate', 'reasonable_4th_count']].sort_values('go_for_it_rate', ascending=False)
        ranking_table['team'] = ranking_table['team'].apply(team_to_full_name)
        ranking_table.columns = ['Team', 'Go-For-It Rate (%)', 'Success Rate (%)', 'Opportunities']
        st.dataframe(ranking_table, use_container_width=True, hide_index=True)

st.divider()

# ==================== D) DECISION ANALYSIS BY SCORE & TIME ====================
st.header("D) Decision Analysis by Score & Time")

st.markdown('<div class="ssa-info"><strong>What to look for:</strong> Losing teams are more aggressive. Tight games show balanced decision-making. Blowouts show conservative tendencies (punting when close, going for it when far behind). Quarter 4 shows more aggressiveness.</div>', unsafe_allow_html=True)

# Score differential buckets
fourth_downs['score_bucket'] = pd.cut(
    fourth_downs['score_diff'],
    bins=[-100, -8, -1, 1, 8, 100],
    labels=['Losing 8+', 'Losing 1-7', 'Tied', 'Winning 1-7', 'Winning 8+']
)

# Heatmap: score differential x quarter
decision_heatmap = fourth_downs.groupby(['score_bucket', 'qtr']).agg({
    'decision': lambda x: (x == 'Go for It').sum() / len(x) * 100 if len(x) > 0 else 0
}).reset_index()
decision_heatmap.columns = ['score_bucket', 'qtr', 'go_for_it_rate']

# Pivot
pivot_data = decision_heatmap.pivot(index='score_bucket', columns='qtr', values='go_for_it_rate')

fig = px.imshow(
    pivot_data,
    title="Go-For-It Rate by Score Differential & Quarter",
    labels=dict(x='Quarter', y='Score Differential', color='Go-For-It Rate (%)'),
    color_continuous_scale='RdYlGn',
    aspect='auto'
)
fig.update_layout(**CHART_LAYOUT, height=400)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==================== E) WHAT-IF SIMULATOR ====================
st.header("E) What-If Simulator")

st.markdown('<div class="ssa-info"><strong>How to use:</strong> Enter a game situation (field position, yards to go, quarter, score) to see historical outcomes for similar 4th down plays. Use to estimate go-for-it success probability and expected value.</div>', unsafe_allow_html=True)

st.markdown("**Enter a game situation to see historical outcomes for similar 4th downs:**")

col1, col2, col3, col4 = st.columns(4)
with col1:
    sim_yfog = st.number_input("Yards from Own Goal", value=65, min_value=1, max_value=100)
with col2:
    sim_ytg = st.number_input("Yards to Go", value=2, min_value=1, max_value=15)
with col3:
    sim_qtr = st.selectbox("Quarter", [1, 2, 3, 4])
with col4:
    sim_score_diff = st.number_input("Score Differential (Offense)", value=-3, min_value=-50, max_value=50)

# Filter similar situations
tolerance_yfog = 10
tolerance_ytg = 2

similar_4ths = fourth_downs[
    (fourth_downs['yfog'] >= sim_yfog - tolerance_yfog) &
    (fourth_downs['yfog'] <= sim_yfog + tolerance_yfog) &
    (fourth_downs['ytg'] >= max(1, sim_ytg - tolerance_ytg)) &
    (fourth_downs['ytg'] <= sim_ytg + tolerance_ytg)
].copy()

if len(similar_4ths) > 0:
    st.subheader(f"Historical Data for Similar Situations (n={len(similar_4ths)})")

    col1, col2, col3 = st.columns(3)

    # Go-for-it success
    go_for_it_similar = similar_4ths[similar_4ths['decision'] == 'Go for It']
    if len(go_for_it_similar) > 0:
        go_success_pct = (len(go_for_it_similar[go_for_it_similar['succ'] == 'Y']) / len(go_for_it_similar) * 100)
        with col1:
            st.markdown(metric_card("Go-For-It Success %", f"{go_success_pct:.1f}%", sub=f"n={len(go_for_it_similar)}"), unsafe_allow_html=True)

    # Punt data
    punt_similar = similar_4ths[similar_4ths['decision'] == 'Punt']
    if len(punt_similar) > 0:
        with col2:
            st.markdown(metric_card("Total Punts", str(len(punt_similar)), sub="Similar situations"), unsafe_allow_html=True)

    # FG data
    fg_similar = similar_4ths[similar_4ths['decision'] == 'Field Goal']
    if len(fg_similar) > 0:
        with col3:
            st.markdown(metric_card("Total FG Attempts", str(len(fg_similar)), sub="Similar situations"), unsafe_allow_html=True)

    # Decision distribution
    decision_dist = similar_4ths['decision'].value_counts()
    fig = px.pie(
        values=decision_dist.values,
        names=decision_dist.index,
        title="Decision Distribution in Similar Situations",
        color_discrete_map={
            'Go for It': COLORS['positive'],
            'Punt': COLORS['negative'],
            'Field Goal': COLORS['warn']
        }
    )
    fig.update_layout(**CHART_LAYOUT, height=400)
    st.plotly_chart(fig, use_container_width=True)

    # Show sample plays
    with st.expander("View Sample Similar Plays"):
        sample_cols = ['season', 'team', 'decision', 'ytg', 'yfog', 'qtr', 'succ', 'score_diff']
        sample_plays = similar_4ths[sample_cols].head(20).copy()
        sample_plays['team'] = sample_plays['team'].apply(team_to_full_name)
        sample_plays.columns = ['Season', 'Team', 'Decision', 'YTG', 'YFOG', 'Quarter', 'Success', 'Score Diff']
        st.dataframe(sample_plays, use_container_width=True, hide_index=True)
else:
    st.info(f"No similar situations found. Try adjusting YFOG ({sim_yfog}) or YTG ({sim_ytg})")

st.markdown(page_footer(), unsafe_allow_html=True)
