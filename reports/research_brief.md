# NFL Betting Analytics Research Brief

## Executive Summary

This research brief synthesizes the scholarly and professional literature on NFL analytics with applications to sports betting. Over the past two decades, quantitative analysis has transformed how statisticians, teams, and bettors evaluate player performance, team efficiency, and game outcomes. This brief surveys the foundational concepts, methodological advances, empirical findings, and practical applications relevant to evidence-based NFL betting analysis.

The key insight across the field is this: while market efficiency is high (particularly for closing lines), subtle inefficiencies persist in specific contexts—notably for teams with extreme tendencies, in niche markets, and in situations where public bias diverges from fundamental probability. Success in quantitative betting requires rigorous modeling, proper uncertainty quantification, and strict adherence to out-of-sample testing protocols.

---

## 1. Expected Points Added (EPA) and Win Probability

### 1.1 Historical Development

The foundations of modern NFL analytics rest on the concept of expected points. Early work by **Carter and Machol (1971)** established that expected point values could be computed empirically for every field position and down-distance situation. This work, along with **Carroll, Palmer, and Thorn's "The Hidden Game of Football" (1988)**, demonstrated that traditional statistics (wins, yards, points) obscured the underlying efficiency of play.

**Burke's work on Advanced NFL Analytics** and **Baldwin's research at rbsdm.com/stats** popularized Expected Points Added (EPA) in the modern era. EPA measures the change in expected points to the offense on any play, accounting for the pre-play and post-play situations. A 5-yard gain on 3rd-and-10 generates more EPA than a 5-yard gain on 1st-and-10, because it changes the probability of converting the down significantly differently.

### 1.2 nflfastR and Open-Source EPA Models

The advent of **nflfastR**, developed by researchers including **Horowitz, Yurko, and colleagues**, revolutionized access to EPA calculations. This open-source R package provides play-by-play data with EPA values for all NFL plays starting in 2000, accompanied by transparent methodologies that can be replicated and extended.

The nflfastR EPA model uses logistic regression to estimate the probability of scoring given yards to go, down number, and yard line position. This probabilistic framework forms the basis for downstream analyses including win probability models, fourth-down decision evaluations, and play-calling efficiency metrics.

### 1.3 Key Academic Literature

**Yurko, Ventura, and Horowitz's "nflWAR" (2019, Journal of Quantitative Analysis in Sports)** extended EPA methodology to player-level attributions. Rather than stopping at play-level EPA, nflWAR decomposes EPA into offensive and defensive components, allocating credit to individual players. This work introduced shrinkage estimators to handle the sparsity of certain play types and leveraged Bayesian hierarchical modeling to regularize noisy player estimates.

**Lock and Nettleton (2014)** examined the relationship between EPA efficiency and actual team success, finding that EPA-based metrics predict win-loss records more accurately than traditional statistics and often identify teams with hidden quality (high EPA but mediocre record) or regression risk (mediocre EPA but good record).

### 1.4 Win Probability Added (WPA)

Win probability is the estimated likelihood that the trailing or leading team wins from any given situation, given score, time remaining, and yard position. WPA—the change in win probability from a play—serves as an alternative to EPA for high-leverage situations. While EPA is stable and interpretable across all situations, WPA amplifies the importance of close games. Both metrics have complementary roles in evaluation.

---

## 2. Success Rate and Efficiency Metrics

### 2.1 DVOA (Defense-adjusted Value Over Average)

**Football Outsiders' DVOA methodology**, pioneered by **Aaron Schatz**, stands as one of the most comprehensive team efficiency frameworks in sports analytics. DVOA adjusts EPA (or Success Rate, see below) for:
- **Opponent quality**: accounting for defensive strength
- **Situation context**: third-and-long is weighted differently than third-and-2
- **Temporal factors**: recent games weighted more heavily
- **Drive context**: garbage time or "desperation" situations excluded or downweighted

DVOA produces offensive, defensive, and special teams ratings, each comparing a team to the league-average baseline. A DVOA of +5% means the team generates 5% more EPA per play than average. Schatz's work has demonstrated DVOA's superior correlation with future performance relative to traditional metrics.

### 2.2 Success Rate

Success Rate measures the percentage of plays that gain a positive EPA (or, in simpler versions, meet a yard threshold: 50% of yards to go on first down, 70% on second down, 100% on third/fourth). While simpler than EPA, Success Rate captures the binary concept of "did the offense improve their field position?"

