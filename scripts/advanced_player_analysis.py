# scripts/advanced_player_analysis.py
#!/usr/bin/env python
"""
Generate an advanced player analysis report with visualizations.
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
from src.visualization.player_charts import PlayerVisualizer

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
    """Main function to generate advanced player analysis report."""
    parser = argparse.ArgumentParser(description='Generate an advanced player analysis report')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--stat', help='Statistic to analyze')
    parser.add_argument('--top', type=int, default=10, help='Number of top players to include')
    parser.add_argument('--position', help='Filter by position')
    parser.add_argument('--compare', nargs=2, metavar=('PLAYER1', 'PLAYER2'), 
                       help='Compare two players by name')
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
    
    if not all_rostered_players:
        logger.error("No player data available")
        return 1
    
    # Create player analyzer and visualizer
    analyzer = PlayerAnalyzer(all_rostered_players)
    visualizer = PlayerVisualizer(output_dir=args.output_dir)
    
    # Get available stats
    player_df = analyzer.player_df
    available_stats = [col for col in player_df.columns 
                       if col not in ['player_id', 'name', 'team', 'positions']]
    
    # If no stat specified, display available stats and exit
    if not args.stat and not args.compare:
        print("Available statistics:")
        for stat in sorted(available_stats):
            print(f"- {stat}")
        return 0
    
    # Filter by position if specified
    filtered_players = all_rostered_players
    if args.position:
        position_df = analyzer.get_players_by_position(args.position)
        if position_df.empty:
            logger.error(f"No players found at position {args.position}")
            return 1
        
        # Convert back to Player objects (simplified for this example)
        # In a real implementation, you'd want to create a function to convert DataFrame rows back to Player objects
        filtered_players = [p for p in all_rostered_players 
                           if p.name in position_df['name'].values]
    
    # Process based on arguments
    if args.compare:
        player1_name, player2_name = args.compare
        
        # Find the players
        player1 = None
        player2 = None
        for player in all_rostered_players:
            if player1_name.lower() in player.name.lower():
                player1 = player
            if player2_name.lower() in player.name.lower():
                player2 = player
        
        if not player1 or not player2:
            logger.error("One or both players not found")
            return 1
        
        print(f"Comparing {player1.name} and {player2.name}")
        
        # Generate comparison visualization
        try:
            output_path = visualizer.visualize_player_comparison(
                player1, player2, available_stats[:10]  # Use first 10 stats for comparison
            )
            print(f"Comparison chart generated: {output_path}")
        except Exception as e:
            logger.error(f"Error generating comparison: {str(e)}")
    
    elif args.stat:
        if args.stat not in available_stats:
            logger.error(f"Statistic '{args.stat}' not available. Choose from: {', '.join(available_stats)}")
            return 1
        
        print(f"Analyzing top {args.top} players by {args.stat}")
        
        # Generate top players visualization
        try:
            output_path = visualizer.visualize_top_players(
                filtered_players, args.stat, limit=args.top
            )
            print(f"Top players chart generated: {output_path}")
        except Exception as e:
            logger.error(f"Error generating top players chart: {str(e)}")
        
        # If position specified, also generate position comparison
        if not args.position:
            try:
                output_path = visualizer.visualize_position_comparison(
                    all_rostered_players, args.stat
                )
                print(f"Position comparison chart generated: {output_path}")
            except Exception as e:
                logger.error(f"Error generating position comparison: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())