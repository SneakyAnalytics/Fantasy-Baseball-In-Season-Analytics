#!/usr/bin/env python
"""
Analyze player trends and identify breakout candidates using Statcast data.
"""

import os
import sys
import logging
import argparse
import json
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.api.client import ESPNFantasyClient
from src.analysis.player_analysis import PlayerAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO if hasattr(settings, 'DEBUG') and settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('espn_fantasy.log')
    ]
)

logger = logging.getLogger(__name__)

def format_trending_batters(trending_batters):
    """Format trending batters into readable text."""
    sections = []
    
    sections.append("TRENDING BATTERS")
    sections.append("=" * 50)
    
    if not trending_batters:
        sections.append("No trending batters identified.")
        return "\n".join(sections)
    
    # Group by availability
    available = [p for p in trending_batters if p.get('available', False)]
    rostered = [p for p in trending_batters if not p.get('available', False) and p.get('in_league', False)]
    external = [p for p in trending_batters if not p.get('in_league', False)]
    
    # Format available players (most important)
    if available:
        sections.append("\nAVAILABLE WAIVER PICKUPS:")
        for i, player in enumerate(available[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Breakout Score: {player['breakout_score']:.2f}")
            sections.append(f"   Reason: {player['reason']}")
            
            # Add key metrics
            metrics = player.get('metrics', {})
            if metrics:
                metric_lines = []
                if 'ba' in metrics and 'xba' in metrics:
                    metric_lines.append(f"BA: .{int(metrics['ba']*1000):03d} | xBA: .{int(metrics['xba']*1000):03d}")
                if 'slg' in metrics and 'xslg' in metrics:
                    metric_lines.append(f"SLG: .{int(metrics['slg']*1000):03d} | xSLG: .{int(metrics['xslg']*1000):03d}")
                if 'barrel_rate' in metrics:
                    metric_lines.append(f"Barrel %: {metrics['barrel_rate']:.1f}")
                if metric_lines:
                    sections.append(f"   Metrics: {' | '.join(metric_lines)}")
            sections.append("")
    
    # Format rostered players
    if rostered:
        sections.append("\nROSTERED TRENDING PLAYERS:")
        for i, player in enumerate(rostered[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Breakout Score: {player['breakout_score']:.2f}")
            sections.append(f"   Reason: {player['reason']}")
            sections.append("")
    
    # Format external players
    if external and len(external) > 0:
        sections.append("\nOTHER TRENDING PLAYERS (WATCH LIST):")
        for i, player in enumerate(external[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Breakout Score: {player['breakout_score']:.2f}")
            sections.append(f"   Reason: {player['reason']}")
            sections.append("")
    
    return "\n".join(sections)

def format_trending_pitchers(trending_pitchers):
    """Format trending pitchers into readable text."""
    sections = []
    
    sections.append("TRENDING PITCHERS")
    sections.append("=" * 50)
    
    if not trending_pitchers:
        sections.append("No trending pitchers identified.")
        return "\n".join(sections)
    
    # Group by availability
    available = [p for p in trending_pitchers if p.get('available', False)]
    rostered = [p for p in trending_pitchers if not p.get('available', False) and p.get('in_league', False)]
    external = [p for p in trending_pitchers if not p.get('in_league', False)]
    
    # Format available players (most important)
    if available:
        sections.append("\nAVAILABLE WAIVER PICKUPS:")
        for i, player in enumerate(available[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Breakout Score: {player['breakout_score']:.2f}")
            sections.append(f"   Reason: {player['reason']}")
            
            # Add key metrics
            metrics = player.get('metrics', {})
            if metrics:
                metric_lines = []
                if 'era' in metrics and 'xera' in metrics:
                    metric_lines.append(f"ERA: {metrics['era']:.2f} | xERA: {metrics['xera']:.2f}")
                if 'woba' in metrics and 'xwoba' in metrics:
                    metric_lines.append(f"wOBA: .{int(metrics['woba']*1000):03d} | xwOBA: .{int(metrics['xwoba']*1000):03d}")
                if 'k_rate' in metrics:
                    metric_lines.append(f"K%: {metrics['k_rate']:.1f}")
                if metric_lines:
                    sections.append(f"   Metrics: {' | '.join(metric_lines)}")
            sections.append("")
    
    # Format rostered players
    if rostered:
        sections.append("\nROSTERED TRENDING PLAYERS:")
        for i, player in enumerate(rostered[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Breakout Score: {player['breakout_score']:.2f}")
            sections.append(f"   Reason: {player['reason']}")
            sections.append("")
    
    # Format external players
    if external and len(external) > 0:
        sections.append("\nOTHER TRENDING PLAYERS (WATCH LIST):")
        for i, player in enumerate(external[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Breakout Score: {player['breakout_score']:.2f}")
            sections.append(f"   Reason: {player['reason']}")
            sections.append("")
    
    return "\n".join(sections)

def format_trending_down(trending_down_players):
    """Format players trending down into readable text."""
    sections = []
    
    sections.append("PLAYERS TRENDING DOWN")
    sections.append("=" * 50)
    
    if not trending_down_players:
        sections.append("No players with significant negative trends identified.")
        return "\n".join(sections)
    
    # Only show rostered players trending down
    rostered = [p for p in trending_down_players if not p.get('available', False) and p.get('in_league', False)]
    if not rostered:
        sections.append("No rostered players with significant negative trends identified.")
        return "\n".join(sections)
    
    # Separate by player type
    batters = [p for p in rostered if p.get('position') == 'batter']
    pitchers = [p for p in rostered if p.get('position') == 'pitcher']
    
    # Format batters
    if batters:
        sections.append("\nBATTERS TRENDING DOWN:")
        for i, player in enumerate(batters[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Concern Level: {(1.0 - player['breakout_score']):.2f}")
            
            # Add key metrics
            metrics = player.get('metrics', {})
            if metrics:
                metric_lines = []
                if 'ba' in metrics and 'xba' in metrics:
                    metric_lines.append(f"BA: .{int(metrics['ba']*1000):03d} | xBA: .{int(metrics['xba']*1000):03d}")
                if 'slg' in metrics and 'xslg' in metrics:
                    metric_lines.append(f"SLG: .{int(metrics['slg']*1000):03d} | xSLG: .{int(metrics['xslg']*1000):03d}")
                if metric_lines:
                    sections.append(f"   Metrics: {' | '.join(metric_lines)}")
            sections.append("")
    
    # Format pitchers
    if pitchers:
        sections.append("\nPITCHERS TRENDING DOWN:")
        for i, player in enumerate(pitchers[:5], 1):
            sections.append(f"{i}. {player['name']} ({player['team']})")
            sections.append(f"   Concern Level: {(1.0 - player['breakout_score']):.2f}")
            
            # Add key metrics
            metrics = player.get('metrics', {})
            if metrics:
                metric_lines = []
                if 'era' in metrics and 'xera' in metrics:
                    metric_lines.append(f"ERA: {metrics['era']:.2f} | xERA: {metrics['xera']:.2f}")
                if 'woba' in metrics and 'xwoba' in metrics:
                    metric_lines.append(f"wOBA: .{int(metrics['woba']*1000):03d} | xwOBA: .{int(metrics['xwoba']*1000):03d}")
                if metric_lines:
                    sections.append(f"   Metrics: {' | '.join(metric_lines)}")
            sections.append("")
    
    sections.append("\nSTRATEGY TIP: Consider benching/dropping these players if better options are available.")
    
    return "\n".join(sections)

def main():
    """Main function to generate player trends report."""
    parser = argparse.ArgumentParser(description='Analyze player trends using Statcast data')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--min-sample', type=int, default=25, help='Minimum sample size for analysis')
    parser.add_argument('--player-type', choices=['batter', 'pitcher', 'both'], default='both', 
                       help='Type of players to analyze')
    parser.add_argument('--player', help='Analyze a specific player in depth')
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
    
    # Get players
    all_players = []
    
    # Get all teams
    teams = client.get_teams()
    for team in teams:
        if hasattr(team, 'roster') and team.roster:
            for player in team.roster:
                player.rostered = True
            all_players.extend(team.roster)
    
    # Get free agents
    free_agents = client.get_free_agents(size=300)
    for player in free_agents:
        player.rostered = False
    all_players.extend(free_agents)
    
    # Create analyzer
    analyzer = PlayerAnalyzer(all_players)
    
    # If analyzing a specific player
    if args.player:
        player_data = analyzer.get_player_statcast_metrics(args.player)
        if 'error' in player_data:
            logger.error(player_data['error'])
            return 1
        
        # Save detailed player report
        player_filename = args.player.replace(' ', '_').lower() + '_statcast_report.json'
        player_path = os.path.join(args.output_dir, player_filename)
        
        with open(player_path, 'w') as f:
            json.dump(player_data, f, indent=2)
        
        print(f"Detailed player report generated at: {player_path}")
        return 0
    
    # Get trending players
    trending_players = analyzer.find_trending_players(
        min_sample_size=args.min_sample,
        player_type=args.player_type
    )
    
    trending_up = trending_players.get('trending_up', [])
    trending_down = trending_players.get('trending_down', [])
    
    # Split trending players by type
    trending_batters = [p for p in trending_up if p.get('position') == 'batter']
    trending_pitchers = [p for p in trending_up if p.get('position') == 'pitcher']
    
    # Generate report sections
    sections = []
    
    # Header
    header = [
        "=" * 70,
        "PLAYER TRENDS ANALYSIS REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        ""
    ]
    sections.append("\n".join(header))
    
    # Add report sections
    if args.player_type in ['batter', 'both']:
        sections.append(format_trending_batters(trending_batters))
    
    if args.player_type in ['pitcher', 'both']:
        sections.append(format_trending_pitchers(trending_pitchers))
    
    sections.append(format_trending_down(trending_down))
    
    # Final report
    report = "\n\n".join(sections)
    
    # Save report
    today = datetime.now().strftime('%Y-%m-%d')
    report_path = os.path.join(args.output_dir, f'player_trends_{today}.txt')
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Player trends report generated at: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())