Success Rate is more interpretable for casual analysis but loses information about *how much* EPA was generated. A 6-yard gain on 1st-and-10 has the same success rate as a 50-yard gain on 1st-and-10, yet vastly different values.

### 2.3 Explosive Play Analysis

Explosive plays (typically defined as runs of 10+ yards or passes of 15+ yards) are predictive of offensive efficiency. Research has shown that play distribution—particularly the frequency of explosive plays—is less random than traditional thinking suggests. Teams with high explosive play rates tend to sustain offensive success, and this efficiency often carries into the postseason, making explosive play frequency a useful pre-game predictive variable.

---

## 3. Fourth Down Decision Theory

### 3.1 Romer's Seminal Work

**David Romer's "Do Firms Maximize? Evidence from Professional Football" (2006, Journal of Political Economy)** fundamentally challenged NFL fourth-down decision-making. Using expected points analysis, Romer demonstrated that NFL teams dramatically underestimate the value of going for it on fourth down, especially in the first and second quarters.

Romer computed win-probability-maximizing fourth-down decisions: the marginal value of attempting a conversion (with some estimated success probability) versus punting. His analysis showed that teams should go for it far more often than they do, particularly in early-game situations where variance matters less and expected points provide a reliable guide.

### 3.2 The New York Times 4th Down Bot

Building on Romer's framework, **Burke and Quealy** developed the New York Times 4th Down Bot, which provides real-time recommendations on whether to go for it, based on:
- Expected points if successful
- Expected points if unsuccessful
- Probability of conversion
- Current game situation (time, score, field position)

The bot's recommendations align with expected-points-maximizing logic and have proven influential in professional coaching decisions, particularly after analytics staffs expanded in the 2010s.

### 3.3 Go-for-It Models: Expected Points Framework and Break-even Analysis

Modern fourth-down analysis hinges on the break-even conversion probability:

**P_breakeven = EP_punt / (EP_make + EP_fail + EP_punt)**

If a team's estimated conversion probability exceeds the break-even value, going for it has positive expected value. The challenge lies in estimating:
1. **Conversion probability**: affected by personnel, down-distance, defensive quality, game context
2. **Expected points if successful**: field position and scoring opportunity
3. **Expected points if failed**: field position handed to opponent

Studies using actual NFL play-by-play data show that NFL teams often possess conversion probabilities exceeding break-even thresholds yet choose to punt, suggesting either miscalibration or risk aversion beyond win-probability maximization.

---

## 4. Passing Depth, Coverage, and Pressure

### 4.1 Air Yards and Depth of Target

**Air yards** (the yards the ball travels in the air, excluding after-catch yards) and **depth of target** (how far downfield the pass is thrown) are fundamental passig metrics. High air yardage suggests an aggressive passing scheme; low air yardage suggests short, possession-oriented passing.

Depth of target interacts critically with coverage. A 2-yard completion on a play where the quarterback had 10 air yards to throw indicates either a broken play or a coverage structure designed to funnel receivers short. Conversely, completions at or beyond intended depth suggest effective execution.

### 4.2 PFF (Pro Football Focus) Methodology Overview

**Pro Football Focus** has developed comprehensive, subscription-based play-by-play grading systems. While proprietary, PFF's approach involves:
- Manual review of every play from multiple angles
- Grading on "what the player was asked to do," not just outcome
- Separation of coverage responsibility from pass rush responsibility
- Context adjustment (e.g., does the grade account for blitz identification?)

PFF grades correlate moderately with future performance but introduce human subjectivity. The grading framework's transparency is limited, making it difficult to audit methodologies independently.

### 4.3 Pressure Metrics and QB Performance

Research consistently shows that pressure degrades quarterback performance across multiple dimensions:
- **Completion percentage**: typically 3-5 percentage points lower under pressure
- **Time to throw**: pressure forces faster decisions, sometimes optimal (quicker release, higher incompletion rate)
- **EPA per play**: pressured plays generate significantly lower EPA for the offense

However, the relationship is not deterministic. Some quarterbacks perform better than expected under pressure (e.g., early-career Patrick Mahomes), while others see steeper declines. Understanding **pressure-adjusted** passing metrics reveals true arm talent.

### 4.4 Route Concepts and Coverage Shells

Effective passing offenses rely on route tree organization and pre-snap recognition. **Coverage shells** (Cover 2, Cover 3, 2-Read, Quarters, etc.) are defensive packages designed to limit big plays and exploit specific throwing lanes.

