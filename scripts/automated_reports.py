# scripts/automated_reports.py
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import schedule
import time
import jinja2

# Add project root to path to ensure imports work
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Imports
from src.api.client import ESPNFantasyClient
from src.analysis.category_analysis import CategoryAnalyzer
from src.analysis.player_analysis import PlayerAnalyzer
from src.analysis.team_analysis import TeamAnalyzer
from src.analysis.matchup_analysis import MatchupAnalyzer
from src.visualization.category_charts import CategoryVisualizer
from src.visualization.trend_charts import TrendVisualizer
from src.visualization.charts import TeamVisualizer
from src.visualization.player_charts import PlayerVisualizer
from src.visualization.delivery import ReportDelivery
from config.settings import (
    LEAGUE_ID, TEAM_ID, ESPN_S2, SWID, YEAR,
    EMAIL_ENABLED, EMAIL_FROM, EMAIL_TO, EMAIL_SUBJECT_PREFIX,
    EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, EMAIL_USERNAME, EMAIL_PASSWORD,
    REPORT_DIR, DAILY_REPORT_ENABLED, WEEKLY_PREVIEW_ENABLED
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(REPORT_DIR, 'automated_reports.log'))
    ]
)
logger = logging.getLogger(__name__)

# Create report directories
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(os.path.join(REPORT_DIR, 'daily'), exist_ok=True)
os.makedirs(os.path.join(REPORT_DIR, 'weekly'), exist_ok=True)
os.makedirs(os.path.join(REPORT_DIR, 'images'), exist_ok=True)
os.makedirs(os.path.join(REPORT_DIR, 'data'), exist_ok=True)

# Set up Jinja2 environment for HTML templates
template_loader = jinja2.FileSystemLoader(os.path.join(project_root, 'templates'))
template_env = jinja2.Environment(loader=template_loader)

# Add datetime function
def datetime_now():
    return datetime.now()

template_env.globals['now'] = datetime_now

