"""Efficiency Explorer - EPA, Success Rate, and Explosive Plays Analysis"""
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

st.set_page_config(page_title="Efficiency Explorer", layout="wide", initial_sidebar_state="expanded")
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

st.title("⚡ Efficiency Explorer")
st.markdown("EPA, success rate, and explosive play analysis across teams, plays, and situations.")

# ============================================================================
# SIDEBAR FILTERS
# ============================================================================
with st.sidebar:
    st.header("Filters")

    season_select = st.selectbox("Season", options=sorted(SEASON_RANGE, reverse=True), index=0)

    play_type_select = st.selectbox(
        "Play Type",
        options=["All", "PASS", "RUSH"],
        help="Filter by play type"
    )

    down_select = st.multiselect("Down", [1, 2, 3, 4], default=[1, 2, 3, 4])

    situation_select = st.multiselect(
        "Situation",
        ["All Plays", "Red Zone (80+ yfog)", "Goal-to-Go (99+ yfog)", "Late & Close", "Shotgun", "No Huddle"],
        default=["All Plays"]
    )

# ============================================================================
# LOAD AND CACHE DATA
# ============================================================================
@st.cache_data
def load_plays_data(season_select):
    """Load plays with game context."""
    sql = """
    SELECT
        p.gid, p.pid, p.off, p.def, p.type, p.dseq, p.qtr, p.dwn, p.ytg, p.yfog,
        p.yds, p.succ, p.fd, p.sg, p.nh, p.pts, p.epa,
        g.seas, g.v, g.h, g.ptsv, g.ptsh
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE g.seas = ? AND p.epa IS NOT NULL
    """
    return query(sql, [season_select])

plays_df = load_plays_data(season_select)

# Apply filters
if play_type_select != "All":
    plays_df = plays_df[plays_df['type'] == play_type_select]

if down_select:
    plays_df = plays_df[plays_df['dwn'].isin(down_select)]

# Situation filters
if "All Plays" not in situation_select:
    mask = pd.Series([False] * len(plays_df), index=plays_df.index)

    if "Red Zone (80+ yfog)" in situation_select:
        mask |= (plays_df['yfog'] >= 80)
    if "Goal-to-Go (99+ yfog)" in situation_select:
        mask |= (plays_df['yfog'] >= 99)
    if "Late & Close" in situation_select:
        mask |= (plays_df['qtr'] >= 4) & (abs(plays_df['ptsv'] - plays_df['ptsh']) <= 8)
    if "Shotgun" in situation_select:
        mask |= (plays_df['sg'] == 'Y')
    if "No Huddle" in situation_select:
        mask |= (plays_df['nh'] == 'Y')

    plays_df = plays_df[mask]

# ============================================================================
# METRIC CARDS
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

league_epa = plays_df['epa'].mean()
league_success = (plays_df['succ'] == 'Y').sum() / len(plays_df) * 100 if len(plays_df) > 0 else 0

# Best offense
off_epa = plays_df.groupby('off')['epa'].mean().sort_values(ascending=False)
best_off = off_epa.index[0] if len(off_epa) > 0 else "N/A"
best_off_epa = off_epa.iloc[0] if len(off_epa) > 0 else 0

# Best defense (lower is better)
def_epa = plays_df.groupby('def')['epa'].mean().sort_values(ascending=True)
best_def = def_epa.index[0] if len(def_epa) > 0 else "N/A"
best_def_epa = def_epa.iloc[0] if len(def_epa) > 0 else 0

with col1:
    st.markdown(metric_card("League Avg EPA/play", f"{league_epa:.2f}"), unsafe_allow_html=True)

with col2:
    st.markdown(metric_card("Success Rate", f"{league_success:.1f}%"), unsafe_allow_html=True)

with col3:
    best_off_name = TEAM_FULL_NAMES.get(best_off, best_off)
    st.markdown(metric_card("Best Offense", f"{best_off_epa:.2f}", sub=best_off_name), unsafe_allow_html=True)

with col4:
    best_def_name = TEAM_FULL_NAMES.get(best_def, best_def)
    st.markdown(metric_card("Best Defense", f"{best_def_epa:.2f}", sub=best_def_name), unsafe_allow_html=True)

st.divider()

# ============================================================================
# SECTION A: TEAM EFFICIENCY RANKINGS
# ============================================================================
st.header("A) Team Efficiency Rankings")

col_a1, col_a2 = st.columns(2)