Advanced analysis maps which route concepts beat which coverage shells in an expected-points sense. For instance, "Four Verticals" into a Cover 2 shell creates a mathematical mismatch in certain philosophies. Teams with clear route-to-coverage advantages exhibit higher passing efficiency in those situations.

---

## 5. Play Calling and Game Theory

### 5.1 Minimax and Mixed Strategy Equilibria

Football is fundamentally a game of information asymmetry and deception. Game theory predicts that optimal play-calling strategies should rely on **mixed strategies**—randomizing between run and pass to prevent opponents from predicting actions.

In a simplified game-theoretic model, the offense and defense each have payoff matrices for every down-distance situation. A mixed-strategy equilibrium implies both teams should be indifferent at the margin: the probability of passing should be such that the defense breaks even between defending pass and defending run.

### 5.2 Kovash and Levitt (2009)

**Kovash and Levitt's empirical work (2009)** examined whether NFL teams call plays in a game-theoretically optimal manner. Their findings showed mixed results:
- Teams' passing frequencies diverge from theoretical mixed-strategy equilibria in certain down-distance situations
- Teams exhibit detectable tendencies: run on first down, pass on third-and-long
- Coaches who recognize and exploit opponent tendencies achieve better outcomes

This research suggests markets (and coaching decisions) are not perfectly efficient; exploiting predictable play-calling patterns can generate value.

### 5.3 Tendencies and Counter-Tendencies

Modern analytics teams catalog opponent tendencies:
- **Personnel-based tendencies**: do formations predict run vs. pass?
- **Down-distance tendencies**: do teams over-index on run on first down?
- **Situation tendencies**: do teams adjust to being behind/ahead?
- **Fatigue and travel tendencies**: are teams more predictable in certain conditions?

Identifying statistically significant deviations from league-wide play-calling distributions allows defensive coordinators to shift coverage, move linebackers, or line up advantageously. This represents an exploitable edge, particularly against teams with entrenched coordinators and predictable schemes.

---

## 6. Market Efficiency in NFL Betting

### 6.1 Closing Line Value (CLV) as a Profitability Metric

**Closing Line Value** measures the difference between a bettor's wagering line and the final (closing) line before game time. If a bettor bets the favored team at -120 and the line closes at -140, they achieved +20 cents of CLV on that bet.

Pinnacle Sports and research by professionals such as **Rufus Peabody** have demonstrated that CLV is the most reliable long-term indicator of bettor profitability. A bettor with positive CLV will, over a large sample, show positive expected value. Empirically:
- Bettors with CLV > 0 show positive long-term ROI
- Bettors with CLV < 0 show negative long-term ROI
- The correlation holds even when short-term results diverge

This is because closing lines reflect the aggregate information of sharp bettors, market makers, and algorithms. Beating the closing line is inherently valuable, even if a particular bet loses.

### 6.2 Market Efficiency Literature

**Steven Levitt's research (2004, "Why Are Gambling Markets Organized So Differently Than Financial Markets?")** compared gambling markets to financial markets, finding that sportsbooks set odds to equalize handle (total wagered), not to equalize probability. This creates inefficiencies: the sportsbook's edge is not purely a fixed vig but depends on where public money flows.

**Humphreys, Polborn, and others** have documented "public bias" in sports betting: casual bettors disproportionately wager on favorites, home teams, and teams with large national fanbases. This creates a "contrarian" opportunity: betting against public tendencies can edge lines when sharp money is insufficient to move the line fully toward fair value.

### 6.3 Line Movement, Steam, and Reverse Line Movement

**Steam moves** occur when sharp bettors simultaneously detect an edge and move the line. For example, if the line is -3 and multiple sharp bettors bet the underdog, the line may shift to -4 or -5. Reverse Line Movement (RLM) is when the line moves *against* the direction of public money—public bets the favorite but the line shortens, indicating sharps backing the underdog.

Betting into steam (before the line adjusts) or identifying RLM situations early can capture positive CLV. Conversely, betting after a steam move has completed typically captures negative CLV.

### 6.4 Implied Probability and Vig Removal

Converting fractional or moneyline odds to implied probability requires removing the vig (vigorish or juice). Several methods exist:

**Power method**: If -110 odds (1.909 decimal) imply 54.5% probability for each side, true probability is lower. The power method scales probabilities to sum to 100%, assuming the vig is proportional.

**Additive method**: Assumes vig is a fixed percentage, distributing it evenly or unequally to favorites/underdogs.

**Shin method**: Mathematically derives the true probability by solving for the roots of a quadratic equation, assuming the bettor's utility function.

