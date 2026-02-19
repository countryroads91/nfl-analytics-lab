"""Market & Closing Line Value Lab - Betting Analysis Dashboard"""
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

st.set_page_config(page_title="Market & CLV Lab", layout="wide", initial_sidebar_state="expanded")

# Apply shared branding CSS
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

st.title("📊 Market & Closing Line Value Lab")
st.markdown("Comprehensive betting analysis: ATS records, O/U accuracy, spread calibration, and situational splits.")

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
with st.sidebar:
    st.header("Filters")

    season_range = st.slider(
        "Season Range",
        min_value=min(SEASON_RANGE),
        max_value=max(SEASON_RANGE),
        value=(2010, 2019),
        step=1
    )

    teams_list = query("SELECT DISTINCT v FROM games WHERE v IS NOT NULL ORDER BY v").iloc[:, 0].tolist()
    selected_teams = st.multiselect("Teams (Leave empty for all)", teams_list, default=[])

    game_perspective = st.radio("Game Perspective", ["All", "Home", "Away"], horizontal=True)

    surface_filter = st.multiselect("Surface", ["GRASS", "ARTIF", "DOME"], default=[])

    temp_range = st.slider("Temperature Range (°F)", -20, 120, (-20, 120), step=5)

    week_range = st.slider("Week Range", 1, 17, (1, 17), step=1)


# ============================================================================
# LOAD AND PROCESS DATA
# ============================================================================
@st.cache_data
def load_games_data(season_min, season_max, week_min, week_max, temp_min, temp_max):
    """Load and process games data with all betting metrics."""
    sql = """
    SELECT
        gid, seas, wk, day, v, h, stad, temp, humd, wspd, wdir, cond, surf,
        ou, sprv, ptsv, ptsh
    FROM games
    WHERE seas >= ? AND seas <= ?
      AND wk >= ? AND wk <= ?
      AND (temp IS NULL OR (temp >= ? AND temp <= ?))
    """
    df = query(sql, [season_min, season_max, week_min, week_max, temp_min, temp_max])

    # Calculate betting metrics
    df['actual_margin'] = df['ptsh'] - df['ptsv']  # Positive = home win
    df['spread_result'] = df['actual_margin'] + df['sprv']  # Positive = home covers
    df['total_pts'] = df['ptsv'] + df['ptsh']
    df['ou_result'] = df['total_pts'] - df['ou']  # Positive = over hits

    # Weather categorization
    def categorize_weather(temp):
        if pd.isna(temp):
            return "Unknown"
        if temp < 35:
            return "Cold"
        elif temp < 55:
            return "Cool"
        elif temp < 75:
            return "Moderate"
        else:
            return "Warm"

    df['weather_cat'] = df['temp'].apply(categorize_weather)

    # Dome identification (simplified)
    df['is_dome'] = df['cond'].astype(str).str.contains("DOME|INDOOR", case=False, na=False)

    return df

games_df = load_games_data(season_range[0], season_range[1], temp_range[0], temp_range[1],
                          week_range[0], week_range[1])

# Apply team filters
if selected_teams:
    if game_perspective == "Home":
        games_df = games_df[games_df['h'].isin(selected_teams)]
    elif game_perspective == "Away":
        games_df = games_df[games_df['v'].isin(selected_teams)]
    else:
        games_df = games_df[(games_df['h'].isin(selected_teams)) | (games_df['v'].isin(selected_teams))]

if surface_filter:
    games_df = games_df[games_df['surf'].isin(surface_filter)]

# ============================================================================
# METRIC CARDS
# ============================================================================
col1, col2, col3, col4, col5 = st.columns(5)

total_games = len(games_df)
home_ats_pct = (games_df['spread_result'] > 0).sum() / total_games * 100 if total_games > 0 else 0
away_ats_pct = (games_df['spread_result'] < 0).sum() / total_games * 100 if total_games > 0 else 0
over_pct = (games_df['ou_result'] > 0).sum() / total_games * 100 if total_games > 0 else 0
avg_spread_error = games_df['spread_result'].abs().mean()