# Calculate offensive EPA
off_stats = plays_df.groupby('off').agg({
    'epa': ['mean', 'std', 'count'],
    'succ': lambda x: (x == 'Y').sum() / len(x) * 100,
    'yds': 'mean'
}).reset_index()
off_stats.columns = ['Team', 'EPA/Play', 'EPA_Std', 'Plays', 'Success%', 'Avg Yards']
off_stats = off_stats.sort_values('EPA/Play', ascending=False)
off_stats['Team Full'] = off_stats['Team'].map(lambda x: TEAM_FULL_NAMES.get(x, x))
off_stats['Type'] = 'Offense'

# Calculate defensive EPA (flip sign)
def_stats = plays_df.groupby('def').agg({
    'epa': ['mean', 'std', 'count'],
    'succ': lambda x: (x == 'Y').sum() / len(x) * 100,
    'yds': 'mean'
}).reset_index()
def_stats.columns = ['Team', 'EPA/Play', 'EPA_Std', 'Plays', 'Success%', 'Avg Yards']
def_stats['EPA/Play'] = -def_stats['EPA/Play']  # Flip for defense
def_stats = def_stats.sort_values('EPA/Play', ascending=True)
def_stats['Team Full'] = def_stats['Team'].map(lambda x: TEAM_FULL_NAMES.get(x, x))
def_stats['Type'] = 'Defense'

with col_a1:
    st.subheader("Offensive EPA/Play Ranking", help="Higher is better")
    st.dataframe(
        off_stats[['Team', 'EPA/Play', 'Success%', 'Plays']].style.format({
            'EPA/Play': '{:.3f}',
            'Success%': '{:.1f}%',
            'Plays': '{:.0f}'
        }),
        use_container_width=True,
        height=400
    )

with col_a2:
    st.subheader("Defensive EPA/Play Ranking", help="Lower EPA against is better (shown as positive)")
    st.dataframe(
        def_stats[['Team', 'EPA/Play', 'Success%', 'Plays']].style.format({
            'EPA/Play': '{:.3f}',
            'Success%': '{:.1f}%',
            'Plays': '{:.0f}'
        }),
        use_container_width=True,
        height=400
    )

# Dual bar chart
fig_dual = make_subplots(
    rows=1, cols=2,
    subplot_titles=("Top 10 Offensive EPA/Play", "Top 10 Defensive EPA/Play"),
    specs=[[{}, {}]]
)

off_top = off_stats.head(10)
fig_dual.add_trace(go.Bar(
    y=off_top['Team Full'],
    x=off_top['EPA/Play'],
    orientation='h',
    name='Offense',
    marker=dict(color=COLORS['positive']),
    text=[f"{x:.3f}" for x in off_top['EPA/Play']],
    textposition='auto'
), row=1, col=1)

def_top = def_stats.head(10)
fig_dual.add_trace(go.Bar(
    y=def_top['Team Full'],
    x=def_top['EPA/Play'],
    orientation='h',
    name='Defense',
    marker=dict(color=COLORS['accent2']),
    text=[f"{x:.3f}" for x in def_top['EPA/Play']],
    textposition='auto'
), row=1, col=2)

fig_dual.update_xaxes(title_text="EPA/Play", row=1, col=1)
fig_dual.update_xaxes(title_text="EPA/Play (Lower is Better)", row=1, col=2)

fig_dual.update_layout(**CHART_LAYOUT,
    height=450,
    showlegend=False
)
st.plotly_chart(fig_dual, use_container_width=True)

st.divider()

# ============================================================================
# SECTION B: ROLLING EPA TRENDS
# ============================================================================
st.header("B) Rolling EPA Trends")

teams_for_rolling = sorted(plays_df['off'].unique())
selected_team = st.selectbox("Select Team for Rolling Trend", teams_for_rolling, key="rolling_team")

@st.cache_data
def compute_rolling_trends(season_select, selected_team):
    """Compute 4-game rolling EPA for a team."""
    sql = """
    SELECT
        g.seas, g.wk, p.gid, p.off, p.def, p.epa
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE g.seas = ? AND p.epa IS NOT NULL
    ORDER BY g.wk
    """
    all_plays = query(sql, [season_select])

    # Offense rolling
    off_plays = all_plays[all_plays['off'] == selected_team].copy()
    off_plays = off_plays.sort_values('wk')
    off_plays['rolling_epa'] = off_plays['epa'].rolling(window=30, min_periods=1).mean()  # ~4 games worth
    off_plays['rolling_count'] = off_plays['epa'].rolling(window=30, min_periods=1).count()

    # Defense rolling
    def_plays = all_plays[all_plays['def'] == selected_team].copy()
    def_plays = def_plays.sort_values('wk')
    def_plays['rolling_epa'] = -def_plays['epa'].rolling(window=30, min_periods=1).mean()
    def_plays['rolling_count'] = def_plays['epa'].rolling(window=30, min_periods=1).count()

    return off_plays, def_plays