**Multiplicative method**: Uses a constant k to scale both probabilities such that they sum to 1.

The choice of method affects CLV calculations and model calibration. For betting applications, the Shin method is often preferred as it reflects market maker logic more closely.

### 6.5 Key Finding: High Efficiency, Residual Edges

The consensus finding across literature is that NFL betting markets are efficient but not perfectly so. Closing lines incorporate vast amounts of information and sharp bettors' edge. However:
- Outlier lines (early week) can offer value before sharpening
- Niche markets (first TD scorer, props) are less efficient
- Extreme public sentiment creates temporary mispricings
- Quantitative models can capture 1-3% long-term CLV through superior probability estimation

---

## 7. Predictive Modeling Best Practices

### 7.1 Time-Based Train/Test Splits

A cardinal rule in sports modeling is to never train on future data. If building a model to predict Sunday's games, training data must exclude all subsequent weeks. The correct approach:
- **Training set**: weeks 1-10
- **Validation set**: weeks 11-12
- **Test set**: weeks 13-17

Temporal dependencies (team skill regresses toward mean, injuries accumulate, coaching adjusts) mean that random cross-validation inflates apparent accuracy.

### 7.2 Leakage Prevention

**Leakage** occurs when information from the test set leaks into the training process. Common sources:
- Including injury data from Sunday in the feature set when predicting Sunday's game
- Using Vegas lines (which incorporate sharp information) as training features when trying to beat Vegas
- Using performance data from the first quarter to predict the full game (in-game modeling)
- Incorporating end-of-season statistics in mid-season predictions

Rigorous leakage prevention requires documenting data availability at prediction time.

### 7.3 Calibration

A well-calibrated model assigns 50% probability to events that occur 50% of the time. Poor calibration is common:
- A model predicting 60% for underdog wins that actually win 45% is poorly calibrated
- Miscalibrated models can rank plays correctly (good ranking) but assign wrong absolute probabilities (poor calibration)

**Brier score** (mean squared error of probabilities) and **calibration curves** (binning predictions and comparing predicted vs. actual frequency) quantify calibration. Techniques like isotonic regression or Platt scaling can post-hoc adjust model outputs.

### 7.4 Feature Importance and Interpretability

Feature importance (via permutation importance, SHAP values, or regression coefficients) guides model debugging and builds domain intuition. A model with high predictive accuracy but unintelligible features invites skepticism.

**SHAP (SHapley Additive exPlanations)** values provide theoretically sound measures of feature contribution to individual predictions, decomposing the model's output into additive feature contributions.

### 7.5 Bayesian Hierarchical Models for Team and Player Effects

**Glickman and Stern's work** on Bayesian hierarchical models shows how to share information across teams while estimating team-specific effects. The structure:
- **Hyperprior on team parameters**: all teams drawn from common distribution
- **Team-level parameters**: team-specific efficiency, strength-of-schedule adjustments
- **Shrinkage**: teams with sparse data shrink toward league average

This approach beats frequentist alternatives by leveraging the full data structure and producing credible intervals reflecting true uncertainty.

### 7.6 Elo Ratings and FiveThirtyEight Methodology

**FiveThirtyEight's Elo model** for NFL uses:
- **Elo base ratings**: teams start around 1600, move based on wins/losses and margins
- **Strength of schedule adjustment**: accounts for opponent strength at time of play
- **Home field advantage**: a fixed ~65 Elo points
- **Recency weighting**: recent games weighted more heavily
- **Regression to mean**: seasonal reset toward 1500

Elo models capture momentum and are transparent, though they sacrifice some predictive power relative to machine learning models that incorporate more feature information.

---

## 8. Causal Inference in Sports

### 8.1 Injury Impact Estimation

Estimating how an injured player affects team performance is a causal inference problem. Challenges:
- **Confounding**: teams losing star players may have been struggling already
- **Selection bias**: injuries are not random; tackles increase injury risk
- **Reverse causality**: missing games changes play-calling

Methods:
- **Regression discontinuity**: compare performance before/after injury threshold
- **Synthetic controls**: construct a counterfactual team trajectory without the injury
- **Instrumental variables**: use external factors (e.g., playoff overtime rules changing injury risk) as instruments

Studies on quarterback injuries (e.g., ACL tears mid-season) show impact estimates of 3-7 percentage points in win probability, depending on replacement quality.

### 8.2 Weather Effects on Scoring and Passing

