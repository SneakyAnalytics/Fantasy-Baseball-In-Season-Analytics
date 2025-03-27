# scripts/visualization_demo.py
import os
import sys
import logging
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path to ensure imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import after fixing path
from src.data.models import Team, Player, Owner
from src.analysis.category_analysis import CategoryAnalyzer
from src.visualization.category_charts import CategoryVisualizer
from src.visualization.trend_charts import TrendVisualizer
from src.visualization.charts import TeamVisualizer
from src.visualization.player_charts import PlayerVisualizer
from src.api.client import ESPNFantasyClient
from config.settings import LEAGUE_ID, TEAM_ID, ESPN_S2, SWID

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_dummy_data():
    """Create dummy data for visualization demonstration."""
    
    # 1. Create dummy teams
    teams = []
    
    # Team names - baseball themed
    team_names = [
        "Sluggers United", "Diamond Kings", "Pitching Aces", 
        "Home Run Heroes", "Batters Box", "Wild Pitchers",
        "Base Stealers", "Extra Innings", "Bullpen Masters", 
        "Grand Slammers"
    ]
    
    for i in range(10):
        team = Team(
            team_id=i+1,
            name=team_names[i],
            abbreviation=team_names[i].split()[0][:3].upper(),
            owners=[Owner(id=str(i+1), display_name=f"Owner {i+1}", first_name="Owner", last_name=str(i+1))],
            division_id=1 if i < 5 else 2,
            division_name="East" if i < 5 else "West",
            standing=i+1,
            wins=80 - i*3 + np.random.randint(-5, 5),
            losses=40 + i*3 + np.random.randint(-5, 5),
            ties=0,
            roster=create_dummy_roster(i+1)
        )
        teams.append(team)
    
    return teams

def create_dummy_roster(team_id):
    """Create a dummy roster for a team."""
    roster = []
    
    # Create a mix of positions
    positions = {
        1: "C", 2: "1B", 3: "2B", 4: "3B", 5: "SS", 
        6: "OF", 7: "OF", 8: "OF", 9: "UTIL", 10: "UTIL",
        11: "SP", 12: "SP", 13: "SP", 14: "RP", 15: "RP",
        16: "P", 17: "P", 18: "P", 19: "P", 20: "P"
    }
    
    # First names and last names for random player generation
    first_names = ["Mike", "Juan", "Aaron", "Shohei", "Fernando", "Mookie", "Freddie", 
                  "Bryce", "José", "Gerrit", "Clayton", "Jacob", "Max", "Walker", "Trea"]
    
    last_names = ["Smith", "Johnson", "García", "Rodríguez", "Martínez", "Jones", "Trout", 
                 "Ohtani", "Tatís", "Betts", "Freeman", "Harper", "Ramírez", "Cole", "Scherzer"]
    
    # Create players
    for i in range(1, 21):
        name = f"{np.random.choice(first_names)} {np.random.choice(last_names)}"
        position = positions[i]
        
        # Different stat distributions for batters vs pitchers
        if "SP" in position or "RP" in position or "P" in position:
            # Pitcher stats
            era = max(0.5, 3.5 + np.random.normal(0, 1))
            whip = max(0.7, 1.2 + np.random.normal(0, 0.2))
            wins = int(np.random.randint(5, 15))
            strikeouts = int(np.random.randint(50, 200))
            innings = int(np.random.randint(50, 180))
            saves = int(np.random.randint(0, 20)) if "RP" in position else 0
            
            # Normalize stats by team quality
            team_factor = (10 - team_id) / 10  # Better teams (lower ID) have better stats
            era *= (1.2 - team_factor * 0.4)
            whip *= (1.1 - team_factor * 0.2)
            wins = int(wins * (0.8 + team_factor * 0.4))
            
            stats = {
                "ERA": era,
                "WHIP": whip,
                "W": wins,
                "SV": saves,
                "K": strikeouts,
                "IP": innings,
                "K/9": strikeouts * 9 / innings if innings > 0 else 0,
                "BB/9": (whip - 1) * 9 * 0.7  # Rough approximation
            }
        else:
            # Batter stats
            avg = max(0.2, min(0.35, 0.26 + np.random.normal(0, 0.03)))
            hr = int(np.random.randint(5, 35))
            runs = int(np.random.randint(30, 100))
            rbi = int(np.random.randint(30, 100))
            sb = int(np.random.randint(0, 25))
            obp = avg + 0.07 + np.random.normal(0, 0.02)
            slg = avg + 0.1 + hr * 0.01
            
            # Normalize stats by team quality
            team_factor = (10 - team_id) / 10  # Better teams (lower ID) have better stats
            avg *= (0.9 + team_factor * 0.2)
            hr = int(hr * (0.8 + team_factor * 0.4))
            runs = int(runs * (0.8 + team_factor * 0.4))
            rbi = int(rbi * (0.8 + team_factor * 0.4))
            
            stats = {
                "AVG": avg,
                "HR": hr,
                "R": runs,
                "RBI": rbi,
                "SB": sb,
                "OBP": obp,
                "SLG": slg,
                "OPS": obp + slg
            }
        
        # Create player
        player = Player(
            playerId=team_id * 100 + i,
            name=name,
            proTeam=np.random.choice(["LAD", "NYY", "HOU", "CHC", "ATL", "BOS", "NYM", "SDP", "PHI", "TOR"]),
            eligibleSlots=[position],
            stats=stats
        )
        roster.append(player)
    
    return roster

