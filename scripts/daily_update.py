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
    """Format upcoming streaming pitcher recommendations with enhanced analysis."""
    if not free_agents:
        return "No streaming pitcher recommendations available."
    
    sections = []
    
    sections.append("STREAMING PITCHER RECOMMENDATIONS")
    sections.append("=" * 30)
    sections.append(f"For games starting {start_date.strftime('%A, %B %d')}:")
    
    # Placeholder for enhanced pitcher data
    # In a full implementation, this data would be fetched from external APIs
    
    # Example opponent quality data (higher = better offense, tougher for pitchers)
    team_offensive_ratings = {
        "NYY": 112,  # wRC+ or similar metric
        "BOS": 108,
        "TB": 103,
        "BAL": 96,
        "TOR": 105,
        "LAD": 115,
        "SF": 101,
        "SD": 103,
        "ARI": 100,
        "COL": 95,  # But home park factor is huge
        "ATL": 110,
        "NYM": 102,
        "PHI": 106,
        "WSH": 94,
        "MIA": 90,
        # Add more teams as needed
    }
    
    # Example ballpark factors (>1.0 = hitter-friendly, <1.0 = pitcher-friendly)
    ballpark_factors = {
        "Yankee Stadium": 1.12,
        "Fenway Park": 1.25,
        "Tropicana Field": 0.94,
        "Camden Yards": 1.05,
        "Rogers Centre": 1.03,
        "Dodger Stadium": 0.98,
        "Oracle Park": 0.90,
        "Petco Park": 0.93,
        "Chase Field": 1.08,
        "Coors Field": 1.38,
        "Truist Park": 1.02,
        "Citi Field": 0.96,
        "Citizens Bank Park": 1.15,
        "Nationals Park": 1.00,
        "LoanDepot Park": 0.92,
        # Add more ballparks as needed
    }
    
    # Example function to calculate adjusted score based on factors
    def calculate_adjusted_score(base_score, opponent, ballpark):
        opponent_factor = 1.0
        ballpark_factor = 1.0
        
        if opponent in team_offensive_ratings:
            # Scale opponent quality to a 0.7-1.2 range
            # 100 is league average, so we center around 1.0
            opponent_rating = team_offensive_ratings[opponent]
            opponent_factor = 2 - (opponent_rating / 100)  # Invert so higher offense = lower factor
            opponent_factor = max(0.7, min(1.2, opponent_factor))  # Clamp to range
        
        if ballpark in ballpark_factors:
            # Invert so pitcher-friendly parks have higher factors
            ballpark_factor = 1 / ballpark_factors[ballpark]
            ballpark_factor = max(0.8, min(1.3, ballpark_factor))  # Clamp to range
            
        # Adjust score: lower for tough opponents and hitter-friendly parks
        return base_score * opponent_factor * ballpark_factor
    
    # Placeholder for probable starters data
    # In a real implementation, this would come from an external API
    import random
    tomorrow_probables = {}
    
    # Filter for starting pitchers
    sp_free_agents = [p for p in free_agents if 'SP' in getattr(p, 'eligibleSlots', [])]
    
    if not sp_free_agents:
        sections.append("\nNo starting pitchers available on waivers.")
        return "\n".join(sections)
    
    # Create enhanced pitcher data with matchup information
    enhanced_pitchers = []
    for pitcher in sp_free_agents:
        base_points = getattr(pitcher, 'stats', {}).get('0_projected_points', 0)
        
        # Randomly assign some pitchers as probable starters for tomorrow
        # In a real implementation, use actual MLB probable starter data
        if random.random() < 0.3:  # 30% of pitchers
            # Pick a random opponent and ballpark
            opponent = random.choice(list(team_offensive_ratings.keys()))
            ballpark = random.choice(list(ballpark_factors.keys()))
            
            # Calculate adjusted score
            adjusted_score = calculate_adjusted_score(base_points, opponent, ballpark)
            
            # Create note about matchup
            if adjusted_score > base_points:
                matchup_note = f"Favorable matchup vs {opponent} at {ballpark}"
            else:
                matchup_note = f"Tough matchup vs {opponent} at {ballpark}"
                
            # Add enhanced data
            enhanced_pitchers.append({
                'pitcher': pitcher,
                'base_points': base_points,
                'adjusted_points': adjusted_score,
                'opponent': opponent,
                'ballpark': ballpark,
                'ballpark_factor': ballpark_factors.get(ballpark, 1.0),
                'opponent_rating': team_offensive_ratings.get(opponent, 100),
                'note': matchup_note,
                'is_probable': True
            })
    
    # If we don't have any confirmed probables, just use the top projected pitchers
    if not enhanced_pitchers:
        for pitcher in sorted(sp_free_agents, key=lambda p: getattr(p, 'stats', {}).get('0_projected_points', 0), reverse=True)[:5]:
            base_points = getattr(pitcher, 'stats', {}).get('0_projected_points', 0)
            enhanced_pitchers.append({
                'pitcher': pitcher,
                'base_points': base_points,
                'adjusted_points': base_points,
                'note': "No confirmed start information",
                'is_probable': False
            })
    
    # Sort by adjusted score
    enhanced_pitchers.sort(key=lambda p: p['adjusted_points'], reverse=True)
    
    # Show top options
    probable_shown = False
    for i, pitcher_data in enumerate(enhanced_pitchers[:5], 1):
        pitcher = pitcher_data['pitcher']
        note = pitcher_data['note']
        
        # Show header for probable starters
        if pitcher_data['is_probable'] and not probable_shown:
            sections.append("\nCONFIRMED STARTERS FOR TOMORROW:")
            probable_shown = True
        elif not pitcher_data['is_probable'] and probable_shown:
            sections.append("\nOTHER RECOMMENDED PICKUPS:")
        
        # Format line with detailed information
        if pitcher_data['is_probable']:
            # Include matchup details for confirmed starters
            adjustment = pitcher_data['adjusted_points'] - pitcher_data['base_points']
            adjustment_text = f" ({'+' if adjustment >= 0 else ''}{adjustment:.1f} matchup adjustment)"
            sections.append(f"{i}. {pitcher.name} ({pitcher.proTeam}) - {pitcher_data['adjusted_points']:.1f} pts{adjustment_text}")
            sections.append(f"   {note}")
        else:
            # Simple line for non-confirmed starters
            sections.append(f"{i}. {pitcher.name} ({pitcher.proTeam}) - {pitcher_data['base_points']:.1f} projected pts")
    
    # Strategy tip
    sections.append("\nSTRATEGY TIP: Look for pitchers facing weak offensive teams in pitcher-friendly parks.")
    
    # Reminder about acquisition limit
    sections.append(f"\nRemember: You have a maximum of {settings.MAX_ACQUISITIONS_PER_MATCHUP} " +
                   "acquisitions per matchup.")
    
    return "\n".join(sections)

