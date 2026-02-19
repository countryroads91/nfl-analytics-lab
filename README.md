# Sharp Sports Analysis — NFL Analytics Lab

<p align="center">
  <img src="https://img.shields.io/badge/Seasons-2000--2019-2ECC71?style=flat-square&labelColor=0A0F0D" />
  <img src="https://img.shields.io/badge/Games-5%2C324-2ECC71?style=flat-square&labelColor=0A0F0D" />
  <img src="https://img.shields.io/badge/Plays-873K+-2ECC71?style=flat-square&labelColor=0A0F0D" />
  <img src="https://img.shields.io/badge/Python-3.8+-3498DB?style=flat-square&labelColor=0A0F0D" />
</p>

A research-driven, interactive analytics suite for NFL bettors, quants, and statisticians. Built on 20 seasons (2000-2019) of play-by-play data from Armchair Analysis, powered by DuckDB + Streamlit + Plotly.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the app
streamlit run app/Home.py
```

Then open **http://localhost:8501** in your browser.

**Windows users:** Double-click `run.bat` to auto-install and launch.

## Dashboard Suite (8 Interactive Views)

| Dashboard | Description |
|-----------|-------------|
| **Market & CLV Lab** | ATS analysis, O/U trends, spread calibration, situational betting splits |
| **Efficiency Explorer** | EPA rankings, success rates, down-distance heatmaps, explosive plays |
| **Passing Microstructure** | Depth x location matrix, QB profiles, pressure impact, target distribution |
| **Trenches & Disruption** | Sack rates, pass rush leaders, run direction analysis, OL vs DL matchups |
| **Fourth Down Lab** | Decision analysis, go-for-it success, aggressiveness rankings, what-if simulator |
| **Penalties & Officiating** | Penalty types, team patterns, year-over-year stability analysis |
| **Red Zone DNA** | Scoring efficiency, playcalling tendencies, goal-to-go analysis |
| **Model Workbench** | Elo ratings, spread prediction, feature importance, calibration diagnostics |
| **Glossary & Methods** | Metric definitions, data documentation, bibliography |

## Research Reports

- `reports/research_brief.md` — Comprehensive literature review (30+ citations)
- `reports/market_efficiency_report.md` — Market efficiency analysis
- `reports/fourth_down_decisions_report.md` — Fourth down decision theory
- `reports/penalty_variance_report.md` — Penalty signal vs noise

## Tech Stack

- **Database:** DuckDB (210MB, 50 tables/views)
- **Frontend:** Streamlit with custom CSS theming
- **Charts:** Plotly with dark theme
- **Modeling:** scikit-learn (Elo, logistic regression)
- **Data Pipeline:** CSV -> Parquet -> DuckDB

## Project Structure

```
nfl_analytics/
├── app/
│   ├── Home.py          # Landing page
│   ├── config.py        # Brand palette, chart defaults, shared CSS
│   ├── db.py            # DuckDB connection helper
│   └── pages/           # 9 interactive dashboards
├── data_processed/
│   ├── nfl.duckdb       # Main analytical database
│   └── *.parquet        # Intermediate parquet files
├── reports/             # Research reports
├── src/data/            # Data ingestion pipeline
├── requirements.txt
├── run.bat              # Windows launcher
└── README.md
```

## Methodology

- EPA values pre-computed in source data
- Elo model: K=20, home advantage ~48 pts, 30% season regression
- All predictions use strict time-based train/test splits
- Betting analysis uses closing lines from dataset
- Full citations in `reports/research_brief.md`

## Data Source

Armchair Analysis NFL database (2000-2019). 27 CSV tables covering plays, passes, rushes, drives, games, penalties, sacks, and more.

---

*Sharp Sports Analysis. Not financial advice. All metrics include sample sizes.*
