#!/usr/bin/env python
"""
Analyze team strengths and weaknesses by category and recommend improvements.
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
from src.analysis.category_analysis import CategoryAnalyzer

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

def format_category_analysis(analysis):
    """Format category analysis into readable text."""
    sections = []
    
    # Header
    sections.append(f"CATEGORY ANALYSIS: {analysis['team_name']}")
    sections.append("=" * 60)
    sections.append("")
    
    # Batting Categories
    sections.append("BATTING CATEGORIES")
    sections.append("-" * 30)
    
    # Create a table header for batting stats
    header = f"{'Category':<6} {'Value':>10} {'League Avg':>12} {'Percentile':>10} {'Strength':<12}"
    sections.append(header)
    sections.append("-" * 60)
    
    # Add each batting category
    batting_cats = sorted(analysis['categories']['batting'].items())
    for cat_name, cat_data in batting_cats:
        # Format row
        value = f"{cat_data['value']:.3f}" if cat_name in ['AVG', 'OBP', 'SLG', 'OPS'] else f"{cat_data['value']:.1f}"
        league_avg = f"{cat_data['league_mean']:.3f}" if cat_name in ['AVG', 'OBP', 'SLG', 'OPS'] else f"{cat_data['league_mean']:.1f}"
        percentile = f"{cat_data['percentile']:.1f}%"
        strength = cat_data['strength']
        
        # Color-code by strength
        if strength == "Very Strong":
            strength = "✅✅ " + strength
        elif strength == "Strong":
            strength = "✅ " + strength
        elif strength == "Weak":
            strength = "❌ " + strength
        elif strength == "Very Weak":
            strength = "❌❌ " + strength
        
        row = f"{cat_name:<6} {value:>10} {league_avg:>12} {percentile:>10} {strength:<12}"
        sections.append(row)
    
    sections.append("")
    
    # Pitching Categories
    sections.append("PITCHING CATEGORIES")
    sections.append("-" * 30)
    
    # Create a table header for pitching stats
    header = f"{'Category':<6} {'Value':>10} {'League Avg':>12} {'Percentile':>10} {'Strength':<12}"
    sections.append(header)
    sections.append("-" * 60)
    
    # Add each pitching category
    pitching_cats = sorted(analysis['categories']['pitching'].items())
    for cat_name, cat_data in pitching_cats:
        # Format row
        is_rate_stat = cat_name in ['ERA', 'WHIP', 'K/9', 'BB/9', 'K/BB']
        value = f"{cat_data['value']:.2f}" if is_rate_stat else f"{cat_data['value']:.1f}"
        league_avg = f"{cat_data['league_mean']:.2f}" if is_rate_stat else f"{cat_data['league_mean']:.1f}"
        percentile = f"{cat_data['percentile']:.1f}%"
        strength = cat_data['strength']
        
        # Color-code by strength
        if strength == "Very Strong":
            strength = "✅✅ " + strength
        elif strength == "Strong":
            strength = "✅ " + strength
        elif strength == "Weak":
            strength = "❌ " + strength
        elif strength == "Very Weak":
            strength = "❌❌ " + strength
        
        row = f"{cat_name:<6} {value:>10} {league_avg:>12} {percentile:>10} {strength:<12}"
        sections.append(row)
    
    sections.append("")
    
    # Team Strengths
    sections.append("TEAM STRENGTHS")
    sections.append("-" * 30)
    
    # Batting strengths
    batting_strengths = analysis.get('strengths', {}).get('batting', [])
    if batting_strengths:
        sections.append("Batting: " + ", ".join(batting_strengths))
    else:
        sections.append("Batting: No significant strengths identified")
    
    # Pitching strengths
    pitching_strengths = analysis.get('strengths', {}).get('pitching', [])
    if pitching_strengths:
        sections.append("Pitching: " + ", ".join(pitching_strengths))
    else:
        sections.append("Pitching: No significant strengths identified")
    
    sections.append("")
    
    # Team Weaknesses
    sections.append("TEAM WEAKNESSES")
    sections.append("-" * 30)
    
    # Batting weaknesses
    batting_weaknesses = analysis.get('weaknesses', {}).get('batting', [])
    if batting_weaknesses:
        sections.append("Batting: " + ", ".join(batting_weaknesses))
    else:
        sections.append("Batting: No significant weaknesses identified")
    
    # Pitching weaknesses
    pitching_weaknesses = analysis.get('weaknesses', {}).get('pitching', [])
    if pitching_weaknesses:
        sections.append("Pitching: " + ", ".join(pitching_weaknesses))
    else:
        sections.append("Pitching: No significant weaknesses identified")
    
    return "\n".join(sections)

def format_improvement_recommendations(recommendations):
    """Format improvement recommendations into readable text."""
    sections = []
    
    # Header
    sections.append(f"CATEGORY IMPROVEMENT RECOMMENDATIONS: {recommendations['team_name']}")
    sections.append("=" * 70)
    sections.append("")
    
    # Team Weaknesses
    sections.append("TEAM WEAKNESSES TO ADDRESS")
    sections.append("-" * 30)
    
    # Batting weaknesses
    batting_weaknesses = recommendations.get('weaknesses', {}).get('batting', [])
    if batting_weaknesses:
        sections.append("Batting: " + ", ".join(batting_weaknesses))
    else:
        sections.append("Batting: No significant weaknesses identified")
    
    # Pitching weaknesses
    pitching_weaknesses = recommendations.get('weaknesses', {}).get('pitching', [])
    if pitching_weaknesses:
        sections.append("Pitching: " + ", ".join(pitching_weaknesses))
    else:
        sections.append("Pitching: No significant weaknesses identified")
    
    sections.append("")
    
    # Improvement Strategies
    sections.append("IMPROVEMENT STRATEGIES")
    sections.append("-" * 30)
    
    # Batting strategies
    batting_strategies = recommendations.get('improvement_strategies', {}).get('batting', {})
    if batting_strategies:
        sections.append("Batting Strategies:")
        for cat, strategy in batting_strategies.items():
            sections.append(f"• {cat}: {strategy}")
    
    # Pitching strategies
    pitching_strategies = recommendations.get('improvement_strategies', {}).get('pitching', {})
    if pitching_strategies:
        sections.append("\nPitching Strategies:")
        for cat, strategy in pitching_strategies.items():
            sections.append(f"• {cat}: {strategy}")
    
    sections.append("")
    
    # Free Agent Recommendations
    fa_recs = recommendations.get('free_agent_recommendations', {})
    if fa_recs and (fa_recs.get('batting') or fa_recs.get('pitching')):
        sections.append("FREE AGENT RECOMMENDATIONS")
        sections.append("-" * 30)
        
        # Batting free agents
        batting_fas = fa_recs.get('batting', {})
        if batting_fas:
            for cat, players in batting_fas.items():
                if players:
                    sections.append(f"\nBest available for {cat}:")
                    for player in players:
                        name = player['name']
                        team = player['team']
                        positions = player['positions']
                        value = player['value']
                        
                        # Format value based on category
                        if cat in ['AVG', 'OBP', 'SLG', 'OPS']:
                            value_str = f"{value:.3f}"
                        else:
                            value_str = f"{value:.1f}"
                        
                        sections.append(f"• {name} ({team}) - {positions} - {cat}: {value_str}")
        
        # Pitching free agents
        pitching_fas = fa_recs.get('pitching', {})
        if pitching_fas:
            for cat, players in pitching_fas.items():
                if players:
                    sections.append(f"\nBest available for {cat}:")
                    for player in players:
                        name = player['name']
                        team = player['team']
                        positions = player['positions']
                        value = player['value']
                        
                        # Format value based on category
                        if cat in ['ERA', 'WHIP', 'K/9', 'BB/9', 'K/BB']:
                            value_str = f"{value:.2f}"
                        else:
                            value_str = f"{value:.1f}"
                        
                        sections.append(f"• {name} ({team}) - {positions} - {cat}: {value_str}")
    
    return "\n".join(sections)

def format_trade_targets(recommendations):
    """Format trade target recommendations into readable text."""
    sections = []
    
    # Header
    sections.append(f"TRADE TARGET RECOMMENDATIONS: {recommendations['team_name']}")
    sections.append("=" * 70)
    sections.append("")
    
    # Check if we have any trade targets
    trade_targets = recommendations.get('trade_targets', {})
    if not trade_targets or (not trade_targets.get('batting') and not trade_targets.get('pitching')):
        sections.append("No trade targets identified. Your team may not have significant categorical weaknesses, or other teams may not have significant strengths in your weak categories.")
        return "\n".join(sections)
    
    # Batting trade targets
    batting_targets = trade_targets.get('batting', {})
    if batting_targets:
        sections.append("BATTING TRADE TARGETS")
        sections.append("-" * 30)
        
        for cat, players in batting_targets.items():
            if players:
                sections.append(f"\nPotential targets to improve {cat}:")
                for player in players:
                    name = player['name']
                    team = player['team']
                    positions = player['positions']
                    value = player['value']
                    owner = player['owner_team']
                    
                    # Format value based on category
                    if cat in ['AVG', 'OBP', 'SLG', 'OPS']:
                        value_str = f"{value:.3f}"
                    else:
                        value_str = f"{value:.1f}"
                    
                    sections.append(f"• {name} ({team}) - {positions} - {cat}: {value_str}")
                    sections.append(f"  Owner: {owner}")
    
    # Pitching trade targets
    pitching_targets = trade_targets.get('pitching', {})
    if pitching_targets:
        sections.append("\nPITCHING TRADE TARGETS")
        sections.append("-" * 30)
        
        for cat, players in pitching_targets.items():
            if players:
                sections.append(f"\nPotential targets to improve {cat}:")
                for player in players:
                    name = player['name']
                    team = player['team']
                    positions = player['positions']
                    value = player['value']
                    owner = player['owner_team']
                    
                    # Format value based on category
                    if cat in ['ERA', 'WHIP', 'K/9', 'BB/9', 'K/BB']:
                        value_str = f"{value:.2f}"
                    else:
                        value_str = f"{value:.1f}"
                    
                    sections.append(f"• {name} ({team}) - {positions} - {cat}: {value_str}")
                    sections.append(f"  Owner: {owner}")
    
    # Add notes on trade strategy
    sections.append("\nTRADE STRATEGY NOTES")
    sections.append("-" * 30)
    sections.append("• Look for trade partners with complementary needs - your strengths matching their weaknesses")
    sections.append("• Consider trading from categories where you have excess strength")
    sections.append("• Prioritize positional flexibility in trade targets")
    sections.append("• Don't overpay for category specialists unless the category is crucial for your team")
    
    return "\n".join(sections)

def main():
    """Main function to analyze team categories and recommend improvements."""
    parser = argparse.ArgumentParser(description='Analyze team categories and recommend improvements')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
    parser.add_argument('--team-id', type=int, help='Team ID to analyze (defaults to configured team)')
    parser.add_argument('--improvements', action='store_true', help='Show improvement recommendations')
    parser.add_argument('--trades', action='store_true', help='Show trade target recommendations')
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
    
    # Get teams
    teams = client.get_teams()
    
    # Create category analyzer
    analyzer = CategoryAnalyzer(teams)
    
    # Today's date for filenames
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Analyze team categories
    analysis = analyzer.analyze_team_categories(team_id)
    
    # Format and save the basic analysis
    report = format_category_analysis(analysis)
    report_path = os.path.join(args.output_dir, f'category_analysis_{today}.txt')
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"Category analysis saved to: {report_path}")
    
    # If improvements requested
    if args.improvements:
        # Get free agents
        free_agents = client.get_free_agents(size=300)
        
        # Get recommendations
        recommendations = analyzer.recommend_category_improvements(team_id, free_agents)
        
        # Format and save the recommendations
        report = format_improvement_recommendations(recommendations)
        report_path = os.path.join(args.output_dir, f'category_improvements_{today}.txt')
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"Improvement recommendations saved to: {report_path}")
    
    # If trade targets requested
    if args.trades:
        # Get trade target recommendations
        trade_recs = analyzer.identify_trade_targets(team_id)
        
        # Format and save the trade recommendations
        report = format_trade_targets(trade_recs)
        report_path = os.path.join(args.output_dir, f'trade_targets_{today}.txt')
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"Trade target recommendations saved to: {report_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())