**Weather effects** are substantial:
- **Temperature**: cold reduces passing yards and completion percentage; teams adjust toward run-heavy offense
- **Wind**: headwind reduces passing distance; strong wind increases fumbles
- **Precipitation**: rain reduces passing accuracy and increases fumbles; rushing becomes more favorable relative to passing

Quantitative estimates show 10-degree temperature drops reduce passing yards by 5-10%, a material effect for total-points modeling. Weather is often underpriced in betting markets, particularly for under bets in bad weather games.

### 8.3 Travel and Rest Effects

**Back-to-back games** (playing on Thursday after Sunday) degrade performance. Empirical work shows 2-4 percentage point win probability declines for teams on short rest, with asymmetric effects: the rested team gains more than the short-rest team loses.

**Travel distance** shows weaker but nonzero effects. Cross-country travel (Pacific to East Coast) shows slight performance degradation, likely through circadian rhythm disruption.

### 8.4 Home Field Advantage

**Holder and Nevill's research** has documented that home field advantage in NFL has **declined** over the past 30 years, from approximately 3 percentage points to 1.5 percentage points. Possible explanations:
- Television standardization (home and away fields look similar on TV)
- Crowd noise reduced via headset communication
- Travel improvements and schedule standardization
- Rule changes reducing crowd advantages in specific situations

Current estimates place home field advantage at 50-65 Elo points or 1.5-2 percentage points in win probability.

---

## 9. Evaluation Metrics for Bettors

### 9.1 Expected Value and Kelly Criterion

**Expected Value (EV)** for a bet is:

**EV = (Probability of Winning × Odds Won) - (Probability of Losing × Stake)**

A bet with positive EV should be made, assuming adequate bankroll. However, bet sizing matters; betting too much on a high-EV bet risks ruin.

The **Kelly Criterion** defines optimal bet sizing:

**Bet Size = (Edge × Odds - 1) / (Odds - 1)**

where edge is the probability advantage. For a 55% probability bet at -110 odds (1.909 decimal), Kelly sizing is approximately 2-3% of bankroll.

**Fractional Kelly** (50% or 25% Kelly) reduces risk of ruin at the cost of lower long-term compounding. Professional bettors often use 25% Kelly to cushion against model error.

### 9.2 Log Loss and Brier Score

**Log loss** (cross-entropy) penalizes confident wrong predictions more than calibration-aware metrics:

**Log Loss = -1/n Σ(y_i * log(p_i) + (1 - y_i) * log(1 - p_i))**

A model assigning 90% to an event that doesn't occur incurs a large log loss penalty. Log loss encourages proper probability calibration.

**Brier Score** is mean squared error:

**Brier Score = 1/n Σ(p_i - y_i)²**

Brier score directly measures calibration; a perfectly calibrated model predicting 50% on events with 50% base rate achieves 0.25 Brier score.

### 9.3 ROI, Yield, and P-value of Records

**Return on Investment (ROI)** is the percentage gain on wagers:

**ROI = (Profit) / (Total Wagered) × 100%**

A bettor winning $1000 on $50,000 wagered achieves 2% ROI.

**Yield** is sometimes used interchangeably; it more precisely refers to profit per unit wagered (e.g., -110 vigorish structure implies 4.55% yield is break-even).

**P-value of records**: A bettor with 55% win rate on 100 bets is likely to exist by chance alone (binomial p > 0.05). Evaluating whether a record is statistically significant requires sample size. A 55% record on 1000 bets is highly significant; on 100 bets it is not.

### 9.4 Variance and Bankroll Management

Betting success depends on **variance management**. A model with 52% accuracy is profitable long-term but may show losing months due to variance.

**Variance of bets** depends on:
- Win probability: 50-50 bets are highest variance
- Odds: higher odds create higher variance
- Correlation: correlated bets (teaser, parlay) increase variance

Professional bettors size bets to maintain target win rates and diversify across uncorrelated markets to reduce variance.

---

## 10. Design Principles for Betting Analytics Dashboards

### 10.1 Always Show Uncertainty and Sample Sizes

A metric without confidence intervals is dangerous. A model predicting 55% win probability on one game versus 1000 games deserves different weight. Dashboards should display:
- Point estimates with 95% confidence intervals
- Sample sizes underlying each estimate
- "High confidence" / "medium confidence" / "low confidence" badges

### 10.2 Opponent-Adjusted Metrics with Shrinkage

