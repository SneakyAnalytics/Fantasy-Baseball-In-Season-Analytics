# src/analysis/schedule_analysis.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

# Try to import the MLB client if available
try:
    from src.api.mlb_client import MLBStatsClient
    HAS_MLB_API = True
except ImportError:
    HAS_MLB_API = False

logger = logging.getLogger(__name__)

class ScheduleAnalyzer:
    """Analyze MLB schedule to find advantageous matchups."""
    
    def __init__(self):
        """Initialize the schedule analyzer."""
        # Initialize the MLB API client if available
        self.mlb_client = MLBStatsClient() if HAS_MLB_API else None
        
        # Cache for team data
        self._team_offensive_ratings = None
        self._team_pitching_ratings = None
        self._ballpark_factors = None
        
    def get_team_offensive_ratings(self) -> Dict[str, Dict[str, float]]:
        """
        Get offensive ratings for all MLB teams.
        
        Returns:
            Dict: Team offensive ratings by team abbreviation
        """
        if self._team_offensive_ratings is not None:
            return self._team_offensive_ratings
        
        if self.mlb_client:
            try:
                # Try to get from MLB client
                self._team_offensive_ratings = self.mlb_client.get_team_ratings()
                return self._team_offensive_ratings
            except Exception as e:
                logger.error(f"Error getting team ratings from MLB API: {e}")
        
        # Fallback to hardcoded values if no MLB client or error
        self._team_offensive_ratings = {
            "NYY": {"offensive": 112, "strikeout_rate": 22.5, "walk_rate": 9.8},
            "BOS": {"offensive": 108, "strikeout_rate": 21.0, "walk_rate": 8.5},
            "TB": {"offensive": 103, "strikeout_rate": 24.2, "walk_rate": 8.9},
            "BAL": {"offensive": 96, "strikeout_rate": 23.8, "walk_rate": 7.5},
            "TOR": {"offensive": 105, "strikeout_rate": 20.5, "walk_rate": 8.2},
            "LAD": {"offensive": 115, "strikeout_rate": 20.8, "walk_rate": 10.3},
            "SF": {"offensive": 101, "strikeout_rate": 23.1, "walk_rate": 9.5},
            "SD": {"offensive": 103, "strikeout_rate": 22.7, "walk_rate": 8.8},
            "ARI": {"offensive": 100, "strikeout_rate": 22.3, "walk_rate": 8.2},
            "COL": {"offensive": 95, "strikeout_rate": 24.5, "walk_rate": 7.3},
            "ATL": {"offensive": 110, "strikeout_rate": 23.1, "walk_rate": 8.7},
            "NYM": {"offensive": 102, "strikeout_rate": 21.9, "walk_rate": 8.4},
            "PHI": {"offensive": 106, "strikeout_rate": 22.7, "walk_rate": 8.9},
            "WSH": {"offensive": 94, "strikeout_rate": 20.8, "walk_rate": 7.6},
            "MIA": {"offensive": 90, "strikeout_rate": 25.3, "walk_rate": 7.1},
            "CHC": {"offensive": 98, "strikeout_rate": 24.1, "walk_rate": 8.3},
            "CIN": {"offensive": 101, "strikeout_rate": 23.5, "walk_rate": 8.5},
            "MIL": {"offensive": 100, "strikeout_rate": 23.8, "walk_rate": 9.1},
            "PIT": {"offensive": 92, "strikeout_rate": 24.2, "walk_rate": 7.5},
            "STL": {"offensive": 102, "strikeout_rate": 19.8, "walk_rate": 8.7},
            "HOU": {"offensive": 108, "strikeout_rate": 19.5, "walk_rate": 9.3},
            "TEX": {"offensive": 105, "strikeout_rate": 23.1, "walk_rate": 8.2},
            "LAA": {"offensive": 100, "strikeout_rate": 24.7, "walk_rate": 7.9},
            "OAK": {"offensive": 88, "strikeout_rate": 24.9, "walk_rate": 7.3},
            "SEA": {"offensive": 97, "strikeout_rate": 25.6, "walk_rate": 8.8},
            "CLE": {"offensive": 99, "strikeout_rate": 21.2, "walk_rate": 7.9},
            "DET": {"offensive": 93, "strikeout_rate": 23.8, "walk_rate": 7.3},
            "KC": {"offensive": 95, "strikeout_rate": 22.1, "walk_rate": 7.1},
            "MIN": {"offensive": 102, "strikeout_rate": 22.9, "walk_rate": 8.7},
            "CWS": {"offensive": 97, "strikeout_rate": 23.5, "walk_rate": 7.6}
        }
        
        return self._team_offensive_ratings
    
    def get_team_pitching_ratings(self) -> Dict[str, Dict[str, float]]:
        """
        Get pitching ratings for all MLB teams.
        
        Returns:
            Dict: Team pitching ratings by team abbreviation
        """
        if self._team_pitching_ratings is not None:
            return self._team_pitching_ratings
        
        # In a full implementation, we'd get these from the MLB API
        # For now, use placeholder data
        self._team_pitching_ratings = {
            "NYY": {"pitching": 105, "strikeout_rate": 24.5, "walk_rate": 7.8, "home_run_rate": 3.2},
            "BOS": {"pitching": 98, "strikeout_rate": 22.0, "walk_rate": 8.5, "home_run_rate": 3.5},
            "TB": {"pitching": 108, "strikeout_rate": 25.2, "walk_rate": 7.9, "home_run_rate": 2.9},
            "BAL": {"pitching": 102, "strikeout_rate": 23.8, "walk_rate": 7.5, "home_run_rate": 3.3},
            "TOR": {"pitching": 100, "strikeout_rate": 21.5, "walk_rate": 8.2, "home_run_rate": 3.4},
            "LAD": {"pitching": 112, "strikeout_rate": 26.8, "walk_rate": 7.3, "home_run_rate": 2.7},
            "SF": {"pitching": 106, "strikeout_rate": 24.1, "walk_rate": 7.5, "home_run_rate": 2.9},
            "SD": {"pitching": 107, "strikeout_rate": 25.7, "walk_rate": 7.8, "home_run_rate": 2.8},
            "ARI": {"pitching": 101, "strikeout_rate": 22.3, "walk_rate": 8.2, "home_run_rate": 3.1},
            "COL": {"pitching": 90, "strikeout_rate": 20.5, "walk_rate": 8.3, "home_run_rate": 3.9},
            "ATL": {"pitching": 110, "strikeout_rate": 26.1, "walk_rate": 7.7, "home_run_rate": 2.7},
            "NYM": {"pitching": 107, "strikeout_rate": 24.9, "walk_rate": 7.4, "home_run_rate": 2.9},
            "PHI": {"pitching": 103, "strikeout_rate": 23.7, "walk_rate": 7.9, "home_run_rate": 3.1},
            "WSH": {"pitching": 94, "strikeout_rate": 20.8, "walk_rate": 8.6, "home_run_rate": 3.6},
            "MIA": {"pitching": 105, "strikeout_rate": 25.3, "walk_rate": 8.1, "home_run_rate": 2.8},
            "CHC": {"pitching": 99, "strikeout_rate": 23.1, "walk_rate": 8.3, "home_run_rate": 3.3},
            "CIN": {"pitching": 97, "strikeout_rate": 22.5, "walk_rate": 8.5, "home_run_rate": 3.7},
            "MIL": {"pitching": 104, "strikeout_rate": 24.8, "walk_rate": 7.6, "home_run_rate": 3.1},
            "PIT": {"pitching": 96, "strikeout_rate": 21.2, "walk_rate": 8.5, "home_run_rate": 3.4},
            "STL": {"pitching": 102, "strikeout_rate": 22.8, "walk_rate": 7.7, "home_run_rate": 3.2},
            "HOU": {"pitching": 109, "strikeout_rate": 25.5, "walk_rate": 7.3, "home_run_rate": 2.9},
            "TEX": {"pitching": 104, "strikeout_rate": 23.1, "walk_rate": 7.9, "home_run_rate": 3.2},
            "LAA": {"pitching": 95, "strikeout_rate": 21.7, "walk_rate": 8.5, "home_run_rate": 3.5},
            "OAK": {"pitching": 97, "strikeout_rate": 22.9, "walk_rate": 8.3, "home_run_rate": 3.2},
            "SEA": {"pitching": 106, "strikeout_rate": 25.6, "walk_rate": 7.8, "home_run_rate": 2.9},
            "CLE": {"pitching": 105, "strikeout_rate": 24.2, "walk_rate": 7.6, "home_run_rate": 3.0},
            "DET": {"pitching": 102, "strikeout_rate": 23.8, "walk_rate": 8.3, "home_run_rate": 3.1},
            "KC": {"pitching": 98, "strikeout_rate": 22.1, "walk_rate": 8.1, "home_run_rate": 3.3},
            "MIN": {"pitching": 103, "strikeout_rate": 24.5, "walk_rate": 7.7, "home_run_rate": 3.1},
            "CWS": {"pitching": 99, "strikeout_rate": 23.5, "walk_rate": 8.0, "home_run_rate": 3.4}
        }
        
        return self._team_pitching_ratings
    
    def get_ballpark_factors(self) -> Dict[str, float]:
        """
        Get ballpark factors for all MLB ballparks.
        
        Returns:
            Dict: Ballpark factors by ballpark name
        """
        if self._ballpark_factors is not None:
            return self._ballpark_factors
        
        if self.mlb_client:
            try:
                # Try to get from MLB client
                self._ballpark_factors = self.mlb_client.get_ballpark_factors()
                return self._ballpark_factors
            except Exception as e:
                logger.error(f"Error getting ballpark factors from MLB API: {e}")
        
        # Fallback to hardcoded values if no MLB client or error
        self._ballpark_factors = {
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
            "Wrigley Field": 1.04,
            "Great American Ball Park": 1.11,
            "American Family Field": 1.05,
            "PNC Park": 0.91,
            "Busch Stadium": 0.98,
            "Minute Maid Park": 1.08,
            "Globe Life Field": 0.97,
            "Angel Stadium": 0.97,
            "Oakland Coliseum": 0.93,
            "T-Mobile Park": 0.94,
            "Progressive Field": 0.98,
            "Comerica Park": 0.95,
            "Kauffman Stadium": 0.98,
            "Target Field": 1.00
        }
        
        return self._ballpark_factors
    
    def get_team_schedule(self, team_abbr: str, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """
        Get the upcoming schedule for a specific MLB team.
        
        Args:
            team_abbr: Team abbreviation
            days_ahead: Number of days to look ahead
            
        Returns:
            List: Schedule data for the team
        """
        if not self.mlb_client:
            logger.warning("MLB API client not available, returning placeholder data")
            return self._get_placeholder_schedule(team_abbr, days_ahead)
        
        try:
            # Get schedule for the next N days
            schedule = []
            start_date = datetime.now()
            
            for day in range(days_ahead):
                date = start_date + timedelta(days=day)
                daily_schedule = self.mlb_client.get_schedule(date=date)
                
                # Extract games for the specified team
                if 'dates' in daily_schedule and daily_schedule['dates']:
                    for game in daily_schedule['dates'][0]['games']:
                        home_team = game['teams']['home']['team']['name']
                        away_team = game['teams']['away']['team']['name']
                        
                        # Convert team names to abbreviations
                        home_abbr = self.mlb_client._get_team_abbreviation(home_team)
                        away_abbr = self.mlb_client._get_team_abbreviation(away_team)
                        
                        # Check if this game involves the requested team
                        if home_abbr == team_abbr or away_abbr == team_abbr:
                            # Format game data
                            game_data = {
                                'date': date.strftime('%Y-%m-%d'),
                                'home_team': home_abbr,
                                'away_team': away_abbr,
                                'ballpark': self._get_ballpark_by_team(home_abbr),
                                'is_home': home_abbr == team_abbr
                            }
                            
                            schedule.append(game_data)
            
            return schedule
            
        except Exception as e:
            logger.error(f"Error getting schedule from MLB API: {e}")
            return self._get_placeholder_schedule(team_abbr, days_ahead)
    
    def _get_placeholder_schedule(self, team_abbr: str, days_ahead: int) -> List[Dict[str, Any]]:
        """
        Generate placeholder schedule for a team if MLB API is unavailable.
        
        Args:
            team_abbr: Team abbreviation
            days_ahead: Number of days to look ahead
            
        Returns:
            List: Placeholder schedule data
        """
        import random
        
        # Get all team abbreviations
        all_teams = list(self.get_team_offensive_ratings().keys())
        all_teams.remove(team_abbr)  # Remove the team itself
        
        schedule = []
        start_date = datetime.now()
        
        for day in range(days_ahead):
            # Skip some days randomly to simulate off days
            if random.random() < 0.2:  # 20% chance of an off day
                continue
                
            date = start_date + timedelta(days=day)
            
            # Randomly select an opponent
            opponent = random.choice(all_teams)
            
            # Randomly determine home/away (with slight bias toward home)
            is_home = random.random() < 0.55  # 55% chance of home game
            
            game_data = {
                'date': date.strftime('%Y-%m-%d'),
                'home_team': team_abbr if is_home else opponent,
                'away_team': opponent if is_home else team_abbr,
                'ballpark': self._get_ballpark_by_team(team_abbr if is_home else opponent),
                'is_home': is_home
            }
            
            schedule.append(game_data)
        
        return schedule
    
    def _get_ballpark_by_team(self, team_abbr: str) -> str:
        """
        Get the ballpark name for a team's home games.
        
        Args:
            team_abbr: Team abbreviation
            
        Returns:
            str: Ballpark name
        """
        # Map team abbreviations to ballpark names
        team_ballparks = {
            "NYY": "Yankee Stadium",
            "BOS": "Fenway Park",
            "TB": "Tropicana Field",
            "BAL": "Camden Yards",
            "TOR": "Rogers Centre",
            "LAD": "Dodger Stadium",
            "SF": "Oracle Park",
            "SD": "Petco Park",
            "ARI": "Chase Field",
            "COL": "Coors Field",
            "ATL": "Truist Park",
            "NYM": "Citi Field",
            "PHI": "Citizens Bank Park",
            "WSH": "Nationals Park",
            "MIA": "LoanDepot Park",
            "CHC": "Wrigley Field",
            "CIN": "Great American Ball Park",
            "MIL": "American Family Field",
            "PIT": "PNC Park",
            "STL": "Busch Stadium",
            "HOU": "Minute Maid Park",
            "TEX": "Globe Life Field",
            "LAA": "Angel Stadium",
            "OAK": "Oakland Coliseum",
            "SEA": "T-Mobile Park",
            "CLE": "Progressive Field",
            "DET": "Comerica Park",
            "KC": "Kauffman Stadium",
            "MIN": "Target Field",
            "CWS": "Guaranteed Rate Field"
        }
        
        return team_ballparks.get(team_abbr, "Unknown Ballpark")
    
    def analyze_matchup_quality(self, team_abbr: str, is_offense: bool, opponent_abbr: str, 
                               ballpark: str) -> Dict[str, Any]:
        """
        Analyze the quality of a matchup for a team.
        
        Args:
            team_abbr: Team abbreviation
            is_offense: True if analyzing for offense, False for pitching
            opponent_abbr: Opponent team abbreviation
            ballpark: Ballpark name
            
        Returns:
            Dict: Matchup quality analysis
        """
        # Get team ratings
        offensive_ratings = self.get_team_offensive_ratings()
        pitching_ratings = self.get_team_pitching_ratings()
        ballpark_factors = self.get_ballpark_factors()
        
        # Get specific ratings
        team_offense = offensive_ratings.get(team_abbr, {}).get("offensive", 100)
        team_pitching = pitching_ratings.get(team_abbr, {}).get("pitching", 100)
        opponent_offense = offensive_ratings.get(opponent_abbr, {}).get("offensive", 100)
        opponent_pitching = pitching_ratings.get(opponent_abbr, {}).get("pitching", 100)
        
        # Get ballpark factor
        park_factor = ballpark_factors.get(ballpark, 1.0)
        
        # Calculate matchup quality
        if is_offense:
            # For offense, we want weak opponent pitching and favorable ballpark
            base_score = 100 * (1 / (opponent_pitching / 100)) * park_factor
            
            # Additional factors
            opponent_k_rate = pitching_ratings.get(opponent_abbr, {}).get("strikeout_rate", 22.0)
            matchup_rating = base_score * (1 / (opponent_k_rate / 22.0))
            
            # Determine quality level
            if matchup_rating > 120:
                quality = "Excellent"
                recommendation = "Start all hitters"
            elif matchup_rating > 110:
                quality = "Good"
                recommendation = "Start most hitters"
            elif matchup_rating > 100:
                quality = "Favorable"
                recommendation = "Start regular hitters"
            elif matchup_rating > 90:
                quality = "Average"
                recommendation = "Start your studs"
            else:
                quality = "Tough"
                recommendation = "Consider benching borderline hitters"
            
            return {
                "matchup_rating": matchup_rating,
                "quality": quality,
                "recommendation": recommendation,
                "team_offense": team_offense,
                "opponent_pitching": opponent_pitching,
                "opponent_k_rate": opponent_k_rate,
                "ballpark_factor": park_factor,
                "is_offense": is_offense
            }
        else:
            # For pitching, we want weak opponent offense and favorable ballpark
            base_score = 100 * (1 / (opponent_offense / 100)) * (1 / park_factor)
            
            # Additional factors
            opponent_k_rate = offensive_ratings.get(opponent_abbr, {}).get("strikeout_rate", 22.0)
            matchup_rating = base_score * (opponent_k_rate / 22.0)
            
            # Determine quality level
            if matchup_rating > 120:
                quality = "Excellent"
                recommendation = "Stream pitchers against this team"
            elif matchup_rating > 110:
                quality = "Good"
                recommendation = "Good streaming opportunity"
            elif matchup_rating > 100:
                quality = "Favorable"
                recommendation = "Start your regular pitchers"
            elif matchup_rating > 90:
                quality = "Average"
                recommendation = "Start your studs"
            else:
                quality = "Tough"
                recommendation = "Consider benching borderline pitchers"
            
            return {
                "matchup_rating": matchup_rating,
                "quality": quality,
                "recommendation": recommendation,
                "team_pitching": team_pitching,
                "opponent_offense": opponent_offense,
                "opponent_k_rate": opponent_k_rate,
                "ballpark_factor": park_factor,
                "is_offense": is_offense
            }
    
    def analyze_team_schedule(self, team_abbr: str, days_ahead: int = 14) -> Dict[str, Any]:
        """
        Analyze the upcoming schedule for a team.
        
        Args:
            team_abbr: Team abbreviation
            days_ahead: Number of days to look ahead
            
        Returns:
            Dict: Schedule analysis results
        """
        # Get team schedule
        schedule = self.get_team_schedule(team_abbr, days_ahead)
        
        # Analyze each matchup
        games = []
        offensive_advantage = 0
        pitching_advantage = 0
        
        for game in schedule:
            game_date = game['date']
            opponent = game['away_team'] if game['is_home'] else game['home_team']
            ballpark = game['ballpark']
            
            # Analyze for both offense and pitching
            offense_analysis = self.analyze_matchup_quality(team_abbr, True, opponent, ballpark)
            pitching_analysis = self.analyze_matchup_quality(team_abbr, False, opponent, ballpark)
            
            # Add to running totals
            offensive_advantage += offense_analysis['matchup_rating'] - 100
            pitching_advantage += pitching_analysis['matchup_rating'] - 100
            
            # Add to games list
            games.append({
                'date': game_date,
                'opponent': opponent,
                'ballpark': ballpark,
                'is_home': game['is_home'],
                'offense_quality': offense_analysis['quality'],
                'offense_rating': offense_analysis['matchup_rating'],
                'pitching_quality': pitching_analysis['quality'],
                'pitching_rating': pitching_analysis['matchup_rating']
            })
        
        # Calculate schedule advantage
        num_games = len(games)
        if num_games > 0:
            offensive_schedule_advantage = offensive_advantage / num_games
            pitching_schedule_advantage = pitching_advantage / num_games
            overall_schedule_advantage = (offensive_schedule_advantage + pitching_schedule_advantage) / 2
        else:
            offensive_schedule_advantage = 0
            pitching_schedule_advantage = 0
            overall_schedule_advantage = 0
        
        # Determine schedule quality
        if overall_schedule_advantage > 10:
            schedule_quality = "Excellent"
        elif overall_schedule_advantage > 5:
            schedule_quality = "Good"
        elif overall_schedule_advantage > 0:
            schedule_quality = "Favorable"
        elif overall_schedule_advantage > -5:
            schedule_quality = "Average"
        else:
            schedule_quality = "Tough"
        
        return {
            'team': team_abbr,
            'games': games,
            'offensive_schedule_advantage': offensive_schedule_advantage,
            'pitching_schedule_advantage': pitching_schedule_advantage,
            'overall_schedule_advantage': overall_schedule_advantage,
            'schedule_quality': schedule_quality,
            'days_analyzed': days_ahead,
            'analysis_date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def find_streaming_opportunities(self, days_ahead: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find good streaming opportunities for the next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            Dict: Daily streaming opportunities
        """
        # Get all team abbreviations
        teams = list(self.get_team_offensive_ratings().keys())
        
        # Store opportunities by date
        opportunities_by_date = {}
        
        # Current date
        start_date = datetime.now()
        
        for day in range(days_ahead):
            date = start_date + timedelta(days=day)
            date_str = date.strftime('%Y-%m-%d')
            
            # List to store this day's opportunities
            daily_opportunities = []
            
            # For each team, check if they have a favorable pitching matchup on this day
            for team in teams:
                # Get team's schedule
                schedule = self.get_team_schedule(team, days_ahead=1)
                
                # Look for a game on this specific date
                for game in schedule:
                    if game['date'] == date_str:
                        opponent = game['away_team'] if game['is_home'] else game['home_team']
                        ballpark = game['ballpark']
                        
                        # Analyze pitching matchup
                        pitching_analysis = self.analyze_matchup_quality(team, False, opponent, ballpark)
                        
                        # If it's a good opportunity, add it to the list
                        if pitching_analysis['matchup_rating'] > 105:
                            opportunity = {
                                'team': team,
                                'opponent': opponent,
                                'ballpark': ballpark,
                                'is_home': game['is_home'],
                                'rating': pitching_analysis['matchup_rating'],
                                'quality': pitching_analysis['quality'],
                                'recommendation': pitching_analysis['recommendation']
                            }
                            daily_opportunities.append(opportunity)
            
            # Sort opportunities by rating
            daily_opportunities.sort(key=lambda x: x['rating'], reverse=True)
            
            # Store in the dictionary
            opportunities_by_date[date_str] = daily_opportunities
        
        return opportunities_by_date
    
    def find_hitter_streaming_opportunities(self, days_ahead: int = 7) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find good hitting matchups for the next N days.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            Dict: Daily hitting matchup opportunities
        """
        # Get all team abbreviations
        teams = list(self.get_team_offensive_ratings().keys())
        
        # Store opportunities by date
        opportunities_by_date = {}
        
        # Current date
        start_date = datetime.now()
        
        for day in range(days_ahead):
            date = start_date + timedelta(days=day)
            date_str = date.strftime('%Y-%m-%d')
            
            # List to store this day's opportunities
            daily_opportunities = []
            
            # For each team, check if they have a favorable offensive matchup on this day
            for team in teams:
                # Get team's schedule
                schedule = self.get_team_schedule(team, days_ahead=1)
                
                # Look for a game on this specific date
                for game in schedule:
                    if game['date'] == date_str:
                        opponent = game['away_team'] if game['is_home'] else game['home_team']
                        ballpark = game['ballpark']
                        
                        # Analyze offensive matchup
                        offense_analysis = self.analyze_matchup_quality(team, True, opponent, ballpark)
                        
                        # If it's a good opportunity, add it to the list
                        if offense_analysis['matchup_rating'] > 105:
                            opportunity = {
                                'team': team,
                                'opponent': opponent,
                                'ballpark': ballpark,
                                'is_home': game['is_home'],
                                'rating': offense_analysis['matchup_rating'],
                                'quality': offense_analysis['quality'],
                                'recommendation': offense_analysis['recommendation']
                            }
                            daily_opportunities.append(opportunity)
            
            # Sort opportunities by rating
            daily_opportunities.sort(key=lambda x: x['rating'], reverse=True)
            
            # Store in the dictionary
            opportunities_by_date[date_str] = daily_opportunities
        
        return opportunities_by_date