with col1:
    st.markdown(metric_card("Total Games", f"{total_games}"), unsafe_allow_html=True)

with col2:
    st.markdown(metric_card("Home ATS%", f"{home_ats_pct:.1f}%"), unsafe_allow_html=True)

with col3:
    st.markdown(metric_card("Away ATS%", f"{away_ats_pct:.1f}%"), unsafe_allow_html=True)

with col4:
    st.markdown(metric_card("Over%", f"{over_pct:.1f}%"), unsafe_allow_html=True)

with col5:
    st.markdown(metric_card("Avg Spread Error", f"{avg_spread_error:.2f}"), unsafe_allow_html=True)

st.divider()

# ============================================================================
# SECTION A: ATS ANALYSIS
# ============================================================================
st.header("A) Against the Spread (ATS) Analysis")

col_a1, col_a2 = st.columns(2)

with col_a1:
    # Home/Away ATS records by team
    ats_records = []
    for team in sorted(games_df['h'].unique()):
        home_games = games_df[games_df['h'] == team]
        away_games = games_df[games_df['v'] == team]

        if len(home_games) > 0:
            home_wins = (home_games['spread_result'] > 0).sum()
            home_pushes = (home_games['spread_result'] == 0).sum()
            ats_records.append({
                'Team': team,
                'Perspective': 'Home',
                'Games': len(home_games),
                'ATS_Wins': home_wins,
                'Win%': home_wins / len(home_games) * 100,
                'Pushes': home_pushes
            })

        if len(away_games) > 0:
            away_wins = (away_games['spread_result'] < 0).sum()
            away_pushes = (away_games['spread_result'] == 0).sum()
            ats_records.append({
                'Team': team,
                'Perspective': 'Away',
                'Games': len(away_games),
                'ATS_Wins': away_wins,
                'Win%': away_wins / len(away_games) * 100,
                'Pushes': away_pushes
            })

        # Overall
        all_games = pd.concat([home_games, away_games])
        if len(all_games) > 0:
            overall_wins = ((all_games['h'] == team) & (all_games['spread_result'] > 0)).sum() + \
                          ((all_games['v'] == team) & (all_games['spread_result'] < 0)).sum()
            overall_pushes = (all_games['spread_result'] == 0).sum()
            ats_records.append({
                'Team': team,
                'Perspective': 'Overall',
                'Games': len(all_games),
                'ATS_Wins': overall_wins,
                'Win%': overall_wins / len(all_games) * 100,
                'Pushes': overall_pushes
            })

    ats_df = pd.DataFrame(ats_records).sort_values(['Team', 'Perspective'])
    # Apply team full names
    ats_df['Team'] = ats_df['Team'].map(lambda x: TEAM_FULL_NAMES.get(x, x))

    st.subheader("ATS Record by Team & Perspective", help="Home/Away/Overall ATS records with win % and pushes")
    st.dataframe(
        ats_df.style.format({'Win%': '{:.1f}%', 'ATS_Wins': '{:.0f}'}),
        use_container_width=True,
        height=400
    )

with col_a2:
    # ATS Win% bar chart - need to recreate from original team codes since we mapped them
    ats_summary_orig = pd.DataFrame(ats_records).sort_values(['Team', 'Perspective'])
    ats_summary = ats_summary_orig[ats_summary_orig['Perspective'] == 'Overall'].sort_values('Win%', ascending=False).head(15)
    ats_summary['Team Full'] = ats_summary['Team'].map(lambda x: TEAM_FULL_NAMES.get(x, x))

    fig_ats = go.Figure()

    colors_list = [
        COLORS['positive'] if x >= 55 else COLORS['negative'] if x <= 45 else COLORS['neutral']
        for x in ats_summary['Win%']
    ]

    fig_ats.add_trace(go.Bar(
        x=ats_summary['Win%'],
        y=ats_summary['Team Full'],
        orientation='h',
        marker=dict(color=colors_list),
        text=[f"{w:.1f}% (n={g})" for w, g in zip(ats_summary['Win%'], ats_summary['Games'])],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>ATS Win%: %{x:.1f}%<extra></extra>'
    ))

    fig_ats.update_layout(**CHART_LAYOUT,
        title="Top 15 Teams by ATS Win%",
        xaxis_title="ATS Win %",
        yaxis_title="Team",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig_ats, use_container_width=True)

