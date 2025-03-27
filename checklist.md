# Enhanced Fantasy Baseball Analytics Checklist

## Pitching Strategy Enhancements
- [x] **Probable Pitcher Data Integration**
  - [x] Add external API integration for verified probable pitchers schedule
  - [x] Track pitchers' upcoming starts for the matchup week
  - [x] Calculate optimal start distribution based on roster slots and schedule
  
- [x] **Opponent Quality Analysis**
  - [x] Add team offensive rankings data (team OPS, wRC+, etc.)
  - [x] Calculate matchup difficulty scores for each probable start
  - [x] Weigh pitcher performance expectations based on opponent quality

- [x] **Ballpark Factors**
  - [x] Integrate ballpark effects data for hitting/pitching
  - [x] Apply park factors to pitcher projections
  - [x] Identify favorable/unfavorable ballpark scenarios

- [x] **Pitcher Performance Metrics**
  - [x] Add recent performance trends (last 3, 7, 15, 30 days)
  - [x] Include advanced metrics (xFIP, SIERA, K%, etc.)
  - [x] Create composite score for current form

- [x] **Streaming Pitcher Recommendations**
  - [x] Develop algorithm to find best streamers for specific days
  - [x] Factor in ownership percentage and acquisition trends
  - [x] Optimize for limited transactions per week/matchup

## Daily Analysis Enhancements
- [x] **Pickup Trend Analysis**
  - [x] Track ownership percentage changes
  - [x] Monitor recent roster add/drop activity
  - [x] Identify players trending up/down

- [x] **Stats-Based Breakout Identifiers**
  - [x] Calculate performance vs. expected stats
  - [x] Find players with significant K%, BB%, exit velocity changes
  - [x] Implement "breakout score" based on underlying metrics

- [x] **Schedule Analysis**
  - [x] Add team-by-team upcoming schedule analysis
  - [x] Identify favorable hitting matchups (weak pitching staffs, hitter-friendly parks)
  - [x] Calculate "schedule advantage" scores

- [ ] **Player Performance Projections**
  - [ ] Implement custom short-term projections
  - [ ] Weight recent performance more heavily than season stats
  - [ ] Compare projections to consensus industry rankings

## Advanced Analytics
- [x] **Categorical Strength/Weakness Analysis**
  - [x] Analyze team strengths/weaknesses by scoring category
  - [x] Recommend category-specific acquisition targets
  - [x] Suggest trade targets to address categorical weaknesses

- [ ] **Team Construction Analysis**
  - [ ] Evaluate roster construction efficiency
  - [ ] Identify position redundancies and gaps
  - [ ] Suggest optimal bench/active roster allocation

- [ ] **Matchup-Specific Strategy**
  - [ ] Generate opponent-specific strategy recommendations
  - [ ] Identify categorical battles worth prioritizing vs. conceding
  - [ ] Adjust pitcher streaming strategy based on matchup

## Technical Improvements
- [x] **External Data Sources**
  - [x] Add MLB API integration for enhanced stats
    - [x] Create MLB API client with authentication
    - [x] Add endpoints for team/player stats
    - [x] Implement probable starter lookup
    - [x] Add ballpark factors data
  - [x] Integrate Baseball Savant data for advanced metrics
    - [x] Implement web scraper or API client
    - [x] Extract Statcast metrics (exit velocity, barrel %, etc.)
    - [x] Create percentile rankings for key metrics
  - [ ] Add FanGraphs integration for projections
    - [ ] Set up data retrieval method (API/scraping)
    - [ ] Implement advanced metrics (xFIP, SIERA, etc.)
    - [ ] Create normalized projection system
  - [ ] Merge multiple data sources for comprehensive player profiles
    - [x] Create data normalization layer
    - [x] Implement caching system for API data
    - [ ] Build composite player ratings

- [x] **Visualization Enhancements**
  - [x] Create visual matchup comparison dashboards
  - [x] Add performance trend charts
  - [x] Develop player comparison visualizations
  - [x] Implement categorical analysis visualizations
  - [x] Create player trending and statistical distribution charts

- [x] **Automated Delivery**
  - [x] Improve email formatting with HTML templates
  - [x] Set up scheduled report generation
  - [x] Add daily and weekly report delivery with visualizations
  - [ ] Add SMS/push notifications for urgent recommendations