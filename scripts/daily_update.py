#!/usr/bin/env python
"""
Generate a daily fantasy baseball update report.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.api.client import ESPNFantasyClient
from src.analysis.matchup_analysis import MatchupAnalyzer
from src.analysis.player_analysis import PlayerAnalyzer
# Import the adapter class for early season
from src.data.adapters import SimpleMatchup

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

def format_daily_performance(team_players, opponent_players):
    """Format daily performance summary."""
    sections = []
    
    # Check if we have performance data
    has_performance_data = False
    for player in team_players:
        if hasattr(player, 'stats') and player.stats and '0_points' in player.stats:
            has_performance_data = True
            break
    
    if not has_performance_data:
        return "No performance data available for yesterday."
    
    sections.append("YESTERDAY'S PERFORMANCE")
    sections.append("=" * 30)
    
    # Team performance
    team_points = 0
    team_performance = []
    
    for player in team_players:
        if hasattr(player, 'stats') and player.stats and '0_points' in player.stats:
            points = player.stats.get('0_points', 0)
            team_points += points
            team_performance.append((player.name, points))
    
    # Sort by points (highest first)
    team_performance.sort(key=lambda x: x[1], reverse=True)
    
    sections.append(f"YOUR TEAM: {team_points:.1f} POINTS")
    
    for player, points in team_performance:
        if points > 0:
            sections.append(f"  {player}: +{points:.1f} pts")
        else:
            sections.append(f"  {player}: {points:.1f} pts")
    
    # Opponent performance
    opponent_points = 0
    opponent_performance = []
    
    for player in opponent_players:
        if hasattr(player, 'stats') and player.stats and '0_points' in player.stats:
            points = player.stats.get('0_points', 0)
            opponent_points += points
            opponent_performance.append((player.name, points))
    
    # Sort by points (highest first)
    opponent_performance.sort(key=lambda x: x[1], reverse=True)
    
    sections.append(f"\nOPPONENT: {opponent_points:.1f} POINTS")
    
    for player, points in opponent_performance:
        if points > 0:
            sections.append(f"  {player}: +{points:.1f} pts")
        else:
            sections.append(f"  {player}: {points:.1f} pts")
    
    # Daily summary
    daily_diff = team_points - opponent_points
    
    sections.append("\nDAILY SUMMARY:")
    if daily_diff > 0:
        sections.append(f"You WON the day by {daily_diff:.1f} points")
    elif daily_diff < 0:
        sections.append(f"You LOST the day by {abs(daily_diff):.1f} points")
    else:
        sections.append("The day ended in a TIE")
    
    return "\n".join(sections)

def format_matchup_status(matchup, team_id):
    """Format current matchup status."""
    sections = []
    
    sections.append("CURRENT MATCHUP STATUS")
    sections.append("=" * 30)
    
    # Determine which team is yours
    if matchup.team_1.team_id == team_id:
        your_team = matchup.team_1
        your_score = matchup.team_1_score
        opponent = matchup.team_2
        opponent_score = matchup.team_2_score
    else:
        your_team = matchup.team_2
        your_score = matchup.team_2_score
        opponent = matchup.team_1
        opponent_score = matchup.team_1_score
    
    sections.append(f"{your_team.name} vs {opponent.name}")
    sections.append(f"Week {matchup.week} Matchup")
    sections.append("")
    sections.append(f"YOUR SCORE:     {your_score:.1f}")
    sections.append(f"OPPONENT SCORE: {opponent_score:.1f}")
    
    # Calculate score difference
    score_diff = your_score - opponent_score
    
    if score_diff > 0:
        sections.append(f"\nYou are WINNING by {score_diff:.1f} points")
    elif score_diff < 0:
        sections.append(f"\nYou are LOSING by {abs(score_diff):.1f} points")
    else:
        sections.append("\nThe matchup is TIED")
    
    return "\n".join(sections)

def format_upcoming_streams(free_agents, start_date):
    """Format upcoming streaming pitcher recommendations."""
    if not free_agents:
        return "No streaming pitcher recommendations available."
    
    sections = []
    
    sections.append("STREAMING PITCHER RECOMMENDATIONS")
    sections.append("=" * 30)
    sections.append(f"For games starting {start_date.strftime('%A, %B %d')}:")
    
    # In a real implementation, you would:
    # 1. Filter pitchers by probable start date
    # 2. Evaluate matchups and ballparks
    # 3. Consider recent performance
    
    # For now, just show top free agent pitchers
    sp_free_agents = [p for p in free_agents if 'SP' in getattr(p, 'eligibleSlots', [])]
    
    if not sp_free_agents:
        sections.append("\nNo starting pitchers available on waivers.")
        return "\n".join(sections)
    
    # Sort by projected points if available
    sp_free_agents.sort(key=lambda p: getattr(p, 'stats', {}).get('0_projected_points', 0), reverse=True)
    
    # Show top 5 options
    for i, pitcher in enumerate(sp_free_agents[:5], 1):
        proj_points = getattr(pitcher, 'stats', {}).get('0_projected_points', 0)
        sections.append(f"{i}. {pitcher.name} ({pitcher.proTeam}) - {proj_points:.1f} projected pts")
    
    # Reminder about acquisition limit
    sections.append(f"\nRemember: You have a maximum of {settings.MAX_ACQUISITIONS_PER_MATCHUP} " +
                   "acquisitions per matchup.")
    
    return "\n".join(sections)

def format_hot_pickups(free_agents):
    """Format hot waiver wire pickups."""
    if not free_agents:
        return "No waiver wire recommendations available."
    
    sections = []
    
    sections.append("HOT WAIVER WIRE PICKUPS")
    sections.append("=" * 30)
    
    # In a real implementation, you would:
    # 1. Look at recent performance trends
    # 2. Consider ownership % changes
    # 3. Factor in upcoming schedules
    
    # For now, just group by position and show projected points
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'SP', 'RP']
    
    for pos in positions:
        pos_players = [p for p in free_agents if pos in str(getattr(p, 'eligibleSlots', []))]
        
        if not pos_players:
            continue
        
        # Sort by projected points
        pos_players.sort(key=lambda p: getattr(p, 'stats', {}).get('0_projected_points', 0), reverse=True)
        
        # Show top 2 options for each position
        sections.append(f"\nTop {pos} Available:")
        for i, player in enumerate(pos_players[:2], 1):
            proj_points = getattr(player, 'stats', {}).get('0_projected_points', 0)
            sections.append(f"{i}. {player.name} ({player.proTeam}) - {proj_points:.1f} projected pts")
    
    return "\n".join(sections)

def generate_report(team_name, team_roster, opponent_roster, matchup, free_agents):
    """Generate the full daily report text."""
    sections = []
    
    # Header
    header = [
        "=" * 50,
        f"DAILY FANTASY BASEBALL UPDATE: {team_name}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        ""
    ]
    sections.append("\n".join(header))
    
    # Performance summary
    sections.append(format_daily_performance(team_roster, opponent_roster))
    
    # Current matchup status
    sections.append("\n\n" + format_matchup_status(matchup, team_id))
    
    # Tomorrow's streaming recommendations
    tomorrow = datetime.now() + timedelta(days=1)
    sections.append("\n\n" + format_upcoming_streams(free_agents, tomorrow))
    
    # Hot waiver wire pickups
    sections.append("\n\n" + format_hot_pickups(free_agents))
    
    # Footer
    footer = [
        "",
        "=" * 50,
        "Generated by Fantasy Baseball Analyzer",
        "=" * 50
    ]
    sections.append("\n".join(footer))
    
    return "\n".join(sections)

def main():
    """Main function to generate daily update report."""
    parser = argparse.ArgumentParser(description='Generate a daily fantasy baseball update report')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--team-id', type=int, help='Team ID (defaults to configured team)')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Get configured team ID or use argument
    team_id = args.team_id if args.team_id else getattr(settings, 'MY_TEAM_ID', None)
    if not team_id:
        logger.error("No team ID specified. Use --team-id or set MY_TEAM_ID in settings.")
        return 1
    
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
    
    # Get matchup data
    matchups = client.get_matchups()
    
    # Identify my team and its matchup - try by ID first, then by name
    my_team = client.get_team_by_id(team_id)
    
    # If that fails, try to find by name (for "Mr. Met's Monastery")
    if not my_team and team_id == 4:
        logger.info(f"Team with ID {team_id} not found directly, trying to find by name")
        my_team = client.get_team_by_name("Mr. Met's Monastery")
    
    # If still not found, let the user select their team
    if not my_team:
        logger.warning(f"Team with ID {team_id} not found. Please select your team:")
        teams = client.get_teams()
        for i, team in enumerate(teams, 1):
            team_name = getattr(team, 'team_name', 'Unknown Team')
            logger.warning(f"{i}. {team_name}")
        
        # In interactive mode, we'd ask for input here
        # For now, use Mr. Met's Monastery as a fallback
        for team in teams:
            team_name = getattr(team, 'team_name', '')
            if "Mr. Met's Monastery" in team_name:
                my_team = team
                logger.info(f"Using '{team_name}' as your team")
                break
    
    if not my_team:
        logger.error(f"Could not identify your team")
        return 1
    
    # Find my matchup
    my_matchup = None
    for matchup in matchups:
        if (hasattr(matchup, 'home_team') and matchup.home_team.team_id == team_id) or \
           (hasattr(matchup, 'away_team') and matchup.away_team.team_id == team_id):
            my_matchup = matchup
            break
    
    if not my_matchup:
        logger.error(f"No current matchup found for team {my_team.team_name}")
        return 1
    
    # Identify my opponent
    opponent = my_matchup.away_team if my_matchup.home_team.team_id == team_id else my_matchup.home_team
    
    # Get free agents
    free_agents = client.get_free_agents(size=300)  # Get a large batch of free agents
    
    # Generate report
    report = generate_report(
        my_team.team_name,
        my_team.roster,
        opponent.roster,
        my_matchup,
        free_agents
    )
    
    # Save report
    today = datetime.now().strftime('%Y-%m-%d')
    report_path = os.path.join(args.output_dir, f'daily_update_{today}.txt')
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Daily update report generated at: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())