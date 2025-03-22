# scripts/fantasy_insights.py
#!/usr/bin/env python
"""
Generate fantasy baseball insights and recommendations.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import numpy as np
import pandas as pd

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.api.client import ESPNFantasyClient
from src.analysis.fantasy_analysis import FantasyAnalyzer

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
    """Main function to generate fantasy insights."""
    parser = argparse.ArgumentParser(description='Generate fantasy baseball insights')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--team-id', type=int, help='Team ID to analyze')
    parser.add_argument('--undervalued', action='store_true', help='Find undervalued players')
    parser.add_argument('--overperforming', action='store_true', help='Find overperforming players')
    parser.add_argument('--position-scarcity', action='store_true', help='Analyze position scarcity')
    parser.add_argument('--trade-targets', action='store_true', help='Suggest trade targets')
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
    
    # Get teams and players
    teams = client.get_teams()
    
    all_rostered_players = []
    for team in teams:
        if hasattr(team, 'roster') and team.roster:
            all_rostered_players.extend(team.roster)
    
    if not all_rostered_players:
        logger.error("No player data available")
        return 1
    
    # Create fantasy analyzer
    analyzer = FantasyAnalyzer(all_rostered_players, teams)
    
    # Generate insights
    report_path = os.path.join(args.output_dir, 'fantasy_insights.txt')
    with open(report_path, 'w') as f:
        f.write(f"ESPN Fantasy Baseball - Insights and Recommendations\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"League: {client.league.settings.name}\n\n")
        
        # Get available stats
        player_df = analyzer.player_df
        available_stats = [col for col in player_df.columns 
                          if col not in ['player_id', 'name', 'team', 'positions'] 
                          and pd.api.types.is_numeric_dtype(player_df[col])]
        
        f.write("Available Statistics\n")
        f.write("-------------------\n")
        for stat in sorted(available_stats):
            f.write(f"- {stat}\n")
        f.write("\n")
        
        # Find performance stats
        actual_stats = [s for s in available_stats if not s.startswith('projected_')]
        projected_stats = [s for s in available_stats if s.startswith('projected_')]
        
        # If both actual and projected stats available, identify interesting players
        if args.undervalued and actual_stats and projected_stats:
            # Use the first stats for demonstration
            actual_stat = actual_stats[0]
            projected_stat = projected_stats[0]
            
            f.write(f"Undervalued Players (comparing {actual_stat} vs {projected_stat})\n")
            f.write(f"{'='*60}\n")
            
            undervalued = analyzer.identify_undervalued_players(actual_stat, projected_stat)
            if not undervalued.empty:
                f.write(undervalued.head(15).to_string(index=False))
            else:
                f.write("No undervalued players identified\n")
            f.write("\n\n")
        
        if args.overperforming and actual_stats and projected_stats:
            # Use the first stats for demonstration
            actual_stat = actual_stats[0]
            projected_stat = projected_stats[0]
            
            f.write(f"Overperforming Players (comparing {actual_stat} vs {projected_stat})\n")
            f.write(f"{'='*60}\n")
            
            overperforming = analyzer.identify_overperforming_players(actual_stat, projected_stat)
            if not overperforming.empty:
                f.write(overperforming.head(15).to_string(index=False))
            else:
                f.write("No overperforming players identified\n")
            f.write("\n\n")
        
        if args.position_scarcity:
            f.write("Position Scarcity Analysis\n")
            f.write(f"{'='*60}\n")
            
            scarcity = analyzer.find_position_scarcity()
            
            f.write("Position Player Counts:\n")
            for pos, count in sorted(scarcity.get('position_counts', {}).items(), key=lambda x: x[1]):
                f.write(f"- {pos}: {count} players\n")
            f.write("\n")
            
            f.write("Position Depth Analysis (performance drop-off from top to mid-tier):\n")
            for pos, metrics in scarcity.get('position_depth', {}).items():
                f.write(f"\n{pos}:\n")
                for stat, values in metrics.items():
                    f.write(f"  {stat}: {values['dropoff']:.2f} drop-off (Top: {values['top_avg']:.1f}, Mid: {values['mid_avg']:.1f})\n")
            f.write("\n\n")
        
        if args.trade_targets and args.team_id:
            f.write("Trade Target Recommendations\n")
            f.write(f"{'='*60}\n")
            
            targets = analyzer.suggest_trade_targets(args.team_id)
            
            if 'team_name' in targets:
                f.write(f"Team: {targets['team_name']}\n\n")
                
                if targets.get('weak_positions'):
                    f.write("Positions to strengthen: " + ", ".join(targets['weak_positions']) + "\n\n")
                    
                    for pos, players in targets.get('trade_targets', {}).items():
                        f.write(f"Recommended {pos} targets:\n")
                        for player in players:
                            stat_val = list(player.items())[3][1]  # Get the stat value
                            f.write(f"- {player['name']} ({player['team']}): {stat_val}\n")
                        f.write("\n")
                else:
                    f.write("No clear position weaknesses identified\n")
            else:
                f.write(f"Could not analyze team with ID {args.team_id}\n")
    
    print(f"Fantasy insights report generated at: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())