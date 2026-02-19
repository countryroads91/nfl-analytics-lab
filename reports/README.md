# NFL Analytics Suite - Research Reports

This directory contains three research-grade analytical reports analyzing 20 years (2000–2019) of NFL data from the nfl.duckdb database.

## Reports Generated

### 1. Market Efficiency Report
**File**: `market_efficiency_report.md`
**Size**: 13 KB | **Words**: ~2,800

**Key Research Questions**:
- Is the NFL betting market efficient?
- Do systematic patterns exist in spread/total pricing?
- What role does home-field advantage play?
- Are there exploitable weather effects?

**Key Findings**:
- Home teams cover 56.95% of games (3.95 points above 50%)
- Large favorites (14+) cover 79.4%, suggesting underpricing
- Over/under market clusters near 50%, highly efficient
- Dome venues show 3.9pp higher over rates
- Market is largely efficient; vig makes small edges unprofitable

**Data Queried**:
- 5,324 games with spreads and totals
- Season-level trends
- Weather-stratified analysis
- Spread bucket analysis

---

### 2. Fourth Down Decisions Report
**File**: `fourth_down_decisions_report.md`
**Size**: 16 KB | **Words**: ~3,200

**Key Research Questions**:
- Are NFL teams making optimal fourth down decisions?
- How has aggressiveness evolved over 20 years?
- Which teams are most/least aggressive?
- What are conversion success rates by distance?

**Key Findings**:
- Go-for-it rate increased 34% over 20 years (11.5% → 15.4%)
- Red zone conservatism is striking: teams punt 97% on first-and-goal
- Conversion success: 65.4% (0–1 yd), 50.8% (2–3 yd), 30.1% (6+ yd)
- Jacksonville most aggressive (15.51% GFI rate), San Diego most conservative (9.58%)
- Trend aligns with analytics adoption (Romer 2006)

**Data Queried**:
- 83,371 fourth down plays
- Go-for-it vs. punt/FG breakdown
- Field position stratification
- Team-level aggressiveness rankings
- Success rates by yards-to-go

---

### 3. Penalty Variance Report
**File**: `penalty_variance_report.md`
**Size**: 19 KB | **Words**: ~3,500

**Key Research Questions**:
- Are team penalty rates predictable or random?
- Which penalty types show stability?
- How do game situations affect penalties?
- Can penalty rates be exploited for betting?

**Key Findings**:
- Penalties average 7.47 per team per game (range: 6.0–8.9)
- Year-to-year correlation ~0.45, indicating 50% signal, 50% noise
- Close games (within 3 pts) have 36% higher penalty rates (5.64 vs 4.15 PPG)
- 85% of penalties accepted; 11.8% declined
- Oakland most penalized (8.86 PPG), Green Bay least (5.97 PPG)
- Short-term betting edge <1%; insufficient after vig

**Data Queried**:
- 79,527 penalties across 5,324 games
- Team penalty rates (PPG, yards per game)
- Penalty type frequency and stability
- Game situation context (score differential)
- Acceptance/decline rates

---

## Methodology

All reports follow academic research standards:

1. **Data Source**: Primary data from `/sessions/clever-epic-galileo/nfl_analytics/data_processed/nfl.duckdb`
2. **Query Language**: SQL (DuckDB dialect)
3. **Time Period**: 2000–2019 regular season NFL games (5,324 games total)
4. **Sample Sizes**: 
   - Market Efficiency: 5,324 games
   - Fourth Down: 83,371 plays
   - Penalties: 79,527 penalties
5. **Statistical Methods**: Descriptive statistics, time-series trends, correlation analysis, stratification
6. **Limitations**: Documented in each report's "Caveats" section

## Key Databases & Tables Used

| Report | Primary Tables | Records |
|--------|---|---|
| Market Efficiency | games | 5,324 |
| Fourth Down | plays, games, fgxp, punts | 83,371 plays, 6,154 FGs |
| Penalties | penalties, plays, games | 79,527 penalties |

## Citation Format

For academic/professional use:

```bibtex
@report{nfl_analytics_2026,
  author = {Claude Analytics},
  title = {[Report Title]: [Subtitle]},
  institution = {NFL Analytics Suite},
  year = {2026},
  month = {February},
  note = {Data period: 2000--2019, Database: nfl.duckdb}
}
```

Example:
```bibtex
@report{market_efficiency_2026,
  author = {Claude Analytics},
  title = {NFL Market Efficiency: Where (If Anywhere) the Edge Lives},
  institution = {NFL Analytics Suite},
  year = {2026},
  month = {February},
  note = {Analysis of 5,324 games (2000--2019)}
}
```

## Quick Insights Summary

| Topic | Headline | Finding |
|-------|----------|---------|
| **Betting** | Market Efficiency | 56.95% home cover, but near-efficient after accounting for vig |
| **Strategy** | Fourth Down | Go-for-it rates rising (11.5%→15.4%), but red zone still conservative |
| **Discipline** | Penalties | 50% signal, 50% noise; unpredictable short-term |

## Files in Directory

```
reports/
├── market_efficiency_report.md      (13 KB)
├── fourth_down_decisions_report.md  (16 KB)
├── penalty_variance_report.md       (19 KB)
└── README.md                        (this file)
```

## Data Quality Notes

- **Completeness**: >95% (minimal missing values)
- **Time Coverage**: 20 complete NFL seasons (2000–2019)
- **Teams**: All 32 NFL franchises
- **Games**: 5,324 regular season games
- **Known Issues**: 
  - Penalty codes are cipher-based (JP-2400, etc.); descriptions inferred
  - 4.55% of penalties classified as "None" (data quality artifacts)
  - No home/road or referee identity variables

## Next Steps for Users

1. **For Research**: Use reports as literature review citations; consider extending to 2020–2025 data
2. **For Betting**: Extract insights (e.g., dome venue over, fourth down trends) but recognize vig limits
3. **For Coaching**: Use fourth down and penalty analysis to benchmark team strategies
4. **For Analytics Teams**: Use findings as validation of existing models or inspiration for new research

---

**Generated**: February 19, 2026
**Database**: /sessions/clever-epic-galileo/nfl_analytics/data_processed/nfl.duckdb
**Total Analysis**: 168,126 data points (5,324 games + 83,371 plays + 79,527 penalties)