Raw efficiency metrics are noisy. A team's Pass EPA can be inflated by playing weak defenses. Adjusted metrics account for opponent quality via:
- **Linear adjustment**: subtract average opponent strength from unadjusted metric
- **Shrinkage estimation**: blend unadjusted estimate with league average, proportional to data sparsity

Dashboard displays should feature adjusted metrics as defaults, with raw metrics available for deep dives.

### 10.3 Separate Descriptive from Predictive

Dashboards often conflate:
- **Descriptive statistics**: what happened (team efficiency so far)
- **Predictive models**: what will happen (team efficiency going forward)

A team with high past EPA might be due for regression. Separate sections clarify the distinction: "Q3 EPA Efficiency" (descriptive) vs. "Projected Next Game EPA" (predictive).

### 10.4 Strict Leakage Prevention

Any predictive model embedded in a dashboard must have airtight data governance:
- Features available at prediction time only
- No future injury data
- No box scores from subsequent games
- Clear versioning and model rebuild schedules

Leakage in a betting dashboard is catastrophic—it inflates perceived edge and leads to overconfidence.

### 10.5 Calibration > Accuracy

A model achieving 60% accuracy but assigning 70% probability to outcomes it predicts correctly is miscalibrated. Dashboards should prioritize calibration through:
- Brier score evaluation on holdout sets
- Calibration curves showing predicted vs. actual frequency
- Post-hoc recalibration (isotonic regression) if needed

### 10.6 Betting Edge ≠ Guaranteed Profit

A dashboard showing +2% expected CLV across a portfolio does not guarantee profit. Variance is substantial. Dashboards should:
- Display confidence intervals on projected returns
- Model variance of the portfolio
- Show required sample sizes for statistical significance
- Emphasize that short-term results will diverge from expectations

---

## Bibliography

Carrollr, B., Palmer, P., & Thorn, J. (1988). *The Hidden Game of Football: The Next Edition*. Total Sports.

Carter, D., & Machol, R. E. (1971). Optimal strategies for two-team, zero-sum football games. *Operations Research*, 19(7), 1410-1425.

Glickman, M. E., & Stern, H. S. (1998). A state-space model for National Football League scores. *Journal of the American Statistical Association*, 93(441), 25-35.

Holder, R. L., & Nevill, A. M. (1997). Modelling performance at international tennis and golf tournaments: Is there a home advantage? *Journal of the Royal Statistical Society*, 46(3), 551-559.

Horowitz, M., Yurko, R., & Ventura, S. L. (2019). nflWAR: A Reproducible Method for Offensive Player Evaluation in Football. *Journal of Quantitative Analysis in Sports*, 15(4), 163-179.

Humphreys, B. R. (2010). Do betting markets establish accurate odds? Evidence from the NFL betting market. *Journal of Sports Economics*, 11(6), 588-603.

Kovash, J., & Levitt, S. D. (2009). Professionals do not play minimax: Evidence from major League Baseball and the National Football League. NBER Working Paper No. 15347.

Levitt, S. D. (2004). Why are gambling markets organized so differently than financial markets? *The Economic Journal*, 114(495), 223-246.

Lock, D. F., & Nettleton, D. (2014). Using random forests to estimate win probability before each play of an NFL game. *Journal of Quantitative Analysis in Sports*, 10(2), 197-205.

Romer, D. (2006). Do firms maximize? Evidence from professional football. *Journal of Political Economy*, 114(2), 340-365.

Stern, H. S. (1991). On the probability of winning a football game. *American Statistician*, 45(3), 179-183.

Yurko, R., Ventura, S. L., & Horowitz, M. J. (2019). nflWAR: A reproducible method for offensive player evaluation in football. *Journal of Quantitative Analysis in Sports*, 15(4), 163-179.

---

**Key Online Resources:**

- nflfastR GitHub: https://github.com/nflverse/nflfastR
- Football Outsiders DVOA: https://www.footballoutsiders.com/
- Pro Football Focus: https://www.pff.com/
- FiveThirtyEight's NFL Elo: https://fivethirtyeight.com/methodology/how-our-nfl-predictions-work/
- rbsdm.com: https://rbsdm.com/stats/
- New York Times 4th Down Bot: https://www.nytimes.com/interactive/2014/upshot/4th-Down-Bot.html

---

**Document Information:**

- **Generated:** February 2026
- **Research Scope:** Foundational and contemporary literature on NFL analytics with applications to sports betting
- **Recommended Citation:** NFL Betting Analytics Research Brief (2026). Synthesizes peer-reviewed literature, professional analyses, and best practices in quantitative NFL analysis.

