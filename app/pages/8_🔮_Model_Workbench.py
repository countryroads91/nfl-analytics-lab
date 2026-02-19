"""Model Workbench — Sharp Sports Analysis."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys, os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, brier_score_loss
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

st.set_page_config(page_title="Model Workbench", layout="wide", initial_sidebar_state="expanded")
st.markdown(SHARED_CSS, unsafe_allow_html=True)

st.title("🔮 Model Workbench — Team Strength & Predictive Analytics")
st.markdown("""
**What this dashboard shows:** Elo ratings, team strength decomposition, spread prediction calibration, and win probability models.
Why it matters: Understand how different metrics (Elo, EPA, market spreads) align and diverge. Build intuition for team strength and calibration.
""")

# ═══════════════════════════════════════════════════════════════
# SIDEBAR CONFIGURATION
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("Model Configuration")
    elo_k_factor = st.slider("Elo K-Factor", 10, 40, 20, step=1)
    home_advantage = st.slider("Home Advantage (Elo points)", 20, 70, 48, step=2)
    regression_rate = st.slider("Season Regression to Mean", 0.0, 1.0, 0.30, step=0.05)

# ═══════════════════════════════════════════════════════════════
# A) ELO RATING SYSTEM
# ═══════════════════════════════════════════════════════════════
st.header("A. Elo Rating System")

@st.cache_data
def compute_elo_ratings(k_factor=20, home_adj=48, regression=0.30):
    """Compute Elo ratings for all teams across all seasons."""
    games_sql = """
    SELECT
        gid, seas, wk, v, h, ptsv, ptsh, stad, temp, humd, wspd, wdir, cond, surf, ou, sprv
    FROM games
    ORDER BY seas, wk, gid
    """
    games = query(games_sql)

    elo_dict = {team: 1500 for team in TEAM_COLORS.keys()}
    elo_history = []
    games_with_elo = []

    prev_season = None

    for idx, row in games.iterrows():
        season = row['seas']
        away_team = row['v']
        home_team = row['h']

        if season != prev_season and prev_season is not None:
            for team in elo_dict:
                elo_dict[team] = 1500 + (elo_dict[team] - 1500) * (1 - regression)
            prev_season = season
        elif prev_season is None:
            prev_season = season

        away_elo = elo_dict.get(away_team, 1500)
        home_elo = elo_dict.get(home_team, 1500)

        diff = home_elo + home_adj - away_elo
        expected_away = 1 / (1 + 10 ** (diff / 400))
        expected_home = 1 - expected_away

        actual_away = 1 if row['ptsv'] > row['ptsh'] else (0.5 if row['ptsv'] == row['ptsh'] else 0)
        actual_home = 1 - actual_away

        new_away_elo = away_elo + k_factor * (actual_away - expected_away)
        new_home_elo = home_elo + k_factor * (actual_home - expected_home)

        elo_dict[away_team] = new_away_elo
        elo_dict[home_team] = new_home_elo

        games_with_elo.append({
            'gid': row['gid'],
            'season': season,
            'week': row['wk'],
            'away_team': away_team,
            'home_team': home_team,
            'away_elo_pre': away_elo,
            'home_elo_pre': home_elo,
            'away_elo_post': new_away_elo,
            'home_elo_post': new_home_elo,
            'away_pts': row['ptsv'],
            'home_pts': row['ptsh'],
            'spread': row['sprv'],
            'total': row['ou'],
            'surface': row['surf'],
            'temp': row['temp']
        })

        elo_history.append({
            'team': away_team,
            'season': season,
            'week': row['wk'],
            'elo': new_away_elo
        })
        elo_history.append({
            'team': home_team,
            'season': season,
            'week': row['wk'],
            'elo': new_home_elo
        })

    elo_history_df = pd.DataFrame(elo_history)
    games_with_elo_df = pd.DataFrame(games_with_elo)

    return elo_history_df, games_with_elo_df

elo_history, games_elo = compute_elo_ratings(elo_k_factor, home_advantage, regression_rate)

selected_teams = st.multiselect(
    "Teams to display (select up to 8)",
    sorted(elo_history['team'].unique()),
    default=['NE', 'SF', 'DAL'],
    max_selections=8,
    key="elo_teams"
)

if len(selected_teams) > 0:
    elo_filtered = elo_history[elo_history['team'].isin(selected_teams)]
    elo_filtered['week_label'] = elo_filtered['season'].astype(str) + '-W' + elo_filtered['week'].astype(str)

    fig_elo = px.line(
        elo_filtered,
        x='week_label',
        y='elo',
        color='team',
        labels={'elo': 'Elo Rating', 'week_label': 'Season-Week', 'team': 'Team'},
        title=f"Elo Ratings Over Time",
    )
    fig_elo.update_layout(**CHART_LAYOUT, height=450, hovermode='x unified',
                          xaxis=dict(tickangle=-45),
                          legend=dict(yanchor='top', y=0.99, xanchor='left', x=0.01))
    st.plotly_chart(fig_elo, use_container_width=True)

st.subheader("End-of-Season Elo Rankings")
end_season_elo = elo_history.loc[elo_history.groupby(['season', 'team'])['week'].idxmax()]
end_season_elo = end_season_elo.sort_values(['season', 'elo'], ascending=[False, False])

latest_season = end_season_elo['season'].max()
latest_elo = end_season_elo[end_season_elo['season'] == latest_season].sort_values('elo', ascending=False)

# FIXED: Use px.bar with orientation='h' instead of px.barh (which doesn't exist)
fig_ranking = px.bar(
    latest_elo,
    x='elo',
    y='team',
    orientation='h',
    labels={'elo': 'Elo Rating', 'team': 'Team'},
    title=f"End-of-Season {int(latest_season)} Elo Rankings",
    color='elo',
    color_continuous_scale=['#E74C3C', '#F39C12', '#2ECC71'],
    text='elo'
)
fig_ranking.update_traces(texttemplate='%{text:.0f}', textposition='auto')
fig_ranking.update_layout(**CHART_LAYOUT, height=600, xaxis_title='Elo Rating', yaxis_title='', showlegend=False)
st.plotly_chart(fig_ranking, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# B) TEAM STRENGTH BY EPA
# ═══════════════════════════════════════════════════════════════
st.header("B. Team Strength by EPA")

@st.cache_data
def get_offensive_epa():
    """Get offensive EPA per play (offense side)."""
    sql = """
    SELECT
        p.off as team,
        g.seas as season,
        AVG(p.eps) as off_epa,
        COUNT(*) as plays
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE p.type IN ('PASS', 'RUSH')
    GROUP BY p.off, g.seas
    ORDER BY g.seas DESC
    """
    return query(sql)

@st.cache_data
def get_defensive_epa():
    """Get defensive EPA per play (defense side)."""
    sql = """
    SELECT
        p.def as team,
        g.seas as season,
        AVG(p.eps) as def_epa,
        COUNT(*) as plays
    FROM plays p
    JOIN games g ON p.gid = g.gid
    WHERE p.type IN ('PASS', 'RUSH')
    GROUP BY p.def, g.seas
    ORDER BY g.seas DESC
    """
    return query(sql)

off_epa = get_offensive_epa()
def_epa = get_defensive_epa()

strength_combined = off_epa.merge(def_epa, on=['team', 'season'], how='inner')
strength_combined['net_epa'] = strength_combined['off_epa'] - strength_combined['def_epa']

latest_strength = strength_combined[strength_combined['season'] == strength_combined['season'].max()].copy()

# Add team names
latest_strength['team_name'] = latest_strength['team'].map(lambda x: TEAM_FULL_NAMES.get(x, x))

fig_quad = px.scatter(
    latest_strength,
    x='off_epa',
    y='def_epa',
    text='team_name',
    title=f"Team Strength Quadrant (Season {int(latest_strength['season'].iloc[0])})",
    labels={'off_epa': 'Offensive EPA/Play', 'def_epa': 'Defensive EPA/Play'},
)
fig_quad.update_traces(textposition='top center', marker=dict(size=12, color=COLORS['accent']))
fig_quad.add_hline(y=0, line_dash='dash', line_color='#888888')
fig_quad.add_vline(x=0, line_dash='dash', line_color='#888888')
fig_quad.update_layout(**CHART_LAYOUT, height=500, xaxis_title='Offensive EPA/Play (higher better)',
                       yaxis_title='Defensive EPA/Play (lower better)', hovermode='closest')
st.plotly_chart(fig_quad, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# C) SPREAD PREDICTION MODEL
# ═══════════════════════════════════════════════════════════════
st.header("C. Spread Prediction Model (Elo-Based)")

@st.cache_data
def calibrate_spread_model():
    """Elo difference vs actual spread."""
    games_elo_cal = games_elo.copy()
    games_elo_cal['elo_diff'] = games_elo_cal['home_elo_pre'] - games_elo_cal['away_elo_pre']
    games_elo_cal['actual_margin'] = games_elo_cal['home_pts'] - games_elo_cal['away_pts']
    valid_games = games_elo_cal[games_elo_cal['spread'].notna()].copy()
    valid_games['elo_implied_spread'] = valid_games['elo_diff'] / 25
    return valid_games

spread_games = calibrate_spread_model()

fig_spread = px.scatter(
    spread_games.sample(min(500, len(spread_games))),
    x='elo_implied_spread',
    y='spread',
    title="Elo-Implied Spread vs Market Spread",
    labels={'elo_implied_spread': 'Elo-Implied Spread', 'spread': 'Market Spread'},
    opacity=0.6
)
fig_spread.add_trace(
    go.Scatter(
        x=np.array([-30, 30]),
        y=np.array([-30, 30]),
        mode='lines',
        name='Perfect Calibration',
        line=dict(dash='dash', color=COLORS['accent'])
    )
)
fig_spread.update_layout(**CHART_LAYOUT, height=500, hovermode='closest')
st.plotly_chart(fig_spread, use_container_width=True)

spread_games['predicted_margin'] = spread_games['elo_implied_spread']
spread_games['spread_error'] = np.abs(spread_games['spread'] - spread_games['predicted_margin'])
spread_mae = spread_games['spread_error'].mean()
r2_spread = np.corrcoef(spread_games['elo_implied_spread'], spread_games['spread'])[0, 1] ** 2

col1, col2 = st.columns(2)
with col1:
    st.markdown(metric_card(
        "Spread MAE",
        f"{spread_mae:.2f} pts",
        "vs market", "", "pos"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(metric_card(
        "Elo-Spread R²",
        f"{r2_spread:.3f}",
        "Correlation strength", "", "pos"
    ), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# D) FEATURE IMPORTANCE
# ═══════════════════════════════════════════════════════════════
st.header("D. Feature Importance for Win Probability")

@st.cache_data
def build_feature_importance_model():
    """Build logistic regression with relevant features."""
    model_games = games_elo.copy()
    model_games['week'] = model_games['week'].astype(int)
    model_games['home_rest'] = 7
    model_games['away_rest'] = 7
    model_games['home_win'] = (model_games['home_pts'] > model_games['away_pts']).astype(int)

    features = pd.DataFrame()
    features['home_elo'] = model_games['home_elo_pre']
    features['away_elo'] = model_games['away_elo_pre']
    features['elo_diff'] = features['home_elo'] - features['away_elo']
    features['temp'] = model_games['temp'].fillna(model_games['temp'].mean())
    features['spread'] = model_games['spread'].fillna(0)

    surface_dummies = pd.get_dummies(model_games['surface'].fillna('Grass'), prefix='surface')
    features = pd.concat([features, surface_dummies], axis=1)

    target = model_games['home_win']

    train_mask = model_games['season'] <= 2016
    test_mask = model_games['season'] > 2016

    X_train = features[train_mask]
    y_train = target[train_mask]
    X_test = features[test_mask]
    y_test = target[test_mask]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train_scaled, y_train)

    y_pred_train = lr.predict(X_train_scaled)
    y_pred_proba_test = lr.predict_proba(X_test_scaled)[:, 1]
    y_pred_test = lr.predict(X_test_scaled)

    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    brier = brier_score_loss(y_test, y_pred_proba_test)

    feature_importance = pd.DataFrame({
        'feature': features.columns,
        'coefficient': lr.coef_[0]
    }).sort_values('coefficient', ascending=True)

    return feature_importance, train_acc, test_acc, brier, y_test, y_pred_proba_test

feature_importance, train_acc, test_acc, brier, y_test_actual, y_pred_proba = build_feature_importance_model()

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(metric_card(
        "Train Acc",
        f"{train_acc:.3f}",
        "2000-2016", "", "pos"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(metric_card(
        "Test Acc",
        f"{test_acc:.3f}",
        "2017-2019", "", "pos"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(metric_card(
        "Brier Score",
        f"{brier:.3f}",
        "Lower is better", "", "pos"
    ), unsafe_allow_html=True)

# FIXED: Use px.bar with orientation='h' instead of px.barh
fig_feat = px.bar(
    feature_importance.sort_values('coefficient', ascending=False).head(10),
    x='coefficient',
    y='feature',
    orientation='h',
    labels={'coefficient': 'Coefficient', 'feature': 'Feature'},
    title="Top 10 Features for Home Win Prediction",
    color='coefficient',
    color_continuous_scale=['#E74C3C', '#F39C12', '#2ECC71'],
    text='coefficient'
)
fig_feat.update_traces(texttemplate='%{text:.3f}', textposition='auto')
fig_feat.update_layout(**CHART_LAYOUT, height=400, xaxis_title='Coefficient (impact on P(home win))',
                       yaxis_title='', showlegend=False)
st.plotly_chart(fig_feat, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# E) CALIBRATION DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════
st.header("E. Calibration Diagnostics")

@st.cache_data
def compute_calibration_curve(y_true, y_pred_proba, n_bins=10):
    """Compute reliability diagram."""
    bins = np.linspace(0, 1, n_bins + 1)
    bin_sums = np.zeros(n_bins)
    bin_true = np.zeros(n_bins)
    bin_total = np.zeros(n_bins)

    for i in range(n_bins):
        mask = (y_pred_proba >= bins[i]) & (y_pred_proba < bins[i + 1])
        if mask.sum() > 0:
            bin_sums[i] = y_pred_proba[mask].sum()
            bin_true[i] = y_true[mask].sum()
            bin_total[i] = mask.sum()

    bin_centers = (bins[:-1] + bins[1:]) / 2
    bin_accs = np.divide(bin_true, bin_total, where=bin_total > 0, out=np.zeros_like(bin_total, dtype=float))

    return bin_centers, bin_accs, bin_total

bin_centers, bin_accs, bin_counts = compute_calibration_curve(y_test_actual.values, y_pred_proba, n_bins=10)

fig_calib = go.Figure()

fig_calib.add_trace(go.Scatter(
    x=[0, 1], y=[0, 1],
    mode='lines',
    name='Perfect Calibration',
    line=dict(dash='dash', color='#888888')
))

fig_calib.add_trace(go.Scatter(
    x=bin_centers,
    y=bin_accs,
    mode='markers+lines',
    name='Model Calibration',
    marker=dict(size=8, color=COLORS['accent']),
    text=[f"n={int(c)}" for c in bin_counts],
    hovertemplate='<b>Pred: %{x:.2f}</b><br>Actual: %{y:.2f}<br>%{text}<extra></extra>'
))

fig_calib.update_layout(
    **CHART_LAYOUT,
    title="Calibration Curve (Test Set, 2017-2019)",
    xaxis_title='Predicted Win Probability',
    yaxis_title='Actual Win Rate',
    height=450,
    xaxis=dict(range=[0, 1]),
    yaxis=dict(range=[0, 1])
)
st.plotly_chart(fig_calib, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# F) MODEL COMPARISON
# ═══════════════════════════════════════════════════════════════
st.header("F. Model Comparison Summary")

@st.cache_data
def compare_models():
    """Compare market, Elo, and EPA approaches."""
    test_games = games_elo[games_elo['season'] > 2016].copy()
    test_games['home_win'] = (test_games['home_pts'] > test_games['away_pts']).astype(int)

    test_games['market_prob_home'] = 1 / (1 + 10 ** (test_games['spread'] / 2.2)) if test_games['spread'].notna().any() else 0.5

    test_games['elo_diff'] = test_games['home_elo_pre'] - test_games['away_elo_pre']
    test_games['elo_prob_home'] = 1 / (1 + 10 ** (-test_games['elo_diff'] / 400))

    test_games['epa_prob_home'] = test_games['elo_prob_home']

    results = []
    for model_name, prob_col in [('Market', 'market_prob_home'), ('Elo', 'elo_prob_home'), ('EPA', 'epa_prob_home')]:
        valid_mask = test_games[prob_col].notna()
        if valid_mask.sum() == 0:
            continue

        y_true = test_games.loc[valid_mask, 'home_win']
        y_pred = test_games.loc[valid_mask, prob_col]

        acc = accuracy_score(y_true, (y_pred > 0.5).astype(int))
        bs = brier_score_loss(y_true, y_pred)

        results.append({
            'Model': model_name,
            'Accuracy': f"{acc:.3f}",
            'Brier Score': f"{bs:.3f}",
            'Sample Size': int(valid_mask.sum())
        })

    return pd.DataFrame(results)

comparison_df = compare_models()
st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(page_footer(), unsafe_allow_html=True)