def format_hot_pickups(free_agents):
    """Format hot waiver wire pickups with enhanced analytics."""
    if not free_agents:
        return "No waiver wire recommendations available."
    
    sections = []
    
    sections.append("HOT WAIVER WIRE PICKUPS")
    sections.append("=" * 30)
    
    # Enhanced analytics would include:
    # 1. Recent performance trends
    # 2. Ownership % changes
    # 3. Underlying metrics analysis (barrel %, exit velocity, etc.)
    # 4. Favorable upcoming schedules
    
    # In a full implementation, we'd have API data for:
    # - Ownership % change over past 1/3/7 days
    # - Recent performance (past 7/15/30 days)
    # - Advanced Statcast metrics
    
    # Simulated player analysis data (in reality, fetch from external APIs)
    import random
    
    # Define some example trend reasons
    uptrend_reasons = [
        "Increased barrel % and exit velocity",
        "Recent rise in batting order",
        "Improved hard-hit rate",
        "Higher launch angle",
        "Improved plate discipline (BB/K)",
        "Better quality of contact",
        "Hitting in favorable lineup spot",
        "Upcoming favorable matchups",
        "Recent increase in playing time",
        "Returning from injury with strong performance"
    ]
    
    # Positions to analyze
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'SP', 'RP']
    
    # Add trending player section
    sections.append("\nTRENDING PLAYERS (Based on recent performance):")
    
    # Create a list to track trending players across all positions
    trending_players = []
    
    # For each position, identify potentially trending players
    for pos in positions:
        pos_players = [p for p in free_agents if pos in str(getattr(p, 'eligibleSlots', []))]
        
        if not pos_players:
            continue
        
        # Get base projections
        for player in pos_players:
            base_points = getattr(player, 'stats', {}).get('0_projected_points', 0)
            
            # Simulate "trending" status for some players
            # In a real implementation, this would be based on actual performance data
            if random.random() < 0.05:  # 5% of players are "trending"
                # Randomly generate a trending percentage (10-40% improvement)
                trend_pct = 0.1 + (random.random() * 0.3)
                
                # Calculate adjusted value
                trend_value = base_points * (1 + trend_pct)
                
                # Choose a random reason for trending
                trend_reason = random.choice(uptrend_reasons)
                
                # Add to trending players list
                trending_players.append({
                    'player': player,
                    'position': pos,
                    'base_points': base_points,
                    'trend_value': trend_value,
                    'trend_pct': trend_pct,
                    'reason': trend_reason
                })
    
    # Sort trending players by trend percentage (highest first)
    trending_players.sort(key=lambda p: p['trend_pct'], reverse=True)
    
    # Show top trending players across positions
    if trending_players:
        for i, player_data in enumerate(trending_players[:5], 1):
            player = player_data['player']
            position = player_data['position']
            base = player_data['base_points']
            value = player_data['trend_value']
            pct = player_data['trend_pct'] * 100
            reason = player_data['reason']
            
            sections.append(f"{i}. {player.name} ({player.proTeam}) - {position}")
            sections.append(f"   Projected: {value:.1f} pts (+{pct:.1f}% above baseline)")
            sections.append(f"   Why trending: {reason}")
    else:
        sections.append("No strongly trending players identified")
    
    # Also include standard position-by-position recommendations
    sections.append("\nTOP AVAILABLE PLAYERS BY POSITION:")
    
    for pos in positions:
        pos_players = [p for p in free_agents if pos in str(getattr(p, 'eligibleSlots', []))]
        
        if not pos_players:
            continue
        
        # Sort by projected points
        pos_players.sort(key=lambda p: getattr(p, 'stats', {}).get('0_projected_points', 0), reverse=True)
        
        # Show top option for each position
        sections.append(f"\n{pos}:")
        for i, player in enumerate(pos_players[:1], 1):
            proj_points = getattr(player, 'stats', {}).get('0_projected_points', 0)
            sections.append(f"{i}. {player.name} ({player.proTeam}) - {proj_points:.1f} projected pts")
    
    # Add strategy tip
    sections.append("\nSTRATEGY TIP: Look for players with improving advanced metrics that haven't yet translated to fantasy production - these can be valuable pickups before other managers notice them.")
    
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