# Cover margin distribution
st.subheader("Cover Margin Distribution", help="Distribution of how much teams beat/missed the spread by")
fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(
    x=games_df['spread_result'],
    nbinsx=40,
    marker=dict(color=COLORS['accent'], opacity=0.7),
    name='Cover Margin'
))
fig_hist.add_vline(x=0, line_dash="dash", line_color=COLORS['warn'], annotation_text="Break-even (0)")

fig_hist.update_layout(**CHART_LAYOUT,
    title="Distribution of Spread Results (Positive = Home Covers)",
    xaxis_title="Cover Margin (points)",
    yaxis_title="Frequency",
    height=350,
    showlegend=False
)
st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# ============================================================================
# SECTION B: OVER/UNDER ANALYSIS
# ============================================================================
st.header("B) Over/Under Analysis")

col_b1, col_b2 = st.columns(2)

with col_b1:
    # O/U by team
    ou_records = []
    for team in sorted(games_df['h'].unique()):
        home_games = games_df[games_df['h'] == team]
        away_games = games_df[games_df['v'] == team]
        all_games = pd.concat([home_games, away_games])

        if len(all_games) > 0:
            overs = (all_games['ou_result'] > 0).sum()
            ou_records.append({
                'Team': team,
                'Games': len(all_games),
                'Overs': overs,
                'Over%': overs / len(all_games) * 100,
                'Avg Total': all_games['total_pts'].mean(),
                'Avg OU Line': all_games['ou'].mean()
            })

    ou_df = pd.DataFrame(ou_records).sort_values('Over%', ascending=False)
    # Apply team full names
    ou_df['Team'] = ou_df['Team'].map(lambda x: TEAM_FULL_NAMES.get(x, x))

    st.subheader("O/U Records by Team", help="Over hit percentage and average total points vs line")
    st.dataframe(
        ou_df.style.format({'Over%': '{:.1f}%', 'Avg Total': '{:.1f}', 'Avg OU Line': '{:.1f}'}),
        use_container_width=True,
        height=400
    )

