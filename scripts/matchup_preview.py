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
    """Format pitching strategy into readable text with schedule information."""
    sections = []
    
    sections.append("PITCHING STRATEGY")
    sections.append("=" * 30)
    
    max_starts = pitching_strategy.get('max_starts', 12)
    sections.append(f"Maximum pitcher starts: {max_starts}")
    
    # Add adjusted point total if available
    projected = pitching_strategy.get('projected_points', 0)
    adjusted = pitching_strategy.get('adjusted_points', 0)
    
    if adjusted > 0 and projected > 0:
        adjustment = adjusted - projected
        adjustment_text = "+" if adjustment > 0 else ""
        sections.append(f"Projected pitching points: {projected:.1f} ({adjustment_text}{adjustment:.1f} matchup adjustment) = {adjusted:.1f} total")
    elif projected > 0:
        sections.append(f"Projected pitching points: {projected:.1f}")
    
    # Get pitcher notes and schedule information
    pitcher_notes = pitching_strategy.get('pitcher_notes', {})
    pitcher_schedule = pitching_strategy.get('pitcher_schedule', {})
    
    # Strategy explanation
    sections.append("\nSTRATEGY EXPLANATION:")
    sections.append("Pitcher rankings are based on a combination of:")
    sections.append("• Baseline projections")
    sections.append("• Opponent offensive strength (including K%)")
    sections.append("• Ballpark factors")
    sections.append("• Home/away status")
    sections.append("• Pitcher's recent performance trends")
    
    # Format recommended starters
    recommended = pitching_strategy.get('recommended_pitchers', [])
    if recommended:
        sections.append("\nRECOMMENDED STARTERS:")
        for i, pitcher in enumerate(recommended, 1):
            pitcher_line = f"{i}. {pitcher}"
            
            # Add note if available
            if pitcher in pitcher_notes:
                pitcher_line += f" - {pitcher_notes[pitcher]}"
                
            # Add scheduled start date if available
            if pitcher_schedule and pitcher in pitcher_schedule:
                start_info = pitcher_schedule[pitcher]
                if 'date' in start_info:
                    start_date = start_info['date']
                    pitcher_line += f" (Scheduled: {start_date.strftime('%a, %b %d')})"
                    
                # Add opponent and ballpark info if available
                if 'opponent' in start_info and 'ballpark' in start_info:
                    opponent = start_info['opponent']
                    ballpark = start_info['ballpark']
                    home_away = "home" if start_info.get('home_game', False) else "away"
                    pitcher_line += f" - {home_away} vs {opponent} at {ballpark}"
                
            sections.append(pitcher_line)
    
    # Format benched pitchers
    benched = pitching_strategy.get('benched_pitchers', [])
    if benched:
        sections.append("\nCONSIDER BENCHING:")
        for pitcher in benched:
            pitcher_line = f"- {pitcher}"
            
            # Add note if available
            if pitcher in pitcher_notes:
                pitcher_line += f" - {pitcher_notes[pitcher]}"
                
            # Add scheduled start date if available
            if pitcher_schedule and pitcher in pitcher_schedule:
                start_info = pitcher_schedule[pitcher]
                if 'date' in start_info:
                    start_date = start_info['date']
                    pitcher_line += f" (Scheduled: {start_date.strftime('%a, %b %d')})"
            
            sections.append(pitcher_line)
            
    # Weekly distribution analysis
    sections.append("\nWEEKLY DISTRIBUTION:")
    start_distribution = pitching_strategy.get('start_distribution', {})
    
    if start_distribution:
        # Sort dates chronologically
        sorted_dates = sorted(start_distribution.keys())
        
        # Show the distribution of starts for each day
        sections.append("Scheduled starts by day:")
        
        for date_str in sorted_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            day_name = date_obj.strftime('%a %m/%d')
            pitchers = start_distribution[date_str]
            
            if len(pitchers) == 1:
                sections.append(f"• {day_name}: {pitchers[0]}")
            else:
                sections.append(f"• {day_name}: {', '.join(pitchers)} ({len(pitchers)} pitchers)")
    else:
        sections.append("For optimal performance, aim to distribute your starts evenly throughout the week,")
        sections.append("focusing on favorable matchups while ensuring you reach your maximum starts.")
    
    # Add insights or general strategy notes
    strategy_note = pitching_strategy.get('note', '')
    if strategy_note:
        sections.append(f"\nNOTE: {strategy_note}")
    
    # Add a strategy tip based on the matchup
    sections.append("\nSTRATEGY TIP: Prioritize your starts against weaker offensive teams and in pitcher-friendly parks. Consider the opponent's strikeout tendencies for pitchers who rely on Ks for fantasy value.")
        
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
        logger.warning(f"No current matchup found for team {my_team.team_name}")
        
        # If no active matchup is found, look for the next scheduled matchup
        logger.info("Looking for next scheduled matchup...")
        if hasattr(my_team, 'schedule') and my_team.schedule:
            for scheduled_matchup in my_team.schedule:
                # Check if this matchup has the team we want
                team1 = getattr(scheduled_matchup, 'team_1', None) 
                team2 = getattr(scheduled_matchup, 'team_2', None)
                
                # If team attributes aren't found, try home_team and away_team
                if not team1 or not team2:
                    team1 = getattr(scheduled_matchup, 'home_team', None)
                    team2 = getattr(scheduled_matchup, 'away_team', None)
                
                # Create a simple matchup object with the first available opponent
                if team1 and team2:
                    logger.info(f"Found upcoming matchup: {team1.team_name} vs {team2.team_name}")
                    
                    # Create a simplified matchup
                    from src.data.adapters import SimpleMatchup
                    if str(team1.team_id) == str(team_id):
                        my_matchup = SimpleMatchup(team1, team2)
                    else:
                        my_matchup = SimpleMatchup(team2, team1)
                    break
        
        if not my_matchup:
            logger.error(f"No current or upcoming matchups found for team {my_team.team_name}")
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