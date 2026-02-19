"""Global configuration for NFL Analytics Suite — Sharp Sports Analysis."""
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_processed", "nfl.duckdb")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_processed")

# Sharp Sports Analysis — LIGHT brand palette
COLORS = {
    "bg": "#FFFFFF",
    "card": "#F8FAF9",
    "card_border": "#D5E8DD",
    "accent": "#1A9B50",        # Signature green (deeper for readability on white)
    "accent2": "#27AE60",       # Secondary green
    "accent3": "#C0392B",       # Red for negative/contrast
    "warn": "#E67E22",          # Amber warning
    "text": "#1C2833",
    "muted": "#7F8C8D",
    "grid": "#E8F0EC",
    "positive": "#1A9B50",
    "negative": "#C0392B",
    "neutral": "#2980B9",
    "gold": "#D4AC0D",
}

# Chart template defaults — LIGHT theme
CHART_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, sans-serif", color=COLORS["text"]),
    plot_bgcolor=COLORS["bg"],
    paper_bgcolor=COLORS["bg"],
    hoverlabel=dict(bgcolor=COLORS["card"], font_size=12, font_color=COLORS["text"]),
    margin=dict(l=40, r=20, t=50, b=40),
)

TEAM_COLORS = {
    "ARI": "#97233F", "ATL": "#A71930", "BAL": "#241773", "BUF": "#00338D",
    "CAR": "#0085CA", "CHI": "#C83200", "CIN": "#FB4F14", "CLE": "#311D00",
    "DAL": "#003594", "DEN": "#FB4F14", "DET": "#0076B6", "GB": "#203731",
    "HOU": "#03202F", "IND": "#002C5F", "JAC": "#006778", "JAX": "#006778",
    "KC": "#E31837", "LAC": "#0080C6", "LA": "#003594", "LAR": "#003594",
    "LV": "#A5ACAF", "OAK": "#A5ACAF", "MIA": "#008E97", "MIN": "#4F2683",
    "NE": "#002244", "NO": "#D3BC8D", "NYG": "#0B2265", "NYJ": "#125740",
    "PHI": "#004C54", "PIT": "#FFB612", "SF": "#AA0000", "SEA": "#002244",
    "TB": "#D50A0A", "TEN": "#0C2340", "WAS": "#773141", "SD": "#0080C6",
    "STL": "#003594",
}

SEASON_RANGE = list(range(2000, 2020))

# Team full name mapping (shared across all pages)
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

# Shared CSS for all pages — LIGHT THEME
SHARED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --brand-green: #1A9B50;
        --brand-bg: #FFFFFF;
        --card-bg: #F8FAF9;
        --border: #D5E8DD;
        --negative: #C0392B;
        --gold: #D4AC0D;
        --text: #1C2833;
        --muted: #7F8C8D;
    }

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: var(--brand-bg);
        color: var(--text);
    }

    h1 { font-weight: 800; letter-spacing: -0.03em; font-size: 2rem; color: var(--text); }
    h2 { font-weight: 700; letter-spacing: -0.02em; color: var(--brand-green); }
    h3 { font-weight: 600; letter-spacing: -0.01em; color: var(--text); }

    /* Sidebar */
    div[data-testid="stSidebar"] {
        background: #F0F7F3;
        border-right: 1px solid var(--border);
    }
    div[data-testid="stSidebar"] h1, div[data-testid="stSidebar"] h2 {
        color: var(--brand-green);
    }

    /* Metric cards */
    .ssa-metric {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 8px;
        border-left: 3px solid var(--brand-green);
    }
    .ssa-metric .label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .ssa-metric .value {
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--text);
        font-family: 'JetBrains Mono', monospace;
        line-height: 1.2;
    }
    .ssa-metric .sub {
        font-size: 0.72rem;
        color: var(--muted);
        margin-top: 2px;
    }
    .ssa-metric .delta-pos { color: var(--brand-green); font-weight: 600; }
    .ssa-metric .delta-neg { color: var(--negative); font-weight: 600; }

    /* Info box */
    .ssa-info {
        background: #F0F7F3;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 14px 18px;
        font-size: 0.82rem;
        color: #566573;
        line-height: 1.6;
        margin: 12px 0;
    }
    .ssa-info strong { color: var(--brand-green); }

    /* Section headers */
    .section-divider {
        border-top: 1px solid var(--border);
        margin: 28px 0 20px;
    }

    /* Table styling */
    .stDataFrame { border-radius: 8px; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        font-size: 0.82rem;
        border-radius: 6px 6px 0 0;
    }

    /* Footer */
    .ssa-footer {
        font-size: 0.68rem;
        color: #95A5A6;
        text-align: center;
        margin-top: 40px;
        padding: 16px 0;
        border-top: 1px solid var(--border);
    }
</style>
"""

def metric_card(label, value, sub="", delta="", delta_type="pos"):
    """Render a branded metric card."""
    delta_html = ""
    if delta:
        cls = "delta-pos" if delta_type == "pos" else "delta-neg"
        delta_html = f'<span class="{cls}">{delta}</span>'
    return f"""<div class="ssa-metric">
        <div class="label">{label}</div>
        <div class="value">{value} {delta_html}</div>
        <div class="sub">{sub}</div>
    </div>"""

def page_footer():
    """Standard footer for all pages."""
    return '<div class="ssa-footer">Sharp Sports Analysis | Data: Armchair Analysis 2000-2019 | All metrics include sample sizes. Not financial advice.</div>'
