#!/usr/bin/env python
"""
Analyze MLB schedule to find favorable matchups and streaming opportunities.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.analysis.schedule_analysis import ScheduleAnalyzer

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

def format_team_schedule_analysis(analysis):
    """Format team schedule analysis into readable text."""
    sections = []
    
    # Header
    sections.append(f"SCHEDULE ANALYSIS: {analysis['team']}")
    sections.append("=" * 50)
    sections.append(f"Analysis Date: {analysis['analysis_date']}")
    sections.append(f"Days Analyzed: {analysis['days_analyzed']}")
    sections.append("")
    
    # Overall assessment
    sections.append("OVERALL SCHEDULE ASSESSMENT")
    sections.append("-" * 30)
    sections.append(f"Schedule Quality: {analysis['schedule_quality']}")
    sections.append(f"Offensive Advantage: {analysis['offensive_schedule_advantage']:.2f}")
    sections.append(f"Pitching Advantage: {analysis['pitching_schedule_advantage']:.2f}")
    sections.append(f"Overall Advantage: {analysis['overall_schedule_advantage']:.2f}")
    sections.append("")
    
    # Upcoming games
    sections.append("UPCOMING GAMES")
    sections.append("-" * 30)
    
    games = analysis['games']
    for game in games:
        date_obj = datetime.strptime(game['date'], '%Y-%m-%d')
        date_str = date_obj.strftime('%a, %b %d')
        
        home_away = "vs" if game['is_home'] else "@"
        sections.append(f"{date_str}: {home_away} {game['opponent']} ({game['ballpark']})")
        
        # Add matchup quality indicators
        offense_emoji = "🔴" if game['offense_rating'] < 95 else "🟢" if game['offense_rating'] > 105 else "🟡"
        pitching_emoji = "🔴" if game['pitching_rating'] < 95 else "🟢" if game['pitching_rating'] > 105 else "🟡"
        
        sections.append(f"  Offense: {offense_emoji} {game['offense_quality']} ({game['offense_rating']:.1f})")
        sections.append(f"  Pitching: {pitching_emoji} {game['pitching_quality']} ({game['pitching_rating']:.1f})")
        sections.append("")
    
    # Strategic recommendations
    sections.append("STRATEGIC RECOMMENDATIONS")
    sections.append("-" * 30)
    
    # Identify best and worst matchups
    best_offense = max(games, key=lambda x: x['offense_rating']) if games else None
    worst_offense = min(games, key=lambda x: x['offense_rating']) if games else None
    best_pitching = max(games, key=lambda x: x['pitching_rating']) if games else None
    worst_pitching = min(games, key=lambda x: x['pitching_rating']) if games else None
    
    if best_offense:
        best_off_date = datetime.strptime(best_offense['date'], '%Y-%m-%d').strftime('%a, %b %d')
        sections.append(f"Best offensive matchup: {best_off_date} {analysis['team']} vs {best_offense['opponent']}")
        sections.append(f"  Rating: {best_offense['offense_rating']:.1f} - {best_offense['offense_quality']}")
        sections.append("  Strategy: Play all your hitters from this team")
    
    if best_pitching:
        best_pitch_date = datetime.strptime(best_pitching['date'], '%Y-%m-%d').strftime('%a, %b %d')
        sections.append(f"Best pitching matchup: {best_pitch_date} {analysis['team']} vs {best_pitching['opponent']}")
        sections.append(f"  Rating: {best_pitching['pitching_rating']:.1f} - {best_pitching['pitching_quality']}")
        sections.append("  Strategy: Stream pitchers from this team")
    
    if worst_offense:
        worst_off_date = datetime.strptime(worst_offense['date'], '%Y-%m-%d').strftime('%a, %b %d')
        sections.append(f"Worst offensive matchup: {worst_off_date} {analysis['team']} vs {worst_offense['opponent']}")
        sections.append(f"  Rating: {worst_offense['offense_rating']:.1f} - {worst_offense['offense_quality']}")
        sections.append("  Strategy: Consider benching fringe hitters")
    
    if worst_pitching:
        worst_pitch_date = datetime.strptime(worst_pitching['date'], '%Y-%m-%d').strftime('%a, %b %d')
        sections.append(f"Worst pitching matchup: {worst_pitch_date} {analysis['team']} vs {worst_pitching['opponent']}")
        sections.append(f"  Rating: {worst_pitching['pitching_rating']:.1f} - {worst_pitching['pitching_quality']}")
        sections.append("  Strategy: Avoid streaming pitchers, bench borderline arms")
    
    return "\n".join(sections)

def format_streaming_opportunities(opportunities, is_pitching=True):
    """Format streaming opportunities into readable text."""
    sections = []
    
    # Header
    if is_pitching:
        sections.append("PITCHER STREAMING OPPORTUNITIES")
    else:
        sections.append("HITTER STREAMING OPPORTUNITIES")
    sections.append("=" * 50)
    sections.append("")
    
    # For each date
    for date_str, daily_opps in sorted(opportunities.items()):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        sections.append(f"{date_obj.strftime('%A, %B %d')}:")
        sections.append("-" * 30)
        
        if not daily_opps:
            sections.append("No strong opportunities identified")
            sections.append("")
            continue
        
        # Show top opportunities for each day
        for i, opp in enumerate(daily_opps[:5], 1):
            team = opp['team']
            opponent = opp['opponent']
            ballpark = opp['ballpark']
            quality = opp['quality']
            rating = opp['rating']
            home_away = "vs" if opp['is_home'] else "@"
            
            sections.append(f"{i}. {team} {home_away} {opponent} ({ballpark})")
            sections.append(f"   Rating: {rating:.1f} - {quality}")
            sections.append(f"   {opp['recommendation']}")
            sections.append("")
    
    return "\n".join(sections)

def main():
    """Main function to analyze schedule and streaming opportunities."""
    parser = argparse.ArgumentParser(description='Analyze MLB schedule for fantasy baseball')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--team', help='MLB team abbreviation to analyze (e.g., NYY, LAD)')
    parser.add_argument('--days', type=int, default=14, help='Number of days to analyze')
    parser.add_argument('--streaming', action='store_true', help='Find streaming opportunities')
    parser.add_argument('--hitting', action='store_true', help='Find hitting matchups (with --streaming)')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create schedule analyzer
    analyzer = ScheduleAnalyzer()
    
    # Today's date for filenames
    today = datetime.now().strftime('%Y-%m-%d')
    
    # If a specific team is provided
    if args.team:
        # Analyze team schedule
        analysis = analyzer.analyze_team_schedule(args.team, days_ahead=args.days)
        
        # Format and save the report
        report = format_team_schedule_analysis(analysis)
        report_path = os.path.join(args.output_dir, f'schedule_analysis_{args.team}_{today}.txt')
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"Team schedule analysis saved to: {report_path}")
    
    # If streaming analysis is requested
    if args.streaming:
        if args.hitting:
            # Find hitting matchups
            opportunities = analyzer.find_hitter_streaming_opportunities(days_ahead=args.days)
            
            # Format and save the report
            report = format_streaming_opportunities(opportunities, is_pitching=False)
            report_path = os.path.join(args.output_dir, f'hitting_matchups_{today}.txt')
            
            with open(report_path, 'w') as f:
                f.write(report)
            
            print(f"Hitting matchups saved to: {report_path}")
        else:
            # Find pitching streaming opportunities
            opportunities = analyzer.find_streaming_opportunities(days_ahead=args.days)
            
            # Format and save the report
            report = format_streaming_opportunities(opportunities, is_pitching=True)
            report_path = os.path.join(args.output_dir, f'pitching_streams_{today}.txt')
            
            with open(report_path, 'w') as f:
                f.write(report)
            
            print(f"Pitching streaming opportunities saved to: {report_path}")
    
    # If no specific analysis was requested, show general help
    if not args.team and not args.streaming:
        print("Please specify an analysis type:")
        print("  --team TEAM  Analyze schedule for a specific MLB team")
        print("  --streaming  Find pitching streaming opportunities")
        print("  --streaming --hitting  Find favorable hitting matchups")
        print("  --days DAYS  Number of days to analyze (default: 14)")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())