def create_dummy_trending_data(player_name, stat, days=30, base_value=0.280, volatility=0.02, 
                              trend=0.0005, has_expected=False):
    """Create dummy trending data for a player."""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    dates = []
    values = []
    expected_values = []
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        
        # Calculate value with random noise and trend
        days_passed = (current_date - start_date).days
        trend_component = trend * days_passed
        random_component = np.random.normal(0, volatility)
        
        value = base_value + trend_component + random_component
        values.append(max(0, value))  # Ensure non-negative
        
        # Add expected values if requested
        if has_expected:
            # Expected values typically have less volatility but follow actual performance
            expected_value = base_value + trend_component + np.random.normal(0, volatility * 0.5)
            expected_values.append(max(0, expected_value))
        
        current_date += timedelta(days=1)
    
    if has_expected:
        return dates, values, expected_values
    else:
        return dates, values

def generate_league_distribution(mean_value, std_dev, sample_size=100, min_value=0):
    """Generate a simulated league distribution for a statistic."""
    values = np.random.normal(mean_value, std_dev, sample_size)
    return [max(min_value, v) for v in values]  # Ensure all values are at least min_value

def main():
    """Demonstrate the visualization capabilities."""
    parser = argparse.ArgumentParser(description='Demonstrate visualization capabilities')
    parser.add_argument('--use_espn', action='store_true', 
                      help='Use actual ESPN data instead of dummy data')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Get team data
    if args.use_espn and ESPN_S2 and SWID:
        logger.info("Using real ESPN Fantasy data")
        try:
            client = ESPNFantasyClient(LEAGUE_ID, ESPN_S2, SWID, year=2025)
            teams = client.get_teams()
            logger.info(f"Retrieved {len(teams)} teams from ESPN")
        except Exception as e:
            logger.error(f"Error retrieving ESPN data: {e}")
            logger.info("Falling back to dummy data")
            teams = create_dummy_data()
    else:
        logger.info("Using dummy data for demonstration")
        teams = create_dummy_data()
    
    # 1. Team Visualization Demo
    logger.info("Generating team visualizations...")
    team_visualizer = TeamVisualizer()
    team_visualizer.visualize_standings(teams)
    team_visualizer.visualize_win_percentage(teams)
    team_visualizer.visualize_division_comparison(teams)
    
    # 2. Player Visualization Demo
    logger.info("Generating player visualizations...")
    player_visualizer = PlayerVisualizer()
    
    # Flatten all players from all teams
    all_players = []
    for team in teams:
        if team.roster:
            all_players.extend(team.roster)
    
    # Generate visualizations if players available
    if all_players:
        player_visualizer.visualize_top_players(all_players, "HR", limit=10)
        player_visualizer.visualize_top_players(all_players, "AVG", limit=10)
        player_visualizer.visualize_top_players(all_players, "ERA", limit=10, ascending=True)
        player_visualizer.visualize_position_comparison(all_players, "OPS")
        
        # Player comparison if at least 2 players
        if len(all_players) >= 2:
            player_visualizer.visualize_player_comparison(
                all_players[0], all_players[1], 
                ["AVG", "HR", "RBI", "R", "SB", "OPS"]
            )
    
    # 3. Category Analysis Visualization Demo
    logger.info("Generating category analysis visualizations...")
    
    category_analyzer = CategoryAnalyzer(teams)
    category_visualizer = CategoryVisualizer()
    
    # Analyze first team's categories
    if teams:
        team_analysis = category_analyzer.analyze_team_categories(teams[0].team_id)
        category_visualizer.visualize_category_strengths(team_analysis)
        category_visualizer.visualize_category_strengths(team_analysis, category_type="batting", 
                                                      filename="batting_strengths.png")
        category_visualizer.visualize_category_strengths(team_analysis, category_type="pitching", 
                                                      filename="pitching_strengths.png")
        
        # Generate a ranking visualization
        try:
            category_visualizer.visualize_category_rankings(category_analyzer, "HR", "batting")
            category_visualizer.visualize_category_rankings(category_analyzer, "ERA", "pitching")
        except ValueError as e:
            logger.warning(f"Could not create rankings: {e}")
        
        # Create improvement recommendations visualization with free agents
        free_agents = create_dummy_roster(99)  # Dummy free agents
        recommendations = category_analyzer.recommend_category_improvements(teams[0].team_id, free_agents)
        category_visualizer.visualize_improvement_recommendations(recommendations, "batting")
        category_visualizer.visualize_improvement_recommendations(recommendations, "pitching")
    
    # 4. Trend Visualization Demo
    logger.info("Generating trend visualizations...")
    trend_visualizer = TrendVisualizer()
    
    # Generate player trend data for batting average
    player_name = "Mike Trout"
    dates, avg_values = create_dummy_trending_data(player_name, "AVG", days=30, base_value=0.280, 
                                                 volatility=0.02, trend=0.0005)
    trend_visualizer.visualize_player_trend(player_name, "AVG", avg_values, dates)
    
    # Generate trend data with expected stats
    player_name = "Juan Soto"
    dates, avg_values, expected_values = create_dummy_trending_data(player_name, "AVG", days=30, 
                                                                  base_value=0.300, volatility=0.02, 
                                                                  trend=-0.0003, has_expected=True)
    trend_visualizer.visualize_player_trend(player_name, "AVG", avg_values, dates, 
                                          include_expected=True, expected_values=expected_values,
                                          filename="soto_avg_with_expected.png")
    
    # Generate multiple stat rolling averages
    player_name = "Shohei Ohtani"
    dates, hr_values = create_dummy_trending_data(player_name, "HR", days=45, base_value=0.9, 
                                                volatility=0.5, trend=0.01)
    dates, rbi_values = create_dummy_trending_data(player_name, "RBI", days=45, base_value=3.2, 
                                                 volatility=1.2, trend=0.02)
    dates, slg_values = create_dummy_trending_data(player_name, "SLG", days=45, base_value=0.520, 
                                                 volatility=0.03, trend=0.001)
    
    trend_visualizer.visualize_player_rolling_stats(player_name, 
                                                  {"HR": hr_values, "RBI": rbi_values, "SLG": slg_values}, 
                                                  dates, windows=[7, 15, 30])
    
    # Generate stat distribution visualization
    player_name = "Aaron Judge"
    player_value = 42  # HR
    league_values = generate_league_distribution(20, 8, sample_size=100, min_value=5)
    trend_visualizer.visualize_stat_distribution(player_name, "HR", player_value, league_values)
    
    # Generate multi-stat percentile visualization
    player_name = "Freddie Freeman"
    hr_dist = (28, generate_league_distribution(20, 8, sample_size=100, min_value=5))
    avg_dist = (0.315, generate_league_distribution(0.260, 0.025, sample_size=100, min_value=0.200))
    obp_dist = (0.410, generate_league_distribution(0.330, 0.030, sample_size=100, min_value=0.250))
    slg_dist = (0.550, generate_league_distribution(0.430, 0.050, sample_size=100, min_value=0.300))
    
    trend_visualizer.visualize_multistat_comparison(player_name, {
        "HR": hr_dist,
        "AVG": avg_dist,
        "OBP": obp_dist,
        "SLG": slg_dist
    })
    
    logger.info("Visualizations complete! Check the output directory for generated images.")

if __name__ == "__main__":
    main()