with col_b2:
    # O/U accuracy scatter
    fig_scatter = go.Figure()

    fig_scatter.add_trace(go.Scatter(
        x=games_df['ou'],
        y=games_df['total_pts'],
        mode='markers',
        marker=dict(
            color=games_df['ou_result'],
            colorscale=[[0, COLORS['negative']], [0.5, COLORS['neutral']], [1, COLORS['positive']]],
            size=5,
            opacity=0.6,
            colorbar=dict(title="O/U Result")
        ),
        text=[f"Line: {line:.1f}<br>Actual: {actual:.1f}" for line, actual in zip(games_df['ou'], games_df['total_pts'])],
        hovertemplate='%{text}<extra></extra>'
    ))

    # Add regression line (y=x means perfect calibration)
    min_val = min(games_df['ou'].min(), games_df['total_pts'].min())
    max_val = max(games_df['ou'].max(), games_df['total_pts'].max())
    fig_scatter.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        name='Perfect Calibration',
        line=dict(color=COLORS['warn'], dash='dash', width=2)
    ))

    fig_scatter.update_layout(**CHART_LAYOUT,
        title="O/U Line Accuracy (Actual vs Predicted Total)",
        xaxis_title="O/U Line",
        yaxis_title="Actual Total Points",
        height=400,
        hovermode='closest'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# O/U by season
st.subheader("O/U Hit Rate by Season")
ou_season = games_df.groupby('seas').agg({
    'ou_result': ['count', lambda x: (x > 0).sum()]
}).reset_index()
ou_season.columns = ['Season', 'Games', 'Overs']
ou_season['Over%'] = (ou_season['Overs'] / ou_season['Games'] * 100)

fig_season = go.Figure()
fig_season.add_trace(go.Bar(
    x=ou_season['Season'],
    y=ou_season['Over%'],
    marker=dict(color=COLORS['accent']),
    text=[f"{x:.1f}% (n={g})" for x, g in zip(ou_season['Over%'], ou_season['Games'])],
    textposition='auto'
))
fig_season.add_hline(y=50, line_dash="dash", line_color=COLORS['warn'], annotation_text="50% (Fair Price)")

fig_season.update_layout(**CHART_LAYOUT,
    title="Over/Under Hit Rate by Season",
    xaxis_title="Season",
    yaxis_title="Over Hit %",
    height=350,
    showlegend=False
)
st.plotly_chart(fig_season, use_container_width=True)

st.divider()

# ============================================================================
# SECTION C: SPREAD ACCURACY & CALIBRATION
# ============================================================================
st.header("C) Spread Accuracy & Calibration")

# Create spread buckets
def bucket_spread(spread):
    if pd.isna(spread):
        return "Unknown"
    spread = float(spread)
    if spread <= -14:
        return "-14 or more"
    elif spread <= -10:
        return "-10 to -13.5"
    elif spread <= -7:
        return "-7 to -9.5"
    elif spread <= -3:
        return "-3 to -6.5"
    elif spread < 0:
        return "-1 to -2.5"
    elif spread == 0:
        return "PK"
    elif spread < 3:
        return "+1 to +2.5"
    elif spread < 7:
        return "+3 to +6.5"
    elif spread < 10:
        return "+7 to +9.5"
    else:
        return "+10 or more"

games_df['spread_bucket'] = games_df['sprv'].apply(bucket_spread)

col_c1, col_c2 = st.columns(2)

with col_c1:
    # Spread bucket outcomes
    spread_calibration = games_df.groupby('spread_bucket').agg({
        'spread_result': ['count', lambda x: (x > 0).sum(), lambda x: (x < 0).sum()]
    }).reset_index()
    spread_calibration.columns = ['Spread Bucket', 'Total Games', 'Home Covers', 'Away Covers']
    spread_calibration['Home Win%'] = (spread_calibration['Home Covers'] / spread_calibration['Total Games'] * 100)

    # Order the buckets properly
    bucket_order = ["-14 or more", "-10 to -13.5", "-7 to -9.5", "-3 to -6.5", "-1 to -2.5",
                   "PK", "+1 to +2.5", "+3 to +6.5", "+7 to +9.5", "+10 or more"]
    spread_calibration['Spread Bucket'] = pd.Categorical(spread_calibration['Spread Bucket'],
                                                         categories=bucket_order, ordered=True)
    spread_calibration = spread_calibration.sort_values('Spread Bucket')

    st.subheader("Spread Calibration by Range", help="Win % by spread range (should approach 50%)")
    st.dataframe(
        spread_calibration.style.format({'Home Win%': '{:.1f}%'}),
        use_container_width=True,
        height=350
    )

with col_c2:
    # Calibration chart
    fig_calib = go.Figure()
    fig_calib.add_trace(go.Bar(
        x=spread_calibration['Spread Bucket'],
        y=spread_calibration['Home Win%'],
        marker=dict(color=COLORS['accent']),
        text=[f"{x:.1f}% (n={n})" for x, n in zip(spread_calibration['Home Win%'],
                                                   spread_calibration['Total Games'])],
        textposition='auto'
    ))
    fig_calib.add_hline(y=50, line_dash="dash", line_color=COLORS['warn'],
                       annotation_text="Perfect Calibration (50%)")

    fig_calib.update_layout(**CHART_LAYOUT,
        title="Home Win % by Spread Range",
        xaxis_title="Spread Range",
        yaxis_title="Home Win %",
        height=400,
        showlegend=False
    )
    st.plotly_chart(fig_calib, use_container_width=True)

st.divider()

# ============================================================================
# SECTION D: SITUATIONAL BETTING SPLITS
# ============================================================================
st.header("D) Situational Betting Splits")

col_d1, col_d2 = st.columns(2)

with col_d1:
    st.subheader("Weather Impact on ATS", help="Performance in different weather conditions")
    weather_ats = games_df.groupby('weather_cat').agg({
        'spread_result': ['count', lambda x: (x > 0).sum()]
    }).reset_index()
    weather_ats.columns = ['Weather', 'Games', 'Home Covers']
    weather_ats['Home Win%'] = (weather_ats['Home Covers'] / weather_ats['Games'] * 100)
    weather_ats = weather_ats[weather_ats['Games'] >= 5]  # Filter out small samples

    fig_weather = go.Figure()
    fig_weather.add_trace(go.Bar(
        x=weather_ats['Weather'],
        y=weather_ats['Home Win%'],
        marker=dict(color=COLORS['accent']),
        text=[f"{x:.1f}% (n={g})" for x, g in zip(weather_ats['Home Win%'], weather_ats['Games'])],
        textposition='auto'
    ))
    fig_weather.add_hline(y=50, line_dash="dash", line_color=COLORS['warn'])

    fig_weather.update_layout(**CHART_LAYOUT,
        title="Home ATS% by Weather Condition",
        xaxis_title="Weather",
        yaxis_title="Home Win %",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig_weather, use_container_width=True)

with col_d2:
    st.subheader("Dome vs Open Air", help="Indoor vs outdoor performance")
    games_df['venue_type'] = games_df['is_dome'].map({True: 'Dome/Indoor', False: 'Open Air'})
    venue_ats = games_df.groupby('venue_type').agg({
        'spread_result': ['count', lambda x: (x > 0).sum()]
    }).reset_index()
    venue_ats.columns = ['Venue', 'Games', 'Home Covers']
    venue_ats['Home Win%'] = (venue_ats['Home Covers'] / venue_ats['Games'] * 100)

    fig_venue = go.Figure()
    fig_venue.add_trace(go.Bar(
        x=venue_ats['Venue'],
        y=venue_ats['Home Win%'],
        marker=dict(color=[COLORS['accent'], COLORS['accent2']]),
        text=[f"{x:.1f}% (n={g})" for x, g in zip(venue_ats['Home Win%'], venue_ats['Games'])],
        textposition='auto'
    ))
    fig_venue.add_hline(y=50, line_dash="dash", line_color=COLORS['warn'])

    fig_venue.update_layout(**CHART_LAYOUT,
        title="Home ATS% by Venue Type",
        xaxis_title="Venue Type",
        yaxis_title="Home Win %",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig_venue, use_container_width=True)

# Season trends
st.subheader("Season Trends in ATS Performance")
season_ats = games_df.groupby('seas').agg({
    'spread_result': ['count', lambda x: (x > 0).sum()]
}).reset_index()
season_ats.columns = ['Season', 'Games', 'Home Covers']
season_ats['Home Win%'] = (season_ats['Home Covers'] / season_ats['Games'] * 100)

fig_season_ats = go.Figure()
fig_season_ats.add_trace(go.Scatter(
    x=season_ats['Season'],
    y=season_ats['Home Win%'],
    mode='lines+markers',
    name='Home ATS%',
    line=dict(color=COLORS['accent'], width=3),
    marker=dict(size=8)
))
fig_season_ats.add_hline(y=50, line_dash="dash", line_color=COLORS['warn'], annotation_text="50% (Fair Price)")

fig_season_ats.update_layout(**CHART_LAYOUT,
    title="Home ATS Performance by Season",
    xaxis_title="Season",
    yaxis_title="Home ATS Win %",
    height=350,
    hovermode='x unified'
)
st.plotly_chart(fig_season_ats, use_container_width=True)

st.info("""
    **Interpretation Guide:**
    - **ATS%**: Percentage of games where a side beat the spread. ~55% indicates edge.
    - **O/U**: Higher percentage means more games go over; 50% is equilibrium.
    - **Spread Error**: Average deviation from line. Smaller = more accurate line-setting.
    - **Calibration**: When Home Win% at each spread range hovers around 50%, the market is well-calibrated.
    - **Situational Splits**: Look for persistent edges in specific conditions (weather, dome, etc).
""")

st.markdown(page_footer(), unsafe_allow_html=True)
