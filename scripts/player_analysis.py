# scripts/player_analysis.py
#!/usr/bin/env python
"""
Generate a player analysis report.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.api.client import ESPNFantasyClient
from src.analysis.player_analysis import PlayerAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('espn_fantasy.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main function to generate player analysis report."""
    parser = argparse.ArgumentParser(description='Generate a player analysis report')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--team-id', type=int, help='Analyze roster for specific team ID')
    parser.add_argument('--position', help='Filter by position')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Connect to ESPN API
    client = ESPNFantasyClient(
        league_id=settings.LEAGUE_ID,
        year=settings.YEAR,
        espn_s2=settings.ESPN_S2,
        swid=settings.SWID
    )
    
    if not client.connect():
        logger.error("Failed to connect to ESPN API")
        return 1
    
    # Get all rostered players
    teams = client.get_teams()
    all_rostered_players = []
    for team in teams:
        if hasattr(team, 'roster') and team.roster:
            all_rostered_players.extend(team.roster)
    
    # Create player analyzer
    analyzer = PlayerAnalyzer(all_rostered_players)
    
    # Debug player data structure
    if all_rostered_players and len(all_rostered_players) > 0:
        first_player = all_rostered_players[0]
        logger.info("First player attributes:")
        for attr in dir(first_player):
            if not attr.startswith('_') and not callable(getattr(first_player, attr)):
                logger.info(f"{attr}: {type(getattr(first_player, attr))}")
                
        # If stats exist, examine its structure
        stats = getattr(first_player, 'stats', None)
        if stats:
            logger.info("Stats structure:")
            logger.info(f"Type: {type(stats)}")
            if isinstance(stats, dict):
                for stat_type, stat_values in stats.items():
                    logger.info(f"  {stat_type}: {type(stat_values)}")
                    if isinstance(stat_values, dict):
                        for stat_name, stat_value in list(stat_values.items())[:5]:  # Show first 5 items
                            logger.info(f"    {stat_name}: {type(stat_value)} = {stat_value}")

    # Generate report
    report_path = os.path.join(args.output_dir, 'player_analysis_report.txt')
    with open(report_path, 'w') as f:
        f.write(f"ESPN Fantasy Baseball - Player Analysis Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"League: {client.league.settings.name}\n\n")
        
        # Get available stats from player data
        player_df = analyzer.player_df
        stat_columns = [col for col in player_df.columns if col not in ['player_id', 'name', 'team', 'positions']]
        
        # Print out available stats
        f.write("Available Statistics\n")
        f.write("-------------------\n")
        if stat_columns:
            for stat in sorted(stat_columns):
                f.write(f"- {stat}\n")
        else:
            f.write("No statistics available in player data\n")
        f.write("\n")
        
        # If team ID provided, analyze that team's roster
        if args.team_id:
            target_team = None
            for team in teams:
                if team.team_id == args.team_id:
                    target_team = team
                    break
            
            if target_team:
                f.write(f"Team Roster Analysis: {target_team.team_name}\n")
                f.write(f"{'='*40}\n\n")
                
                analysis = analyzer.analyze_team_roster(target_team)
                
                # Write positions breakdown
                f.write("Positions Breakdown\n")
                f.write("-----------------\n")
                for pos, data in analysis['positions'].items():
                    f.write(f"{pos}: {data['count']} players\n")
                    for player in data['players']:
                        f.write(f"  - {player}\n")
                f.write("\n")
                
                # Write statistics if available
                if 'statistics' in analysis and analysis['statistics']:
                    f.write("Team Statistics\n")
                    f.write("--------------\n")
                    for stat, values in analysis['statistics'].items():
                        f.write(f"{stat}:\n")
                        for key, value in values.items():
                            f.write(f"  {key}: {value}\n")
                    f.write("\n")
            else:
                f.write(f"No team found with ID {args.team_id}\n\n")
        
        # If position filter provided, show players at that position
        if args.position:
            position_players = analyzer.get_players_by_position(args.position)
            
            f.write(f"Players at Position: {args.position}\n")
            f.write(f"{'='*40}\n\n")
            
            if not position_players.empty:
                f.write(f"Total players: {len(position_players)}\n\n")
                
                # If we have stats, show top performers
                f.write("Top Performers\n")
                f.write("-------------\n")
                
                # Filter out columns that contain dictionaries or complex objects
                numeric_stat_cols = []
                for stat in stat_columns:
                    if position_players[stat].dtype in ['int64', 'float64'] or pd.api.types.is_numeric_dtype(position_players[stat]):
                        numeric_stat_cols.append(stat)
                
                if numeric_stat_cols:
                    for stat in numeric_stat_cols:
                        f.write(f"Top 5 by {stat}:\n")
                        try:
                            top_players = position_players.sort_values(stat, ascending=False).head(5)
                            for _, player in top_players.iterrows():
                                f.write(f"  - {player['name']} ({player['team']}): {player[stat]}\n")
                            f.write("\n")
                        except (TypeError, ValueError) as e:
                            f.write(f"  Error sorting by {stat}: {str(e)}\n\n")
                else:
                    f.write("No numeric statistics available for analysis\n\n")
            else:
                f.write(f"No players found at position {args.position}\n\n")
    
    print(f"Player analysis report generated at: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())