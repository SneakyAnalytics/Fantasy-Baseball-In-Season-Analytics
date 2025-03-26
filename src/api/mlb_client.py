"""
MLB Stats API client for retrieving baseball data.

This module provides a client for the official MLB Stats API, which can be used
to fetch player statistics, team data, schedules, and probable pitchers.

Documentation about this API can be found by analyzing:
https://statsapi.mlb.com/api/v1/
"""

import requests
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class MLBStatsClient:
    """Client for the MLB Stats API."""
    
    BASE_URL = "https://statsapi.mlb.com/api/v1"
    
    def __init__(self, cache_duration: int = 3600):
        """
        Initialize the MLB Stats API client.
        
        Args:
            cache_duration: Cache duration in seconds (default: 1 hour)
        """
        self.cache = {}
        self.cache_duration = cache_duration
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the MLB Stats API.
        
        Args:
            endpoint: API endpoint (starting with /)
            params: Query parameters
            
        Returns:
            Dict: API response as JSON
        """
        # Check cache first
        cache_key = f"{endpoint}:{str(params)}"
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if time.time() - cache_time < self.cache_duration:
                logger.debug(f"Using cached data for {endpoint}")
                return cache_data
        
        # Make the request
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            self.cache[cache_key] = (time.time(), data)
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to MLB API: {e}")
            return {}
    
    def get_schedule(self, date: Optional[datetime] = None, 
                    team_id: Optional[int] = None, 
                    sport_id: int = 1) -> Dict[str, Any]:
        """
        Get MLB schedule for a specific date.
        
        Args:
            date: Date to get schedule for (default: today)
            team_id: MLB team ID to filter by
            sport_id: Sport ID (1 = MLB)
            
        Returns:
            Dict: Schedule data
        """
        if date is None:
            date = datetime.now()
            
        date_str = date.strftime("%Y-%m-%d")
        
        params = {
            "sportId": sport_id,
            "date": date_str
        }
        
        if team_id:
            params["teamId"] = team_id
            
        return self._make_request("/schedule", params)
    
    def get_probable_pitchers(self, date: Optional[datetime] = None, 
                             team_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get probable pitchers for a specific date.
        
        Args:
            date: Date to get probable pitchers for (default: today)
            team_id: MLB team ID to filter by
            
        Returns:
            Dict: Probable pitchers data (game_id -> pitcher data)
        """
        schedule = self.get_schedule(date, team_id)
        
        probable_pitchers = {}
        
        if 'dates' in schedule and schedule['dates']:
            for game in schedule['dates'][0]['games']:
                game_id = game['gamePk']
                
                if 'probablePitchers' in game:
                    home_pitcher = None
                    away_pitcher = None
                    
                    if 'home' in game['probablePitchers']:
                        home_pitcher_id = game['probablePitchers']['home']['id']
                        home_pitcher = self.get_player(home_pitcher_id)
                    
                    if 'away' in game['probablePitchers']:
                        away_pitcher_id = game['probablePitchers']['away']['id']
                        away_pitcher = self.get_player(away_pitcher_id)
                    
                    # Add home and away team info
                    home_team = game['teams']['home']['team']['name']
                    away_team = game['teams']['away']['team']['name']
                    
                    probable_pitchers[game_id] = {
                        'game_id': game_id,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_pitcher': home_pitcher,
                        'away_pitcher': away_pitcher
                    }
        
        return probable_pitchers
    
    def get_player(self, player_id: int) -> Dict[str, Any]:
        """
        Get player data by ID.
        
        Args:
            player_id: MLB player ID
            
        Returns:
            Dict: Player data
        """
        return self._make_request(f"/people/{player_id}")
    
    def get_player_stats(self, player_id: int, stats_type: str = "season", 
                        season: Optional[int] = None, group: str = "pitching") -> Dict[str, Any]:
        """
        Get player statistics.
        
        Args:
            player_id: MLB player ID
            stats_type: Type of stats (season, career, etc.)
            season: Season year (default: current year)
            group: Stat group (pitching, hitting, fielding)
            
        Returns:
            Dict: Player statistics
        """
        if season is None:
            season = datetime.now().year
            
        params = {
            "stats": stats_type,
            "season": season,
            "group": group
        }
        
        return self._make_request(f"/people/{player_id}/stats", params)
    
    def get_team_stats(self, team_id: int, stats_type: str = "season", 
                      season: Optional[int] = None, group: str = "hitting") -> Dict[str, Any]:
        """
        Get team statistics.
        
        Args:
            team_id: MLB team ID
            stats_type: Type of stats (season, career, etc.)
            season: Season year (default: current year)
            group: Stat group (pitching, hitting, fielding)
            
        Returns:
            Dict: Team statistics
        """
        if season is None:
            season = datetime.now().year
            
        params = {
            "stats": stats_type,
            "season": season,
            "group": group
        }
        
        return self._make_request(f"/teams/{team_id}/stats", params)
    
    def get_ballpark_factors(self) -> Dict[str, float]:
        """
        Get ballpark factors for all MLB ballparks.
        Note: The MLB API doesn't directly provide this, so we use hard-coded values
        based on recent data. In a production system, this might be pulled from
        another source or updated regularly.
        
        Returns:
            Dict: Ballpark factors (park name -> factor)
        """
        # These are placeholder values and would be updated with actual data
        # in a production system
        return {
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
            "Guaranteed Rate Field": 1.10,
            "Great American Ball Park": 1.11,
            "American Family Field": 1.05,
            "Busch Stadium": 0.98,
            "PNC Park": 0.91,
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
    
    def get_team_ratings(self) -> Dict[str, Dict[str, float]]:
        """
        Get offensive/defensive ratings for all MLB teams.
        Note: These ratings would ideally be calculated from actual MLB API data
        but for simplicity, we use hard-coded values. In a production system,
        these would be calculated from team stats.
        
        Returns:
            Dict: Team ratings (team abbrev -> ratings)
        """
        # These are placeholder values and would be calculated dynamically
        # in a production system
        return {
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
    
    def get_probable_starters_for_next_week(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get probable starting pitchers for the next 7 days.
        
        Returns:
            Dict: Probable starters by MLB team abbreviation
        """
        starters_by_team = {}
        
        # Get schedule for next 7 days
        today = datetime.now()
        
        for day_offset in range(7):
            date = today + timedelta(days=day_offset)
            probables = self.get_probable_pitchers(date)
            
            for game_id, game_data in probables.items():
                # Home team info
                home_team = game_data['home_team']
                home_abbrev = self._get_team_abbreviation(home_team)
                
                if home_abbrev not in starters_by_team:
                    starters_by_team[home_abbrev] = []
                
                if game_data['home_pitcher']:
                    home_pitcher = game_data['home_pitcher']['people'][0] if 'people' in game_data['home_pitcher'] else {}
                    
                    if home_pitcher:
                        starters_by_team[home_abbrev].append({
                            'name': home_pitcher.get('fullName', 'Unknown'),
                            'id': home_pitcher.get('id', 0),
                            'date': date.strftime('%Y-%m-%d'),
                            'opponent': game_data['away_team'],
                            'opponent_abbrev': self._get_team_abbreviation(game_data['away_team']),
                            'home_game': True
                        })
                
                # Away team info
                away_team = game_data['away_team']
                away_abbrev = self._get_team_abbreviation(away_team)
                
                if away_abbrev not in starters_by_team:
                    starters_by_team[away_abbrev] = []
                
                if game_data['away_pitcher']:
                    away_pitcher = game_data['away_pitcher']['people'][0] if 'people' in game_data['away_pitcher'] else {}
                    
                    if away_pitcher:
                        starters_by_team[away_abbrev].append({
                            'name': away_pitcher.get('fullName', 'Unknown'),
                            'id': away_pitcher.get('id', 0),
                            'date': date.strftime('%Y-%m-%d'),
                            'opponent': game_data['home_team'],
                            'opponent_abbrev': self._get_team_abbreviation(game_data['home_team']),
                            'home_game': False
                        })
        
        return starters_by_team
    
    def _get_team_abbreviation(self, team_name: str) -> str:
        """
        Convert full team name to abbreviation.
        
        Args:
            team_name: Full team name
            
        Returns:
            str: Team abbreviation
        """
        # This is a simple mapping and could be more comprehensive
        team_mapping = {
            "New York Yankees": "NYY",
            "Boston Red Sox": "BOS",
            "Tampa Bay Rays": "TB",
            "Baltimore Orioles": "BAL",
            "Toronto Blue Jays": "TOR",
            "Los Angeles Dodgers": "LAD",
            "San Francisco Giants": "SF",
            "San Diego Padres": "SD",
            "Arizona Diamondbacks": "ARI",
            "Colorado Rockies": "COL",
            "Atlanta Braves": "ATL",
            "New York Mets": "NYM",
            "Philadelphia Phillies": "PHI",
            "Washington Nationals": "WSH",
            "Miami Marlins": "MIA",
            "Chicago Cubs": "CHC",
            "Cincinnati Reds": "CIN",
            "Milwaukee Brewers": "MIL",
            "Pittsburgh Pirates": "PIT",
            "St. Louis Cardinals": "STL",
            "Houston Astros": "HOU",
            "Texas Rangers": "TEX",
            "Los Angeles Angels": "LAA",
            "Oakland Athletics": "OAK",
            "Seattle Mariners": "SEA",
            "Cleveland Guardians": "CLE",
            "Detroit Tigers": "DET",
            "Kansas City Royals": "KC",
            "Minnesota Twins": "MIN",
            "Chicago White Sox": "CWS"
        }
        
        return team_mapping.get(team_name, "UNK")