# scripts/team_analysis.py
#!/usr/bin/env python
"""
Generate a team analysis report.
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
from src.analysis.team_analysis import TeamAnalyzer
from src.visualization.charts import TeamVisualizer

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
    """Main function to generate team analysis report."""
    parser = argparse.ArgumentParser(description='Generate a team analysis report')
    parser.add_argument('--output-dir', default='output', help='Directory to save output files')
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
    
    # Get teams
    teams = client.get_teams()

    # Debug team object structure
    if teams and len(teams) > 0:
        first_team = teams[0]
        logger.info("Team object attributes:")
        for attr in dir(first_team):
            if not attr.startswith('_'):  # Skip internal attributes
                value = getattr(first_team, attr)
                if not callable(value):  # Skip methods
                    logger.info(f"{attr}: {type(value)}")
                    # If it's a list and has elements, show the first element's type
                    if isinstance(value, list) and value:
                        logger.info(f"  First element type: {type(value[0])}")
                        # If it's a dictionary, show the keys
                        if isinstance(value[0], dict):
                            logger.info(f"  Keys: {value[0].keys()}")

    
    # Create team analyzer
    analyzer = TeamAnalyzer(teams)
    
    # Get standings
    standings = analyzer.get_standings()
    
    # Get division standings
    division_standings = analyzer.get_division_standings()
    
    # Create visualizer
    visualizer = TeamVisualizer(output_dir=args.output_dir)
    
    # Generate visualizations
    standings_chart = visualizer.visualize_standings(teams)
    win_pct_chart = visualizer.visualize_win_percentage(teams)
    division_chart = visualizer.visualize_division_comparison(teams)
    
    # Generate report
    report_path = os.path.join(args.output_dir, 'team_analysis_report.txt')
    with open(report_path, 'w') as f:
        f.write(f"ESPN Fantasy Baseball - Team Analysis Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"League: {client.league.settings.name}\n\n")
        
        f.write("League Standings\n")
        f.write("---------------\n")
        f.write(standings.to_string(index=False))
        f.write("\n\n")
        
        if division_standings:
            f.write("Division Standings\n")
            f.write("-----------------\n")
            for division_name, df in division_standings.items():
                f.write(f"{division_name}\n")
                f.write(df.to_string(index=False))
                f.write("\n\n")
        
        f.write("Visualization Files\n")
        f.write("------------------\n")
        f.write(f"Standings chart: {os.path.basename(standings_chart)}\n")
        f.write(f"Win percentage chart: {os.path.basename(win_pct_chart)}\n")
        if division_chart:
            f.write(f"Division comparison chart: {os.path.basename(division_chart)}\n")
    
    print(f"Team analysis report generated at: {report_path}")
    print(f"Visualizations saved to: {args.output_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())