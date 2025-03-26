#!/usr/bin/env python
#!/usr/bin/env python
"""
Generate a weekly matchup preview report.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import json

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

def format_position_analysis(position_analysis):
    """Format position analysis into readable text."""
    sections = []
    
    sections.append("POSITION-BY-POSITION BREAKDOWN")
    sections.append("=" * 30)
    
    total_team_proj = 0
    total_opp_proj = 0
    
    for position, analysis in position_analysis.items():
        team_proj = analysis.get('team_projection', 0)
        opp_proj = analysis.get('opponent_projection', 0)
        advantage = analysis.get('advantage', 'even')
        diff = analysis.get('difference', 0)
        
        total_team_proj += team_proj
        total_opp_proj += opp_proj
        
        # Format the position section
        pos_section = [
            f"{position}:",
            f"  Your projection: {team_proj:.1f} pts",
            f"  Opponent projection: {opp_proj:.1f} pts"
        ]
        
        if advantage == "team":
            pos_section.append(f"  ADVANTAGE: YOU (+{diff:.1f} pts)")
        elif advantage == "opponent":
            pos_section.append(f"  ADVANTAGE: OPPONENT (+{diff:.1f} pts)")
        else:
            pos_section.append("  ADVANTAGE: EVEN")
            
        # Add player details
        team_players = analysis.get('team_players', [])
        opp_players = analysis.get('opponent_players', [])
        
        if team_players:
            pos_section.append("  Your players:")
            for player in team_players:
                pos_section.append(f"    - {player}")
                
        if opp_players:
            pos_section.append("  Opponent players:")
            for player in opp_players:
                pos_section.append(f"    - {player}")
                
        sections.append("\n".join(pos_section))
    
    # Add overall projection
    overall = [
        "\nOVERALL PROJECTION",
        "=" * 30,
        f"Your team: {total_team_proj:.1f} projected points",
        f"Opponent: {total_opp_proj:.1f} projected points",
        f"Projected margin: {(total_team_proj - total_opp_proj):.1f} points"
    ]
    
    if total_team_proj > total_opp_proj:
        overall.append("PROJECTION: WIN")
    elif total_opp_proj > total_team_proj:
        overall.append("PROJECTION: LOSS")
    else:
        overall.append("PROJECTION: EVEN MATCHUP")
        
    sections.append("\n".join(overall))
    
    return "\n\n".join(sections)

def format_pitching_strategy(pitching_strategy):
    """Format pitching strategy into readable text."""
    sections = []
    
    sections.append("PITCHING STRATEGY")
    sections.append("=" * 30)
    
    max_starts = pitching_strategy.get('max_starts', 12)
    sections.append(f"Maximum pitcher starts: {max_starts}")
    
    recommended = pitching_strategy.get('recommended_pitchers', [])
    if recommended:
        sections.append("\nRECOMMENDED STARTERS:")
        for i, pitcher in enumerate(recommended, 1):
            sections.append(f"{i}. {pitcher}")
    
    benched = pitching_strategy.get('benched_pitchers', [])
    if benched:
        sections.append("\nCONSIDER BENCHING:")
        for pitcher in benched:
            sections.append(f"- {pitcher}")
            
    projected = pitching_strategy.get('projected_points', 0)
    if projected > 0:
        sections.append(f"\nProjected pitching points: {projected:.1f}")
        
    return "\n".join(sections)

def format_acquisition_recommendations(recommendations):
    """Format acquisition recommendations into readable text."""
    if not recommendations:
        return "No acquisition recommendations available."
        
    sections = []
    
    sections.append("RECOMMENDED ACQUISITIONS")
    sections.append("=" * 30)
    sections.append("Based on your team needs and available free agents:")
    
    for position, players in recommendations.items():
        if position == "streaming_sp":
            sections.append("\nRECOMMENDED STREAMING PITCHERS:")
        else:
            sections.append(f"\nRECOMMENDED {position} PICKUPS:")
            
        if players:
            for i, player in enumerate(players, 1):
                name = player.get('name', 'Unknown')
                team = player.get('team', '')
                
                # Get the projection value (key might vary)
                proj_val = 0
                for key, value in player.items():
                    if 'projected' in key.lower() and isinstance(value, (int, float)):
                        proj_val = value
                        break
                
                sections.append(f"{i}. {name} ({team}) - {proj_val:.1f} projected pts")
    
    sections.append("\nRemember: You have a maximum of 8 acquisitions per matchup.")
    
    return "\n".join(sections)

def generate_report(team_name, opponent_name, position_analysis, pitching_strategy, recommendations):
    """Generate the full report text."""
    sections = []
    
    # Header
    header = [
        "=" * 50,
        f"WEEKLY MATCHUP PREVIEW: {team_name} vs {opponent_name}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        ""
    ]
    sections.append("\n".join(header))
    
    # Position analysis
    sections.append(format_position_analysis(position_analysis))
    
    # Pitching strategy
    sections.append("\n\n" + format_pitching_strategy(pitching_strategy))
    
    # Acquisition recommendations
    sections.append("\n\n" + format_acquisition_recommendations(recommendations))
    
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
    """Main function to generate weekly matchup preview."""
    parser = argparse.ArgumentParser(description='Generate a weekly matchup preview report')
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
    
    # Get all players and free agents
    all_rostered_players = []
    for team in client.get_teams():
        if hasattr(team, 'roster') and team.roster:
            all_rostered_players.extend(team.roster)
    
    free_agents = client.get_free_agents(size=300)  # Get a large batch of free agents
    
    # Create analyzers
    matchup_analyzer = MatchupAnalyzer(
        matchup=my_matchup,
        team=my_team,
        opponent=opponent,
        all_players=all_rostered_players,
        free_agents=free_agents
    )
    
    # Generate analysis components
    position_analysis = matchup_analyzer.analyze_position_matchups()
    pitching_strategy = matchup_analyzer.optimize_pitcher_starts(max_starts=12)  # League setting
    recommendations = matchup_analyzer.recommend_acquisitions(limit=8)  # League setting
    
    # Generate report
    report = generate_report(
        my_team.team_name,
        opponent.team_name,
        position_analysis,
        pitching_strategy,
        recommendations
    )
    
    # Create reports directory if it doesn't exist
    reports_dir = getattr(settings, 'REPORT_DIR', os.path.join(args.output_dir, 'reports'))
    os.makedirs(reports_dir, exist_ok=True)
    
    # Save report
    today = datetime.now().strftime('%Y-%m-%d')
    report_filename = f'matchup_preview_{today}.txt'
    report_path = os.path.join(reports_dir, report_filename)
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Matchup preview report generated at: {report_path}")
    
    # Handle email delivery if enabled
    if hasattr(settings, 'EMAIL_ENABLED') and settings.EMAIL_ENABLED:
        try:
            from src.visualization.delivery import ReportDelivery
            
            subject = f"{settings.EMAIL_SUBJECT_PREFIX}Weekly Matchup Preview: {my_team.team_name} vs {opponent.team_name}"
            recipients = getattr(settings, 'EMAIL_TO', [])
            
            if recipients:
                success = ReportDelivery.deliver_email(
                    subject=subject,
                    body=report,
                    recipients=recipients,
                    attachments=[report_path]
                )
                
                if success:
                    print(f"Report sent via email to: {', '.join(recipients)}")
                else:
                    print("Failed to send email report")
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
    
    # Log to report history
    try:
        from src.visualization.delivery import ReportDelivery
        
        summary = f"Matchup Preview: {my_team.team_name} vs {opponent.team_name}"
        ReportDelivery.log_to_history('weekly', summary, report_path)
    except Exception as e:
        logger.error(f"Error logging to history: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())