class AutomatedReportGenerator:
    """Generate and deliver automated fantasy baseball reports."""
    
    def __init__(self, league_id=LEAGUE_ID, team_id=TEAM_ID, espn_s2=ESPN_S2, swid=SWID, year=None):
        """Initialize the report generator."""
        self.league_id = league_id
        self.team_id = int(team_id) if team_id else None
        self.espn_s2 = espn_s2
        self.swid = swid
        self.year = year if year else YEAR
        self.client = None
        self.teams = []
        self.my_team = None
        self.image_dir = os.path.join(REPORT_DIR, 'images')
        
        # Visualizers
        self.team_visualizer = TeamVisualizer(output_dir=self.image_dir)
        self.player_visualizer = PlayerVisualizer(output_dir=self.image_dir)
        self.category_visualizer = CategoryVisualizer(output_dir=self.image_dir)
        self.trend_visualizer = TrendVisualizer(output_dir=self.image_dir)
        
        # Initialize client if credentials available
        if espn_s2 and swid:
            self.init_client()
    
    def init_client(self):
        """Initialize the ESPN client."""
        try:
            # Match the order of parameters in ESPNFantasyClient.__init__
            self.client = ESPNFantasyClient(
                league_id=self.league_id,
                year=self.year,
                espn_s2=self.espn_s2,
                swid=self.swid
            )
            
            # Connect to the API
            self.client.connect()
            
            # Get teams
            self.teams = self.client.get_teams()
            self.my_team = next((team for team in self.teams if team.team_id == self.team_id), None)
            logger.info(f"Initialized client for league {self.league_id}, team {self.team_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize client: {str(e)}")
            return False
    
    def generate_daily_report(self):
        """Generate and deliver the daily report."""
        logger.info("Generating daily report...")
        
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        report_filename = f"daily_report_{today}.html"
        report_path = os.path.join(REPORT_DIR, 'daily', report_filename)
        
        # Report data collection
        report_data = {
            "date": today,
            "team_name": getattr(self.my_team, 'team_name', None) or 
                         getattr(self.my_team, 'name', None) or 
                         "Your Team",
            "report_type": "Daily Fantasy Baseball Report",
            "sections": []
        }
        
        # Generate attachment images
        attachments = []
        
        try:
            # 1. Current team status
            if self.teams:
                team_analyzer = TeamAnalyzer(self.teams)
                team_stats = team_analyzer.get_team_stats(self.team_id)
                
                # Generate standings visualization
                standings_path = self.team_visualizer.visualize_standings(self.teams, 
                                                                         filename=f"standings_{today}.png")
                attachments.append(standings_path)
                
                # Team status section
                report_data["sections"].append({
                    "title": "Team Status",
                    "content": [
                        f"Current Record: {team_stats['record']['wins']}-{team_stats['record']['losses']}" + 
                        (f"-{team_stats['record']['ties']}" if team_stats['record'].get('ties', 0) > 0 else ""),
                        f"Current Standing: {team_stats['standing']} of {len(self.teams)}",
                        f"Win Percentage: {team_stats['win_percentage']:.3f}"
                    ],
                    "images": [os.path.basename(standings_path)]
                })
            
            # 2. Category Analysis
            if self.teams and self.my_team and hasattr(self.my_team, 'roster') and self.my_team.roster:
                category_analyzer = CategoryAnalyzer(self.teams)
                team_analysis = category_analyzer.analyze_team_categories(self.team_id)
                
                # Generate category visualization
                cat_viz_path = self.category_visualizer.visualize_category_strengths(
                    team_analysis, filename=f"category_strengths_{today}.png")
                attachments.append(cat_viz_path)
                
                # Format strengths and weaknesses
                batting_strengths = team_analysis["strengths"]["batting"]
                batting_weaknesses = team_analysis["weaknesses"]["batting"]
                pitching_strengths = team_analysis["strengths"]["pitching"]
                pitching_weaknesses = team_analysis["weaknesses"]["pitching"]
                
                report_data["sections"].append({
                    "title": "Category Analysis",
                    "content": [
                        "Batting Strengths: " + (", ".join(batting_strengths) if batting_strengths else "None"),
                        "Batting Weaknesses: " + (", ".join(batting_weaknesses) if batting_weaknesses else "None"),
                        "Pitching Strengths: " + (", ".join(pitching_strengths) if pitching_strengths else "None"),
                        "Pitching Weaknesses: " + (", ".join(pitching_weaknesses) if pitching_weaknesses else "None")
                    ],
                    "images": [os.path.basename(cat_viz_path)]
                })
            
            # 3. Player Analysis - Hot/Cold Players
            if self.my_team and hasattr(self.my_team, 'roster') and self.my_team.roster:
                player_analyzer = PlayerAnalyzer()
                hot_players = player_analyzer.find_hot_players(self.my_team.roster, days=7)
                cold_players = player_analyzer.find_cold_players(self.my_team.roster, days=7)
                
                # For demo purposes, generate trend for first hot player if available
                trend_path = None
                if hot_players:
                    # In a real implementation, you'd have trending data
                    # This is just for demonstration
                    player_name = hot_players[0]["name"]
                    dates = [(datetime.now() - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(14, -1, -1)]
                    values = [0.250 + 0.003 * x + np.random.normal(0, 0.02) for x in range(15)]
                    trend_path = self.trend_visualizer.visualize_player_trend(
                        player_name, "AVG", values, dates, filename=f"trend_{player_name.replace(' ', '_').lower()}_{today}.png")
                    attachments.append(trend_path)
                
                report_data["sections"].append({
                    "title": "Player Trends",
                    "content": [
                        "Hot Players (Last 7 Days):",
                        *[f"• {p['name']} ({p['position']}): {p['hot_stat']}" for p in hot_players[:5]],
                        "",
                        "Cold Players (Last 7 Days):",
                        *[f"• {p['name']} ({p['position']}): {p['cold_stat']}" for p in cold_players[:5]]
                    ],
                    "images": [os.path.basename(trend_path)] if trend_path else []
                })
            
            # 4. Matchup Preview - Next Opponent
            current_matchup = None
            if self.client:
                try:
                    matchup_analyzer = MatchupAnalyzer(self.client)
                    current_matchup = matchup_analyzer.get_current_matchup(self.team_id)
                    
                    if current_matchup:
                        opponent = current_matchup.team_2 if current_matchup.team_1.team_id == self.team_id else current_matchup.team_1
                        matchup_analysis = matchup_analyzer.analyze_matchup(current_matchup)
                        
                        # Get categories to target
                        categories_to_target = matchup_analyzer.recommend_categories_to_target(matchup_analysis)
                        
                        report_data["sections"].append({
                            "title": "Current Matchup",
                            "content": [
                                f"Opponent: {opponent.name}",
                                f"Matchup Period: Week {current_matchup.week}",
                                f"Current Score: {current_matchup.team_1_score} - {current_matchup.team_2_score}",
                                "",
                                "Categories to Target:",
                                *[f"• {cat}: {reason}" for cat, reason in categories_to_target.items()]
                            ],
                            "images": []
                        })
                except Exception as e:
                    logger.error(f"Error getting matchup data: {str(e)}")
            
            # 5. Daily Pitching Strategy
            try:
                # Get probable starters for my team (simplified for demo)
                pitchers = []
                if self.my_team and hasattr(self.my_team, 'roster') and self.my_team.roster:
                    pitchers = [p for p in self.my_team.roster if "SP" in getattr(p, "eligibleSlots", [])]
                
                # In a real implementation, you'd get actual probable start data
                # This is just for demonstration
                probable_starters = []
                for i, pitcher in enumerate(pitchers[:3]):  # Limit to 3 pitchers for demo
                    probable_starters.append({
                        "name": pitcher.name,
                        "team": getattr(pitcher, "proTeam", ""),
                        "opponent": f"vs. {['NYY', 'LAD', 'HOU', 'CHC', 'BOS'][i % 5]}",
                        "ballpark": f"{['Yankee Stadium', 'Dodger Stadium', 'Minute Maid Park', 'Wrigley Field', 'Fenway Park'][i % 5]}",
                        "opponent_rank": f"#{i+5} against {['RHP', 'LHP'][i % 2]}",
                        "recommendation": ["Start", "Consider", "Avoid"][i % 3]
                    })
                
                report_data["sections"].append({
                    "title": "Today's Pitching Strategy",
                    "content": [
                        *[f"• {p['name']} ({p['team']}) {p['opponent']} at {p['ballpark']} - {p['recommendation']}" 
                          for p in probable_starters],
                        "",
                        "Streaming Recommendations:",
                        "• Pitcher 1 (40% owned): vs. weak offense in pitcher-friendly park",
                        "• Pitcher 2 (28% owned): High K potential against swing-heavy lineup"
                    ],
                    "images": []
                })
            except Exception as e:
                logger.error(f"Error generating pitching strategy: {str(e)}")
            
            # 6. Waiver Wire / Free Agent Recommendations
            try:
                # In a real implementation, you'd get actual free agent recommendations
                # This is just for demonstration
                free_agent_recommendations = [
                    {"name": "Player A", "position": "OF", "reason": "5 HR in last 7 days, only 28% owned"},
                    {"name": "Player B", "position": "SP", "reason": "2 upcoming starts vs weak teams"},
                    {"name": "Player C", "position": "RP", "reason": "Next in line for saves, closer struggling"},
                    {"name": "Player D", "position": "1B", "reason": "Underlying metrics show breakout potential"},
                    {"name": "Player E", "position": "2B", "reason": "Recently moved to leadoff spot, SB upside"}
                ]
                
                report_data["sections"].append({
                    "title": "Waiver Wire Recommendations",
                    "content": [
                        *[f"• {p['name']} ({p['position']}): {p['reason']}" for p in free_agent_recommendations]
                    ],
                    "images": []
                })
            except Exception as e:
                logger.error(f"Error generating waiver recommendations: {str(e)}")
            
            # Render the HTML template
            template = template_env.get_template('daily_report.html')
            html_content = template.render(**report_data)
            
            # Save the HTML report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Log this report
            ReportDelivery.log_to_history('daily', f"Daily report for {today}", report_path)
            
            # Deliver the report via email if enabled
            if EMAIL_ENABLED and EMAIL_TO:
                email_subject = f"{EMAIL_SUBJECT_PREFIX}Daily Fantasy Report - {today}"
                
                # Create a plain text version for email clients that don't support HTML
                plain_text = f"Daily Fantasy Baseball Report - {today}\n\n"
                for section in report_data["sections"]:
                    plain_text += f"{section['title']}\n"
                    plain_text += "\n".join(section["content"])
                    plain_text += "\n\n"
                
                # Send the email with HTML content and attachments
                ReportDelivery.deliver_email(
                    subject=email_subject,
                    body=plain_text,
                    recipients=EMAIL_TO,
                    sender=EMAIL_FROM,
                    smtp_server=EMAIL_SMTP_SERVER,
                    smtp_port=EMAIL_SMTP_PORT,
                    username=EMAIL_USERNAME,
                    password=EMAIL_PASSWORD,
                    attachments=attachments,
                    use_tls=True,
                    html_content=html_content
                )
                
                logger.info(f"Daily report delivered via email to {', '.join(EMAIL_TO)}")
            
            logger.info(f"Daily report generated successfully: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            return None
    
    def generate_weekly_report(self):
        """Generate and deliver the weekly report."""
        logger.info("Generating weekly report...")
        
        today = datetime.now().strftime("%Y-%m-%d")
        report_filename = f"weekly_report_{today}.html"
        report_path = os.path.join(REPORT_DIR, 'weekly', report_filename)
        
        # Report data collection
        report_data = {
            "date": today,
            "team_name": getattr(self.my_team, 'team_name', None) or 
                         getattr(self.my_team, 'name', None) or 
                         "Your Team",
            "report_type": "Weekly Fantasy Baseball Report",
            "sections": []
        }
        
        # Generate attachment images
        attachments = []
        
        try:
            # 1. League Overview
            if self.teams:
                # Generate division comparison visualization
                division_path = self.team_visualizer.visualize_division_comparison(
                    self.teams, filename=f"division_comparison_{today}.png")
                attachments.append(division_path)
                
                # League overview section
                report_data["sections"].append({
                    "title": "League Overview",
                    "content": [
                        f"Total Teams: {len(self.teams)}",
                        "Division Leaders: " + ", ".join([t.name for t in self.teams if t.standing == 1][:3]),
                        "Recent Trends: Teams gaining ground, close races, etc."
                    ],
                    "images": [os.path.basename(division_path)]
                })
            
            # 2. Weekly Matchup Analysis in Detail
            current_matchup = None
            if self.client:
                try:
                    matchup_analyzer = MatchupAnalyzer(self.client)
                    current_matchup = matchup_analyzer.get_current_matchup(self.team_id)
                    
                    if current_matchup:
                        opponent = current_matchup.team_2 if current_matchup.team_1.team_id == self.team_id else current_matchup.team_1
                        matchup_analysis = matchup_analyzer.analyze_matchup(current_matchup)
                        
                        # Get detailed category comparisons
                        categories = matchup_analysis.get('category_analysis', {})
                        category_comparisons = []
                        
                        for category, details in categories.items():
                            advantage = details.get('advantage', 'Even')
                            my_value = details.get('team1_value', 0)
                            opp_value = details.get('team2_value', 0)
                            
                            if isinstance(my_value, (int, float)) and isinstance(opp_value, (int, float)):
                                category_comparisons.append(
                                    f"{category}: {my_value:.3f if category in ['AVG', 'OBP', 'SLG', 'ERA', 'WHIP'] else my_value} vs "
                                    f"{opp_value:.3f if category in ['AVG', 'OBP', 'SLG', 'ERA', 'WHIP'] else opp_value} - {advantage}"
                                )
                        
                        report_data["sections"].append({
                            "title": "Weekly Matchup Analysis",
                            "content": [
                                f"Opponent: {opponent.name}",
                                f"Matchup Period: Week {current_matchup.week}",
                                f"Current Score: {current_matchup.team_1_score} - {current_matchup.team_2_score}",
                                "",
                                "Category Breakdown:",
                                *category_comparisons,
                                "",
                                "Recommended Strategy:",
                                "• Focus on competitive categories where you have a chance to win",
                                "• Consider streaming pitchers on days X, Y, Z",
                                "• Potential category sacrifices if needed"
                            ],
                            "images": []
                        })
                except Exception as e:
                    logger.error(f"Error getting matchup data: {str(e)}")
            
            # 3. Weekly Schedule Analysis
            try:
                # In a real implementation, you'd get actual schedule data
                # This is just for demonstration
                schedule_analysis = {
                    "teams_with_7_games": ["LAD", "NYY", "CHC", "ATL"],
                    "teams_with_5_or_fewer": ["BOS", "HOU", "SDP"],
                    "favorable_hitting_matchups": ["COL (3 games at Coors)", "CIN (weak pitching staff)"],
                    "favorable_pitching_matchups": ["MIA (pitcher's park, weak offense)", "OAK (pitcher's park)"]
                }
                
                report_data["sections"].append({
                    "title": "Weekly Schedule Analysis",
                    "content": [
                        "Teams with 7 Games: " + ", ".join(schedule_analysis["teams_with_7_games"]),
                        "Teams with 5 or Fewer Games: " + ", ".join(schedule_analysis["teams_with_5_or_fewer"]),
                        "",
                        "Favorable Hitting Matchups:",
                        *[f"• {matchup}" for matchup in schedule_analysis["favorable_hitting_matchups"]],
                        "",
                        "Favorable Pitching Matchups:",
                        *[f"• {matchup}" for matchup in schedule_analysis["favorable_pitching_matchups"]]
                    ],
                    "images": []
                })
            except Exception as e:
                logger.error(f"Error generating schedule analysis: {str(e)}")
            
            # 4. Roster Optimization
            if self.my_team and hasattr(self.my_team, 'roster') and self.my_team.roster:
                # In a real implementation, you'd analyze the actual roster
                # This is just for demonstration
                position_needs = ["SS (current starter struggling)", "OF (need more power)"]
                roster_recommendations = [
                    "Consider dropping Player X (recent decline in performance)",
                    "Player Y better suited for bench than starting lineup",
                    "Too many players at 1B, consider trading for needs",
                    "IL spot available - stash high-upside prospect"
                ]
                
                report_data["sections"].append({
                    "title": "Roster Optimization",
                    "content": [
                        "Position Needs: " + ", ".join(position_needs),
                        "",
                        "Roster Recommendations:",
                        *[f"• {rec}" for rec in roster_recommendations]
                    ],
                    "images": []
                })
            
            # 5. Trade Recommendations
            if self.teams and self.my_team:
                # Use category analyzer to find trade targets
                category_analyzer = CategoryAnalyzer(self.teams)
                trade_recommendations = category_analyzer.identify_trade_targets(self.team_id)
                
                trade_targets = []
                for category_type in ["batting", "pitching"]:
                    for category, players in trade_recommendations.get("trade_targets", {}).get(category_type, {}).items():
                        for player in players[:2]:  # Limit to top 2 per category
                            trade_targets.append(
                                f"{player['name']} ({player['positions']}) - Owned by {player['owner_team']} - Strong in {category}"
                            )
                
                report_data["sections"].append({
                    "title": "Trade Recommendations",
                    "content": [
                        "Based on your team's needs and category analysis:",
                        *[f"• {target}" for target in trade_targets],
                        "",
                        "Trade Strategy:",
                        "• Target teams strong in your weak categories",
                        "• Consider trading from your pitching surplus (strength)",
                        "• Look for 2-for-1 deals to improve roster flexibility"
                    ],
                    "images": []
                })
            
            # 6. Long-term Outlook
            # In a real implementation, you'd have projection data
            # This is just for demonstration
            report_data["sections"].append({
                "title": "Long-term Outlook",
                "content": [
                    "Projected Final Standing: 3rd of 12",
                    "Playoff Odds: 78%",
                    "",
                    "Areas to Address for Playoff Push:",
                    "• Improve saves category (currently bottom 25%)",
                    "• Add more consistent power sources",
                    "• Balance risk/reward with pitching staff"
                ],
                "images": []
            })
            
            # Render the HTML template
            template = template_env.get_template('weekly_report.html')
            html_content = template.render(**report_data)
            
            # Save the HTML report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Log this report
            ReportDelivery.log_to_history('weekly', f"Weekly report for {today}", report_path)
            
            # Deliver the report via email if enabled
            if EMAIL_ENABLED and EMAIL_TO:
                email_subject = f"{EMAIL_SUBJECT_PREFIX}Weekly Fantasy Report - {today}"
                
                # Create a plain text version for email clients that don't support HTML
                plain_text = f"Weekly Fantasy Baseball Report - {today}\n\n"
                for section in report_data["sections"]:
                    plain_text += f"{section['title']}\n"
                    plain_text += "\n".join(section["content"])
                    plain_text += "\n\n"
                
                # Send the email with HTML content and attachments
                ReportDelivery.deliver_email(
                    subject=email_subject,
                    body=plain_text,
                    recipients=EMAIL_TO,
                    sender=EMAIL_FROM,
                    smtp_server=EMAIL_SMTP_SERVER,
                    smtp_port=EMAIL_SMTP_PORT,
                    username=EMAIL_USERNAME,
                    password=EMAIL_PASSWORD,
                    attachments=attachments,
                    use_tls=True,
                    html_content=html_content
                )
                
                logger.info(f"Weekly report delivered via email to {', '.join(EMAIL_TO)}")
            
            logger.info(f"Weekly report generated successfully: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {str(e)}")
            return None

    def run_scheduled_reports(self):
        """Run scheduled reports based on configuration."""
        # Schedule daily report at 7:00 AM
        if DAILY_REPORT_ENABLED:
            schedule.every().day.at("07:00").do(self.generate_daily_report)
            logger.info("Daily reports scheduled for 7:00 AM")
        
        # Schedule weekly report on Mondays at 9:00 AM
        if WEEKLY_PREVIEW_ENABLED:
            schedule.every().monday.at("09:00").do(self.generate_weekly_report)
            logger.info("Weekly reports scheduled for Mondays at 9:00 AM")
        
        logger.info("Starting scheduled report generation...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

def main():
    """Main entry point for the automated reports script."""
    parser = argparse.ArgumentParser(description='Generate automated fantasy baseball reports')
    parser.add_argument('--daily', action='store_true', help='Generate daily report')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly report')
    parser.add_argument('--schedule', action='store_true', help='Run scheduled reports')
    parser.add_argument('--league_id', type=int, help='ESPN league ID')
    parser.add_argument('--team_id', type=int, help='Your team ID')
    parser.add_argument('--email', action='store_true', help='Send email notifications')
    
    args = parser.parse_args()
    
    # Override settings if command line args provided
    league_id = args.league_id if args.league_id else LEAGUE_ID
    team_id = args.team_id if args.team_id else TEAM_ID
    
    # Enable email if requested
    if args.email:
        global EMAIL_ENABLED
        EMAIL_ENABLED = True
    
    # Create report generator
    report_generator = AutomatedReportGenerator(league_id=league_id, team_id=team_id)
    
    # Generate reports based on args
    if args.daily:
        report_generator.generate_daily_report()
    
    if args.weekly:
        report_generator.generate_weekly_report()
    
    if args.schedule:
        report_generator.run_scheduled_reports()
    
    # If no args provided, show help
    if not (args.daily or args.weekly or args.schedule):
        parser.print_help()

if __name__ == "__main__":
    main()