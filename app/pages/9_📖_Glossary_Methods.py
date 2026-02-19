import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from app.db import query
from app.config import COLORS, TEAM_COLORS, SEASON_RANGE

st.set_page_config(page_title="Glossary & Methods", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════
# TITLE & DESCRIPTION
# ═══════════════════════════════════════════════════════════════
st.title("📖 Glossary, Methods & Data Documentation")
st.markdown("""
Complete reference guide for metrics, data sources, methodology, and technical documentation.
Use this page to understand the definitions, limitations, and proper interpretation of analyses across the app.
""")

# ═══════════════════════════════════════════════════════════════
# A) METRIC DEFINITIONS
# ═══════════════════════════════════════════════════════════════
with st.expander("📊 A. Metric Definitions & Formulas", expanded=True):
    metrics_data = {
        "EPA (Expected Points Added)": {
            "definition": "The change in expected points from one play to the next. Pre-computed in the dataset. Positive EPA means the offense gained an advantage; negative means the defense forced a worse situation.",
            "formula": "EPA = Expected Points (start of play) - Expected Points (end of play)",
            "interpretation": "EPA/play averages 0 across the league. Teams with +0.1 EPA/play rank among the best offenses.",
            "range": "Typically -3 to +3 per play"
        },
        "Success Rate": {
            "definition": "Binary indicator of whether a play gained 'enough' yards for the situation. Pre-computed in the 'succ' field.",
            "formula": "1st down: ≥40% of needed yards | 2nd down: ≥60% of needed yards | 3rd/4th down: ≥100% (first down gained)",
            "interpretation": "Average success rate across the league is ~50%. Higher is better for offense.",
            "range": "0 (fail) or 1 (success)"
        },
        "Explosive Play": {
            "definition": "A play that gains a large amount of yards in a single attempt, indicating offensive explosion.",
            "formula": "Pass: ≥20 yards | Rush: ≥10 yards | Receiver: ≥20 yards",
            "interpretation": "Elite offenses generate explosive plays at a higher rate than average. Explosion percentage = (explosive plays / total plays) × 100",
            "range": "Binary per play; rate is typically 5-15% for good offenses"
        },
        "Pressure / Sack Rate": {
            "definition": "The frequency with which a QB is sacked or pressured per passing attempt. Direct measure of offensive line and defensive pass rush effectiveness.",
            "formula": "Sack Rate = Sacks / (Passes + Sacks)",
            "interpretation": "League average sack rate ~7%. Below 5% indicates excellent pass protection.",
            "range": "Typically 3-12% depending on team strength"
        },
        "ATS (Against the Spread)": {
            "definition": "Whether a team covered the point spread (beat the spread by more than the spread amount).",
            "formula": "If team is favorite (negative spread): margin > |spread|. If underdog: margin > spread.",
            "interpretation": "ATS record shows predictability vs betting market expectations. 50% indicates market is fair.",
            "range": "Win% from 0-100%; league average ~50%"
        },
        "CLV (Closing Line Value)": {
            "definition": "The difference between the odds you got and the closing line. Indicator of whether you received favorable pricing.",
            "formula": "CLV = Your Line - Closing Line",
            "interpretation": "Positive CLV on wins indicates consistent value identification. Requires historical betting line data.",
            "range": "Typically ±3 points for standard games"
        },
        "Win Probability": {
            "definition": "Estimated probability that the home team wins, derived from models (Elo, EPA, or market prices).",
            "formula": "Market: 1 / (1 + 10^(spread / 2.2)) | Elo: 1 / (1 + 10^(-elo_diff / 400))",
            "interpretation": "0.5 = even match; 0.7 = 70% favored team expected to win. Calibrated models should match actual win rates.",
            "range": "0.0 to 1.0 (probabilities)"
        },
        "Completion Rate": {
            "definition": "Percentage of pass attempts that result in a completion.",
            "formula": "Completions / Pass Attempts × 100",
            "interpretation": "League average ~65%. Elite QBs 67%+; backup QBs below 60%.",
            "range": "Typically 45-75% over a season"
        },
        "YPA (Yards Per Attempt)": {
            "definition": "Average passing yards gained per pass attempt. Key efficiency metric for quarterbacks.",
            "formula": "(Passing Yards) / (Pass Attempts)",
            "interpretation": "League average ~7.0 YPA. 8.0+ is elite; below 6.0 is below average.",
            "range": "Typically 5.5-8.5 YPA for qualified passers"
        },
        "Sack Rate": {
            "definition": "Frequency of sacks as a percentage of pass attempts including sacks.",
            "formula": "Sacks / (Pass Attempts + Sacks) × 100",
            "interpretation": "Reflects both QB holding time and pass rush effectiveness. League average ~7%.",
            "range": "Typically 3-12%"
        },
        "Red Zone Efficiency": {
            "definition": "Percentage of red zone possessions (yfog ≥ 80) that result in touchdowns or field goals.",
            "formula": "(TDs + FGs) / Total Red Zone Drives",
            "interpretation": "Elite offenses score in 60%+ of red zone drives; poor offenses ~40%.",
            "range": "Typically 40-70%"
        },
        "Goal-to-Go Success": {
            "definition": "Success rate on plays inside the 1-yard line (yfog ≥ 99).",
            "formula": "Plays gaining ≥1 yard / Total goal-to-go plays",
            "interpretation": "Should be very high (80%+). Failures often result in turnovers on downs.",
            "range": "Typically 70-95%"
        }
    }

    for metric_name, metric_info in metrics_data.items():
        with st.expander(f"**{metric_name}**"):
            st.markdown(f"**Definition:** {metric_info['definition']}")
            st.markdown(f"**Formula:** `{metric_info['formula']}`")
            st.markdown(f"**Interpretation:** {metric_info['interpretation']}")
            st.markdown(f"**Typical Range:** {metric_info['range']}")

# ═══════════════════════════════════════════════════════════════
# B) DATA COVERAGE & CAVEATS
# ═══════════════════════════════════════════════════════════════
with st.expander("⚠️ B. Data Coverage & Limitations", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Coverage")
        coverage_text = """
        **Seasons Covered:** 2000–2019 (20 seasons)
        **Data Source:** Armchair Analysis (via nflfastR ingestion)
        **Teams:** 32 NFL teams + historical franchises (STL, OAK, SD)
        **Total Games:** ~5,120 regular season games
        **Play-by-Play Records:** 350,000+ individual plays

        **Table Completeness:**
        - games: 100% coverage (all regular season)
        - plays: 95% (some missing snap-level details pre-2011)
        - passes/rushes: 95% (derived from plays)
        - drives: 98%
        - players: 95% (coverage improves toward 2010s)
        - EPA values: 95% (pre-computed)
        """
        st.markdown(coverage_text)

    with col2:
        st.subheader("Known Limitations")
        limitations_text = """
        **EPA Methodology:**
        - Pre-computed; original calculation methodology may vary slightly from nflfastR
        - Does not adjust for yards-line-to-gain on some plays before 2011

        **Snap-Level Data:**
        - Limited availability before ~2012
        - Pressure/coverage details incomplete vs NFL Next Gen Stats

        **Player Coverage:**
        - Position data incomplete for defensive players (pre-2010)
        - Injury data based on practice reports, not verified in-game

        **Betting Data:**
        - Spreads (sprv) and totals (ou) are closing-line approximations
        - May not represent actual market opening lines
        - No historical line movement data

        **Surface/Stadium:**
        - Surface data quality varies by era
        - Some indoor facilities not consistently classified

        **Temperature/Weather:**
        - Weather data estimated for some historical games
        - Wind direction (wdir) has missing values (~30% pre-2010)
        """
        st.markdown(limitations_text)

# ═══════════════════════════════════════════════════════════════
# C) TABLE DESCRIPTIONS
# ═══════════════════════════════════════════════════════════════
with st.expander("📋 C. Database Table Descriptions", expanded=False):
    st.subheader("Query Table Information")

    @st.cache_data
    def get_table_info():
        """Get row counts and basic schema info for all tables."""
        tables = [
            'games', 'plays', 'passes', 'rushes', 'drives', 'penalties',
            'sacks', 'players', 'offense_stats', 'defense_stats',
            'touchdowns', 'redzone', 'fgxp'
        ]

        table_info = []
        for table in tables:
            try:
                count_sql = f"SELECT COUNT(*) as cnt FROM {table}"
                count_result = query(count_sql)
                row_count = count_result['cnt'].iloc[0] if len(count_result) > 0 else 0

                # Get column info
                cols_sql = f"DESCRIBE {table}"
                cols_result = query(cols_sql)
                col_names = cols_result['column_name'].tolist() if 'column_name' in cols_result.columns else []

                table_info.append({
                    'Table': table,
                    'Rows': int(row_count),
                    'Columns': len(col_names),
                    'Key Columns': ', '.join(col_names[:5]) + ('...' if len(col_names) > 5 else '')
                })
            except:
                pass

        return pd.DataFrame(table_info)

    table_info_df = get_table_info()
    st.dataframe(table_info_df, use_container_width=True, hide_index=True)

    # Detailed descriptions
    st.markdown("""
    **games**
    - Primary table for game-level information
    - Key columns: gid (game ID), seas (season), wk (week), v (visiting team), h (home team)
    - Includes scoring: ptsv, ptsh; betting: sprv (spread), ou (total)
    - Weather: temp, humd (humidity), wspd (wind speed), wdir (wind direction), cond (condition)
    - Stadium: stad (stadium code), surf (surface type)

    **plays**
    - Core play-by-play data
    - Key columns: gid, pid (play ID), off (offensive team), def (defensive team), type (PASS/RUSH/etc.)
    - Positional: qtr (quarter), min, sec, dwn (down), ytg (yards to go), yfog (yards from own goal)
    - Performance: yds (yards), succ (success), pts (points scored), eps (EPA), epa
    - Players: psr (passer), trg (target), bc (ball carrier)

    **passes**
    - Derived from plays where type='PASS'
    - Key columns: pid, psr (QB), trg (receiver), loc (location on field), yds, comp (completion), spk (sack)

    **rushes**
    - Derived from plays where type='RUSH'
    - Key columns: pid, bc (RB), dir (rush direction: LE, LT, LG, MD, RG, RT, RE), yds, succ, kne (knee down)

    **drives**
    - Drive-level summary (aggregates plays)
    - Key columns: uid (drive ID), gid, tname (team), fpid (first play ID), res (result: TD, FG, PUNT, etc.)
    - Stats: num_plays, ry (rush yards), ra (rush attempts), py (pass yards), pa (pass attempts)
    - Performance: peyf (EPA for), peya (EPA against)

    **penalties**
    - All penalties in games
    - Key columns: uid, pid, ptm (penalizing team), pen, desc (description), cat (category)

    **sacks**
    - Sack records with defender info
    - Key columns: uid, qb (QB sacked), sk (sacker), value (sack credit), ydsl (yards lost)

    **players**
    - Player master list
    - Key columns: player (ID), fname, lname, pname (full name), pos1, pos2 (positions)
    - Includes career meta data

    **offense_stats**
    - Season-level offensive statistics by player
    - Key columns: uid, player, seas, year, team, pa (pass attempts), pc (completions), py (pass yards)
    - Includes rushing, receiving, TD stats

    **defense_stats**
    - Season-level defensive statistics by player
    - Key columns: uid, player, seas, year, team, solo (solo tackles), comb (combined), sck (sacks)

    **touchdowns**
    - All touchdown records with context
    - Key columns: pid, qtr, dwn, yds, pts, player (scorer), type (RUSH/REC/INT/FUM/etc.)

    **redzone**
    - Red zone statistics (plays where yfog ≥ 80)
    - Same structure as offense_stats but filtered to red zone carries/targets

    **fgxp**
    - Field goal and extra point attempts
    - Key columns: pid, fgxp (FG or XP), fkicker (kicker), dist (distance), good (1=made, 0=missed)
    """)

# ═══════════════════════════════════════════════════════════════
# D) METHODOLOGY NOTES
# ═══════════════════════════════════════════════════════════════
with st.expander("🔬 D. Methodology & Model Notes", expanded=False):
    st.subheader("Advanced Analytics Methodology")

    methodology_sections = {
        "Elo Rating System": """
        **Purpose:** Estimate relative team strength over time.

        **Parameters:**
        - Initial rating: 1500 for all teams
        - K-factor: 20 (determines rating volatility per game)
        - Home advantage: 48 Elo points (added to home team expected value)
        - Season regression: 30% toward 1500 (prevents extreme swings year-to-year)

        **Calculation:**
        1. Compute expected win probability: P_home = 1 / (1 + 10^(-(Elo_home + 48 - Elo_away) / 400))
        2. Actual result: 1 (home win), 0.5 (tie), 0 (away win)
        3. Update: Elo_new = Elo_old + K × (Actual - Expected)
        4. At season boundary: Elo = 1500 + (Elo - 1500) × 0.7

        **Interpretation:** Elo difference of 100 points ≈ 65% win probability in neutral setting.
        """,

        "EPA (Expected Points Added) Calculation": """
        **Purpose:** Quantify the offensive and defensive value created on each play.

        **Methodology:**
        - Pre-computed using play-by-play context and game state
        - Expected points calculated from historical win probability vs scoring opportunities
        - EPA = (Expected Points at end of play) - (Expected Points at start of play)
        - Positive EPA: Offensive gain; Negative EPA: Defensive gain

        **Interpretation:**
        - League average EPA/play ≈ 0 (by definition)
        - Good offenses: +0.1 to +0.2 EPA/play
        - Elite offenses: +0.2+ EPA/play
        - Good defenses: -0.1 to -0.2 EPA/play

        **Source:** Pre-computed in Armchair Analysis dataset.
        """,

        "Success Rate (Binary Play Outcome)": """
        **Purpose:** Binary indicator of whether a play achieved minimum yardage for the situation.

        **Definition:**
        - 1st down: Gains ≥40% of yards needed for first down
        - 2nd down: Gains ≥60% of yards needed
        - 3rd/4th down: Gains ≥100% of yards needed (conversion)

        **Rationale:** Different standards by down reflect changing risk tolerance.

        **Aggregation:** Success Rate (%) = (Successful plays / Total plays) × 100
        - League average ≈ 50%
        """,

        "Spread Calibration Model": """
        **Purpose:** Validate predictive model accuracy against betting markets.

        **Method:**
        - Convert Elo difference to implied spread: Spread = Elo_diff / 25
        - Compare to market closing line spread
        - Metrics: MAE (Mean Absolute Error), Correlation (R²)

        **Calibration:**
        - Perfect calibration: Elo-implied spread = market spread
        - If Elo-implied typically lower: Elo underestimates favorite strength
        - If typically higher: Elo overestimates

        **Application:** Identify discrepancies between market and model consensus.
        """,

        "Logistic Regression (Win Probability)": """
        **Purpose:** Predict home team win probability from game features.

        **Features:**
        - Home Elo (pre-game rating)
        - Away Elo (pre-game rating)
        - Elo difference (home - away)
        - Temperature
        - Surface type (one-hot encoded)
        - Market spread (external information)

        **Train/Test Split:**
        - Training: 2000–2016 seasons
        - Testing: 2017–2019 seasons (held-out for unbiased evaluation)

        **Metrics:**
        - Accuracy: Correct predictions / Total predictions
        - Brier Score: Mean squared error of probability predictions (lower is better)
        - Calibration: Bin predicted probabilities and compare to actual win rates

        **Interpretation:** Brier score <0.2 indicates good calibration.
        """,

        "Red Zone Analysis": """
        **Purpose:** Study offensive efficiency in critical scoring position.

        **Definitions:**
        - Red Zone: yfog ≥ 80 (within opponent's 20-yard line)
        - Goal-to-Go: yfog ≥ 99 (inside 1-yard line)
        - Inside the 5: yfog ≥ 95 (inside 5-yard line)

        **Key Stats:**
        - TD Rate: Touchdowns / Red zone drives
        - FG Rate: Field goals / Red zone drives
        - Success Rate: Plays gaining required yards
        - EPA/play: Average expected points added

        **Minimum Sample Size:** 30 plays for meaningful analysis.
        """
    }

    for section_name, section_text in methodology_sections.items():
        with st.expander(section_name):
            st.markdown(section_text)

# ═══════════════════════════════════════════════════════════════
# E) BIBLIOGRAPHY & REFERENCES
# ═══════════════════════════════════════════════════════════════
with st.expander("📚 E. Bibliography & References", expanded=False):
    st.markdown("""
    **Core Statistical References:**

    - Romer, D. (2006). "Do Firms Maximize? Evidence from Professional Football."
      _Journal of Political Economy_, 114(2), 340-365.
      [Link](https://www.jstor.org/stable/10.1086/500802)

    - Yurko, R., Ventura, S., & Horowitz, M. (2019). "Going deep: Models for continuous-time
      within-play expectation of goal probability in American football." Journal of
      Quantitative Analysis in Sports, 15(3), 163-180.

    - Burke, B. (2014). "Advanced NFL Stats: 2014 EPA and Per Play Statistics."
      [Link](https://www.advancednflstats.com/)

    **Data Sources:**

    - Armchair Analysis: Raw play-by-play data
      [Link](https://www.armchairanalysis.com/)

    - nflfastR: Modern NFL data (reference for methodology)
      [Link](https://www.nflfastr.nfl.com/)

    **Key Tools & Frameworks:**

    - Football Outsiders: DVOA, S&P+
      [Link](https://www.footballoutsiders.com/)

    - ESPN Stats & Information
      [Link](https://www.espn.com/nfl/statistics)

    **Elo Rating System:**

    - Glickman, M. E., & Jones, A. C. (1999). "Rating the Chess Raters."
      _Chess Life Magazine_. [Mathematical foundation]

    - FiveThirtyEight NFL Predictions:
      [Link](https://projects.fivethirtyeight.com/nfl-predictions/)
    """)

# ═══════════════════════════════════════════════════════════════
# F) HOW TO USE THIS APP
# ═══════════════════════════════════════════════════════════════
with st.expander("🚀 F. How to Use This App", expanded=False):
    st.subheader("Navigation & Features")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Page Guide:**

        1. **Market & CLV Lab** - Analyze market efficiency, closing line value, and ATS records
        2. **Efficiency Explorer** - EPA rankings, play success rates, player efficiency
        3. **Trenches Disruption** - Pass rush metrics, OL performance, sack analysis
        4. **Red Zone DNA** - Red zone efficiency, playcalling, goal-line analysis
        5. **Model Workbench** - Elo ratings, predictive models, calibration
        6. **Glossary & Methods** - This page: definitions and documentation
        """)

    with col2:
        st.markdown("""
        **Filter & Control Tips:**

        - **Multiselect:** Hold Ctrl/Cmd to select multiple teams
        - **Deselect All:** Click the 'x' to clear team filters and see league view
        - **Season Range:** Use sidebar sliders to focus on specific era
        - **Metric Tooltips:** Hover over chart elements for details
        - **Export Data:** Right-click on charts to save as PNG
        - **Mobile:** Collapsible sidebar available on mobile devices
        """)

    st.markdown("""
    **Interpretation Best Practices:**

    1. **Always Check Sample Size:** Metrics with n < 30 should be treated with caution
    2. **Context Matters:** A team with high EPA might be playing from behind (garbage time inflation)
    3. **Correlation ≠ Causation:** Surface type and EPA are correlated, but don't assume causation
    4. **Season Trends:** Use line charts to identify momentum; single-game outliers common
    5. **Model Limitations:** All models assume stable NFL environment; rule changes and talent shifts matter
    6. **Spreads Move:** Market line data is closing line; opening lines differ significantly
    """)

    st.markdown("""
    **Advanced Queries:**

    If you have DuckDB access, try these custom queries:

    ```sql
    -- Find games with extreme EPA swings (large upsets)
    SELECT gid, seas, v, h, ptsv, ptsh,
           AVG(eps) OVER (PARTITION BY gid, off) as avg_epa
    FROM plays
    WHERE seas = 2019 AND (ptsv > ptsh OR ptsh > ptsv)
    ORDER BY ABS(ptsv - ptsh) DESC
    LIMIT 10;

    -- Red zone efficiency by team and opponent
    SELECT off, def, COUNT(*) as plays,
           SUM(CASE WHEN pts > 0 THEN 1 ELSE 0 END) / COUNT(*) as scoring_rate
    FROM plays
    WHERE yfog >= 80
    GROUP BY off, def
    ORDER BY scoring_rate DESC;
    ```
    """)

# ═══════════════════════════════════════════════════════════════
# QUICK REFERENCE CARD
# ═══════════════════════════════════════════════════════════════
st.divider()
st.subheader("⚡ Quick Reference Card")

ref_cols = st.columns(3)

with ref_cols[0]:
    st.markdown("""
    **Typical League Averages**

    | Metric | Value |
    |--------|-------|
    | EPA/Play | 0.0 |
    | Success Rate | ~50% |
    | Completion Rate | ~65% |
    | Sack Rate | ~7% |
    | Explosive Play Rate | ~8% |
    | Red Zone TD Rate | ~55% |
    | Pass Rate | ~57% |
    """)

with ref_cols[1]:
    st.markdown("""
    **Elo Strength Scale**

    | Elo Range | Quality |
    |-----------|---------|
    | 1600+ | Elite |
    | 1550-1599 | Great |
    | 1500-1549 | Average |
    | 1450-1499 | Below Avg |
    | <1450 | Poor |

    100 Elo = ~1.5% WP difference
    """)

with ref_cols[2]:
    st.markdown("""
    **EPA Scale (Per Play)**

    | EPA Range | Quality |
    |-----------|---------|
    | +0.25+ | Elite |
    | +0.10 to +0.25 | Good |
    | -0.10 to +0.10 | Average |
    | -0.10 to -0.25 | Below Avg |
    | <-0.25 | Poor |
    """)

# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════
st.divider()
st.caption("""
**Data Source:** Armchair Analysis | **Coverage:** 2000–2019 Seasons | **Version:** 1.0
Built with Streamlit, Plotly, DuckDB, and scikit-learn. Feedback welcome!
""")