off_rolling, def_rolling = compute_rolling_trends(season_select, selected_team)

col_b1, col_b2 = st.columns(2)

with col_b1:
    st.subheader(f"{selected_team} Offensive EPA Trend", help="4-game rolling average EPA/play")

    if len(off_rolling) > 0:
        fig_off = go.Figure()
        fig_off.add_trace(go.Scatter(
            x=off_rolling['wk'],
            y=off_rolling['rolling_epa'],
            mode='lines+markers',
            name='Offensive EPA',
            line=dict(color=COLORS['accent'], width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(26, 155, 80, 0.15)'
        ))
        fig_off.add_hline(y=0, line_dash="dash", line_color=COLORS['muted'])

        fig_off.update_layout(**CHART_LAYOUT,
            xaxis_title="Week",
            yaxis_title="EPA/Play (Rolling)",
            height=350,
            hovermode='x unified'
        )
        st.plotly_chart(fig_off, use_container_width=True)
    else:
        st.info("No offensive data for selected team/season")

with col_b2:
    st.subheader(f"{selected_team} Defensive EPA Trend", help="4-game rolling average EPA/play allowed")

    if len(def_rolling) > 0:
        fig_def = go.Figure()
        fig_def.add_trace(go.Scatter(
            x=def_rolling['wk'],
            y=def_rolling['rolling_epa'],
            mode='lines+markers',
            name='Defensive EPA',
            line=dict(color=COLORS['accent2'], width=3),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(39, 174, 96, 0.15)'
        ))
        fig_def.add_hline(y=0, line_dash="dash", line_color=COLORS['muted'])

        fig_def.update_layout(**CHART_LAYOUT,
            xaxis_title="Week",
            yaxis_title="EPA/Play Allowed (Rolling)",
            height=350,
            hovermode='x unified'
        )
        st.plotly_chart(fig_def, use_container_width=True)
    else:
        st.info("No defensive data for selected team/season")

st.divider()

# ============================================================================
# SECTION C: DOWN & DISTANCE HEATMAP
# ============================================================================
st.header("C) Down & Distance Heatmap")

col_c_filter1, col_c_filter2, col_c_filter3 = st.columns(3)

with col_c_filter1:
    heatmap_team = st.selectbox("Team (Offense)", teams_for_rolling, key="heatmap_team")

with col_c_filter2:
    heatmap_metric = st.radio("Metric", ["EPA/Play", "Success %"], horizontal=True)

with col_c_filter3:
    heatmap_play_type = st.selectbox("Play Type", ["All", "PASS", "RUSH"], key="heatmap_play")

# Build heatmap data
hm_plays = plays_df[plays_df['off'] == heatmap_team].copy()

if heatmap_play_type != "All":
    hm_plays = hm_plays[hm_plays['type'] == heatmap_play_type]

# Create buckets
def ytg_bucket(ytg):
    if pd.isna(ytg):
        return "Unknown"
    if ytg <= 3:
        return "1-3"
    elif ytg <= 6:
        return "4-6"
    elif ytg <= 10:
        return "7-10"
    elif ytg <= 15:
        return "11-15"
    else:
        return "16+"

hm_plays['ytg_bucket'] = hm_plays['ytg'].apply(ytg_bucket)

if heatmap_metric == "EPA/Play":
    heatmap_data = hm_plays.groupby(['dwn', 'ytg_bucket'])['epa'].mean().reset_index()
    metric_col = 'epa'
    colorscale = "RdYlGn"
    title_suffix = "EPA/Play"
else:
    heatmap_data = hm_plays.groupby(['dwn', 'ytg_bucket']).agg({
        'succ': lambda x: (x == 'Y').sum() / len(x) * 100
    }).reset_index()
    metric_col = 'succ'
    colorscale = "RdYlGn"
    title_suffix = "Success %"

# Pivot for heatmap
hm_pivot = heatmap_data.pivot(index='dwn', columns='ytg_bucket', values=metric_col)

ytg_order = ["1-3", "4-6", "7-10", "11-15", "16+"]
hm_pivot = hm_pivot[[col for col in ytg_order if col in hm_pivot.columns]]

fig_hm = go.Figure(data=go.Heatmap(
    z=hm_pivot.values,
    x=hm_pivot.columns,
    y=hm_pivot.index,
    colorscale=colorscale,
    text=np.round(hm_pivot.values, 2),
    texttemplate='%{text:.2f}',
    textfont={"size": 10},
    colorbar=dict(title=title_suffix)
))

fig_hm.update_layout(**CHART_LAYOUT,
    title=f"{heatmap_team} {title_suffix} by Down & Distance ({heatmap_play_type})",
    xaxis_title="Yards to Go",
    yaxis_title="Down",
    height=400
)
st.plotly_chart(fig_hm, use_container_width=True)

st.divider()

# ============================================================================
# SECTION D: SITUATIONAL SPLITS
# ============================================================================
st.header("D) Situational Splits")

col_d_team = st.selectbox("Team (Situational Analysis)", teams_for_rolling, key="situation_team")

sit_plays = plays_df[plays_df['off'] == col_d_team].copy()

situations = {
    'All Plays': sit_plays,
    '1st Down': sit_plays[sit_plays['dwn'] == 1],
    '2nd Down': sit_plays[sit_plays['dwn'] == 2],
    '3rd Down': sit_plays[sit_plays['dwn'] == 3],
    '4th Down': sit_plays[sit_plays['dwn'] == 4],
    'Red Zone': sit_plays[sit_plays['yfog'] >= 80],
    'Goal-to-Go': sit_plays[sit_plays['yfog'] >= 99],
    'Shotgun': sit_plays[sit_plays['sg'] == 'Y'],
    'No Huddle': sit_plays[sit_plays['nh'] == 'Y'],
}

sit_results = []
for sit_name, sit_data in situations.items():
    if len(sit_data) > 0:
        sit_results.append({
            'Situation': sit_name,
            'Plays': len(sit_data),
            'EPA/Play': sit_data['epa'].mean(),
            'Success%': (sit_data['succ'] == 'Y').sum() / len(sit_data) * 100,
            'Avg Yards': sit_data['yds'].mean()
        })

sit_df = pd.DataFrame(sit_results)

st.subheader(f"{col_d_team} Situational Splits")
st.dataframe(
    sit_df.style.format({
        'EPA/Play': '{:.3f}',
        'Success%': '{:.1f}%',
        'Avg Yards': '{:.2f}',
        'Plays': '{:.0f}'
    }),
    use_container_width=True,
    height=350
)

# Visualization
fig_sit = go.Figure()
fig_sit.add_trace(go.Bar(
    x=sit_df['Situation'],
    y=sit_df['EPA/Play'],
    marker=dict(color=sit_df['EPA/Play'], colorscale="RdYlGn", colorbar=dict(title="EPA/Play")),
    text=[f"{x:.3f}" for x in sit_df['EPA/Play']],
    textposition='auto'
))

fig_sit.update_layout(**CHART_LAYOUT,
    title=f"{col_d_team} EPA/Play by Situation",
    xaxis_title="Situation",
    yaxis_title="EPA/Play",
    height=400,
    showlegend=False
)
st.plotly_chart(fig_sit, use_container_width=True)

st.divider()

# ============================================================================
# SECTION E: EXPLOSIVE PLAY ANALYSIS
# ============================================================================
st.header("E) Explosive Play Analysis")

col_e1, col_e2 = st.columns(2)

with col_e1:
    exp_pass_threshold = st.slider("Explosive Pass Threshold (yards)", 10, 30, 20, step=1)
    exp_rush_threshold = st.slider("Explosive Rush Threshold (yards)", 5, 20, 10, step=1)

# Compute explosive rate by team
exp_results = []
for team in sorted(plays_df['off'].unique()):
    team_plays = plays_df[plays_df['off'] == team]

    # Pass explosives
    pass_plays = team_plays[team_plays['type'] == 'PASS']
    pass_exp = (pass_plays['yds'] >= exp_pass_threshold).sum() if len(pass_plays) > 0 else 0
    pass_count = len(pass_plays)

    # Rush explosives
    rush_plays = team_plays[team_plays['type'] == 'RUSH']
    rush_exp = (rush_plays['yds'] >= exp_rush_threshold).sum() if len(rush_plays) > 0 else 0
    rush_count = len(rush_plays)

    total_plays = len(team_plays)
    if total_plays > 0:
        exp_rate = (pass_exp + rush_exp) / total_plays * 100
    else:
        exp_rate = 0

    exp_results.append({
        'Team': team,
        'Explosive Rate %': exp_rate,
        'Total Explosives': pass_exp + rush_exp,
        'Total Plays': total_plays,
        'Pass Explosives': pass_exp,
        'Rush Explosives': rush_exp
    })

exp_df = pd.DataFrame(exp_results).sort_values('Explosive Rate %', ascending=False)

with col_e2:
    st.subheader("Explosive Rate by Team", help="% of plays gaining 20+ (pass) or 10+ (rush) yards")
    st.dataframe(
        exp_df[['Team', 'Explosive Rate %', 'Total Explosives', 'Total Plays']].style.format({
            'Explosive Rate %': '{:.1f}%',
            'Total Explosives': '{:.0f}',
            'Total Plays': '{:.0f}'
        }),
        use_container_width=True,
        height=400
    )

# Explosive rate chart
fig_exp = go.Figure()
fig_exp.add_trace(go.Bar(
    x=exp_df['Team'],
    y=exp_df['Explosive Rate %'],
    marker=dict(color=COLORS['accent']),
    text=[f"{x:.1f}% ({c})" for x, c in zip(exp_df['Explosive Rate %'], exp_df['Total Explosives'])],
    textposition='auto',
    hovertemplate='<b>%{x}</b><br>Explosive Rate: %{y:.1f}%<extra></extra>'
))

fig_exp.update_layout(**CHART_LAYOUT,
    title="Explosive Play Generation Rate",
    xaxis_title="Team",
    yaxis_title="Explosive Rate %",
    height=400,
    showlegend=False
)
st.plotly_chart(fig_exp, use_container_width=True)

# Explosive play distribution
st.subheader("Distribution of Big Plays")

col_dist1, col_dist2 = st.columns(2)

with col_dist1:
    # Pass distance distribution
    pass_big = plays_df[plays_df['type'] == 'PASS'].copy()
    pass_big = pass_big[pass_big['yds'] > 0]  # Only positive yards

    fig_pass_dist = go.Figure()
    fig_pass_dist.add_trace(go.Histogram(
        x=pass_big['yds'],
        nbinsx=30,
        marker=dict(color=COLORS['accent'], opacity=0.7),
        name='Pass Yards'
    ))
    fig_pass_dist.add_vline(x=exp_pass_threshold, line_dash="dash", line_color=COLORS['warn'],
                           annotation_text=f"Explosive Threshold ({exp_pass_threshold})")

    fig_pass_dist.update_layout(**CHART_LAYOUT,
        title="Pass Play Yardage Distribution",
        xaxis_title="Yards Gained",
        yaxis_title="Frequency",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig_pass_dist, use_container_width=True)

with col_dist2:
    # Rush distance distribution
    rush_big = plays_df[plays_df['type'] == 'RUSH'].copy()
    rush_big = rush_big[rush_big['yds'] > 0]

    fig_rush_dist = go.Figure()
    fig_rush_dist.add_trace(go.Histogram(
        x=rush_big['yds'],
        nbinsx=20,
        marker=dict(color=COLORS['accent2'], opacity=0.7),
        name='Rush Yards'
    ))
    fig_rush_dist.add_vline(x=exp_rush_threshold, line_dash="dash", line_color=COLORS['warn'],
                           annotation_text=f"Explosive Threshold ({exp_rush_threshold})")

    fig_rush_dist.update_layout(**CHART_LAYOUT,
        title="Rush Play Yardage Distribution",
        xaxis_title="Yards Gained",
        yaxis_title="Frequency",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig_rush_dist, use_container_width=True)

st.info("""
    **Efficiency Metrics Guide:**
    - **EPA/Play**: Expected Points Added per play. Positive = advancement, Negative = setback.
    - **Success Rate**: % of plays that move team closer to first down/touchdown.
    - **Explosive Rate**: % of plays gaining 20+ yards (pass) or 10+ yards (rush).
    - **Situational Splits**: Different situations may show efficiency advantages/disadvantages.
    - **Rolling Trends**: 4-game rolling average smooths week-to-week variance.
""")

st.markdown(page_footer(), unsafe_allow_html=True)
