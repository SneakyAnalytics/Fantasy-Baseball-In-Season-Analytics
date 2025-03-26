# ESPN Fantasy Baseball Analyzer

A comprehensive analysis tool for ESPN Fantasy Baseball leagues. This tool connects to the ESPN Fantasy API to extract data from your league, process it, and generate actionable insights to help with fantasy baseball decision-making.

## Features

### Team Analysis

- Connect to ESPN Fantasy Baseball API
- Retrieve league, team, and player data
- Analyze team standings and performance metrics
- Generate team comparison reports
- Visualize team standings and win percentages
- Compare strength across divisions

### Player Analysis

- Track player statistics and performance
- Identify top performers by position
- Compare players head-to-head
- Analyze roster composition
- Generate player reports with key statistics
- Visualize player performance metrics

### Fantasy Insights

- Identify undervalued and overperforming players
- Analyze position scarcity
- Find potential trade targets
- Monitor projected player performance
- Track top projected players by position

### Visualization

- Team standings bar charts
- Win percentage visualizations
- Position comparison charts
- Player performance metrics

## Getting Started

### Prerequisites

- Python 3.8 or higher
- ESPN Fantasy Baseball league ID
- For private leagues: ESPN_S2 and SWID cookies

### Installation

1. Clone the repository:
   git clone https://github.com/SneakyAnalytics/Fantasy-Baseball-In-Season-Analytics.git
   cd Fantasy-Baseball-In-Season-Analytics

2. Create a virtual environment and activate it:
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install dependencies:
   pip install -r requirements.txt

4. Create a `.env` file with your league information:
   LEAGUE_ID=12345
   YEAR=2025
   ESPN_S2=your_espn_s2_cookie # For private leagues
   SWID=your_swid_cookie # For private leagues

5. Run the setup script:
   python scripts/setup.py

## Usage

### Team Analysis

Generate a team analysis report with visualizations:
python scripts/team_analysis.py

### Player Analysis

Generate a player analysis report:
python scripts/player_analysis.py

Analyze players at a specific position:
python scripts/player_analysis.py --position "SP"

Analyze a specific team's roster:
python scripts/player_analysis.py --team-id YOUR_TEAM_ID

### Fantasy Insights

See top projected players:
python scripts/fantasy_insights.py --projections

Find top projected players at a specific position:
python scripts/fantasy_insights.py --projections --position-filter "SP"

Find potential waiver wire targets:
python scripts/fantasy_insights.py --waiver

## Advanced Player Analysis

Analyze player trends using advanced Statcast metrics:
```
python scripts/player_trends.py
```

Analyze a specific player's advanced metrics:
```
python scripts/player_trends.py --player "Juan Soto"
```

Find trending batters only:
```
python scripts/player_trends.py --player-type batter
```

# Matchup Analysis & Reporting Features

## New Features

The Fantasy Baseball Analyzer now includes automated matchup analysis and reporting features:

### Weekly Matchup Preview

A comprehensive analysis of your upcoming matchup, including:

- Position-by-position projections and advantages
- Optimal pitcher start recommendations
- Acquisition recommendations based on team needs
- Overall matchup projection

### Daily Updates

Stay on top of your fantasy baseball team with daily updates:

- Yesterday's performance summary
- Current matchup status
- Streaming pitcher recommendations for upcoming games
- Hot waiver wire pickups

## Getting Started

1. First, identify your team ID by running:

   ```
   python scripts/find_team_id.py
   ```

2. Add your team ID to the config/settings.py file:

   ```python
   MY_TEAM_ID = 12345  # Replace with your actual team ID
   ```

3. Generate a weekly matchup preview:

   ```
   python scripts/matchup_preview.py
   ```

4. Generate a daily update report:
   ```
   python scripts/daily_update.py
   ```

## Customization

You can customize report settings in config/settings.py:

- MAX_PITCHER_STARTS: Maximum number of pitcher starts per matchup (default: 12)
- MAX_ACQUISITIONS_PER_MATCHUP: Maximum player acquisitions per matchup (default: 8)

## Automation

To automate these reports:

### On Windows:

Use Task Scheduler to run the scripts at specific times:

- Weekly preview: Run every Monday morning
- Daily update: Run every morning at 6:00 AM

### On Mac/Linux:

Use cron jobs to run the scripts automatically:

1. Weekly preview every Monday at 6:00 AM:

   ```
   0 6 * * 1 cd /path/to/Fantasy-Baseball-In-Season-Analytics && python scripts/matchup_preview.py
   ```

2. Daily update every day at 6:00 AM:
   ```
   0 6 * * * cd /path/to/Fantasy-Baseball-In-Season-Analytics && python scripts/daily_update.py
   ```

## Sharing Reports

Reports are saved to the 'output' directory by default. You can:

- Email reports to your co-owner (email functionality coming soon)
- Share the output directory through Dropbox, Google Drive, etc.
- Set up a simple web dashboard (future enhancement)

## Project Structure

Fantasy-Baseball-In-Season-Analytics/
│
├── config/ # Configuration files
├── src/ # Source code
│ ├── api/ # ESPN API client
│ ├── data/ # Data models and processing
│ ├── analysis/ # Analysis modules
│ └── visualization/ # Visualization tools
├── scripts/ # Utility scripts
└── tests/ # Tests

## Future Enhancements

- Advanced statistical projections
- Prospect tracking and call-up monitoring
- Statistical indicators for breakout players
- Weekly automated reports
- Custom scoring analysis

## License

This project is licensed under the MIT License - see the LICENSE file for details.
