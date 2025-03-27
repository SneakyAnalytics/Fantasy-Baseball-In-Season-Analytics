# src/analysis/category_analysis.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging

from src.data.models import Team, Player
from src.data.processors import PlayerDataProcessor

logger = logging.getLogger(__name__)

class CategoryAnalyzer:
    """Analyze team strengths and weaknesses by scoring category."""
    
    def __init__(self, teams: Optional[List[Team]] = None):
        """
        Initialize with a list of teams.
        
        Args:
            teams: List of teams in the league
        """
        self.teams = teams
        self.team_dfs = {}
        self.league_stats = {}
        self.categories = {}
        
        if teams:
            self._process_teams()
    
    def set_teams(self, teams: List[Team]):
        """
        Set or update the list of teams.
        
        Args:
            teams: List of teams in the league
        """
        self.teams = teams
        self._process_teams()
    
    def _process_teams(self):
        """Process teams into DataFrames and calculate league stats."""
        self.team_dfs = {}
        
        # Process each team's roster
        for team in self.teams:
            if team.roster:
                self.team_dfs[team.team_id] = PlayerDataProcessor.players_to_dataframe(team.roster)
        
        # Identify available stat categories
        self._identify_categories()
        
        # Calculate league-wide stats
        self._calculate_league_stats()
    
    def _identify_categories(self):
        """Identify available stat categories from team rosters."""
        self.categories = {
            'batting': {},
            'pitching': {}
        }
        
        # Check first team for available categories
        if not self.teams or not self.team_dfs:
            return
        
        first_team_df = list(self.team_dfs.values())[0]
        
        # Look for typical batting categories
        batting_cats = [
            ('AVG', ['avg', 'batting_avg', 'ba']),
            ('HR', ['hr', 'home_runs', 'hrs']),
            ('R', ['r', 'runs', 'run']),
            ('RBI', ['rbi', 'rbis', 'runs_batted_in']),
            ('SB', ['sb', 'stolen_bases', 'steals']),
            ('OBP', ['obp', 'on_base_pct', 'on_base_percentage']),
            ('SLG', ['slg', 'slugging', 'slugging_pct']),
            ('OPS', ['ops', 'on_base_plus_slugging']),
            ('TB', ['tb', 'total_bases']),
            ('H', ['h', 'hits', 'hit']),
            ('2B', ['2b', 'doubles', 'double']),
            ('3B', ['3b', 'triples', 'triple']),
            ('BB', ['bb', 'walks', 'walk']),
            ('XBH', ['xbh', 'extra_base_hits']),
            ('PA', ['pa', 'plate_appearances']),
            ('AB', ['ab', 'at_bats']),
        ]
        
        # Look for typical pitching categories
        pitching_cats = [
            ('ERA', ['era', 'earned_run_avg', 'earned_run_average']),
            ('WHIP', ['whip', 'walks_hits_per_ip']),
            ('W', ['w', 'wins', 'win']),
            ('SV', ['sv', 'saves', 'save']),
            ('K', ['k', 'so', 'strikeouts', 'strikeout']),
            ('HLD', ['hld', 'holds', 'hold']),
            ('QS', ['qs', 'quality_starts']),
            ('IP', ['ip', 'innings_pitched']),
            ('K/9', ['k/9', 'k_per_9', 'strikeouts_per_9']),
            ('BB/9', ['bb/9', 'bb_per_9', 'walks_per_9']),
            ('K/BB', ['k/bb', 'k_per_bb', 'strikeout_to_walk']),
            ('SVH', ['svh', 'saves_plus_holds'])
        ]
        
        # Find batting categories in the DataFrame
        for cat_name, aliases in batting_cats:
            # Search all columns with any of the aliases
            for alias in aliases:
                matching_cols = [col for col in first_team_df.columns if alias in col.lower()]
                if matching_cols:
                    self.categories['batting'][cat_name] = matching_cols[0]
                    break
        
        # Find pitching categories in the DataFrame
        for cat_name, aliases in pitching_cats:
            # Search all columns with any of the aliases
            for alias in aliases:
                matching_cols = [col for col in first_team_df.columns if alias in col.lower()]
                if matching_cols:
                    self.categories['pitching'][cat_name] = matching_cols[0]
                    break
        
        logger.info(f"Identified categories - Batting: {list(self.categories['batting'].keys())}, "
                   f"Pitching: {list(self.categories['pitching'].keys())}")
    
    def _calculate_league_stats(self):
        """Calculate league-wide statistics for each category."""
        if not self.teams or not self.team_dfs or not self.categories:
            return
        
        self.league_stats = {
            'batting': {},
            'pitching': {}
        }
        
        # For each batting category
        for cat_name, col_name in self.categories['batting'].items():
            values = []
            for team_df in self.team_dfs.values():
                if col_name in team_df.columns:
                    # Filter for batters
                    batters = team_df[~team_df['positions'].str.contains('SP|RP', case=False)]
                    if not batters.empty:
                        values.append(batters[col_name].sum())
            
            if values:
                self.league_stats['batting'][cat_name] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
        
        # For each pitching category
        for cat_name, col_name in self.categories['pitching'].items():
            values = []
            for team_df in self.team_dfs.values():
                if col_name in team_df.columns:
                    # Filter for pitchers
                    pitchers = team_df[team_df['positions'].str.contains('SP|RP', case=False)]
                    if not pitchers.empty:
                        # For rate stats (ERA, WHIP), calculate the team aggregate value
                        if cat_name in ['ERA', 'WHIP', 'K/9', 'BB/9', 'K/BB']:
                            # Simple average for demonstration - in reality this would use weights
                            values.append(pitchers[col_name].mean())
                        else:
                            values.append(pitchers[col_name].sum())
            
            if values:
                self.league_stats['pitching'][cat_name] = {
                    'mean': np.mean(values),
                    'median': np.median(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values)
                }
    
    def analyze_team_categories(self, team_id: int) -> Dict[str, Any]:
        """
        Analyze a team's performance in each category.
        
        Args:
            team_id: Team ID to analyze
            
        Returns:
            Dict: Analysis of team's categorical strengths and weaknesses
        """
        if not self.teams or team_id not in self.team_dfs or not self.categories:
            return {"error": "Team data not available"}
        
        team_df = self.team_dfs[team_id]
        
        # Find the team object
        team = next((t for t in self.teams if t.team_id == team_id), None)
        if not team:
            return {"error": "Team not found"}
        
        result = {
            "team_id": team_id,
            "team_name": team.name,
            "categories": {
                "batting": {},
                "pitching": {}
            }
        }
        
        # Analyze batting categories
        for cat_name, col_name in self.categories['batting'].items():
            if col_name in team_df.columns and cat_name in self.league_stats['batting']:
                # Filter for batters
                batters = team_df[~team_df['positions'].str.contains('SP|RP', case=False)]
                
                if not batters.empty:
                    # Get team value
                    team_value = batters[col_name].sum()
                    
                    # Get league stats
                    league_stats = self.league_stats['batting'][cat_name]
                    
                    # Calculate z-score
                    if league_stats['std'] > 0:
                        z_score = (team_value - league_stats['mean']) / league_stats['std']
                    else:
                        z_score = 0
                    
                    # Calculate percentile (rough approximation)
                    percentile = min(max((z_score + 3) / 6, 0), 1) * 100
                    
                    # Determine strength level
                    if percentile >= 80:
                        strength = "Very Strong"
                    elif percentile >= 60:
                        strength = "Strong"
                    elif percentile >= 40:
                        strength = "Average"
                    elif percentile >= 20:
                        strength = "Weak"
                    else:
                        strength = "Very Weak"
                    
                    # Add to result
                    result["categories"]["batting"][cat_name] = {
                        "value": team_value,
                        "league_mean": league_stats['mean'],
                        "league_median": league_stats['median'],
                        "z_score": z_score,
                        "percentile": percentile,
                        "strength": strength
                    }
        
        # Analyze pitching categories
        for cat_name, col_name in self.categories['pitching'].items():
            if col_name in team_df.columns and cat_name in self.league_stats['pitching']:
                # Filter for pitchers
                pitchers = team_df[team_df['positions'].str.contains('SP|RP', case=False)]
                
                if not pitchers.empty:
                    # Get team value (rate vs. counting stats)
                    if cat_name in ['ERA', 'WHIP', 'K/9', 'BB/9', 'K/BB']:
                        team_value = pitchers[col_name].mean()
                    else:
                        team_value = pitchers[col_name].sum()
                    
                    # Get league stats
                    league_stats = self.league_stats['pitching'][cat_name]
                    
                    # Calculate z-score (note: for ERA, WHIP, BB/9 lower is better)
                    if league_stats['std'] > 0:
                        if cat_name in ['ERA', 'WHIP', 'BB/9']:
                            z_score = -1 * (team_value - league_stats['mean']) / league_stats['std']
                        else:
                            z_score = (team_value - league_stats['mean']) / league_stats['std']
                    else:
                        z_score = 0
                    
                    # Calculate percentile (rough approximation)
                    percentile = min(max((z_score + 3) / 6, 0), 1) * 100
                    
                    # Determine strength level
                    if percentile >= 80:
                        strength = "Very Strong"
                    elif percentile >= 60:
                        strength = "Strong"
                    elif percentile >= 40:
                        strength = "Average"
                    elif percentile >= 20:
                        strength = "Weak"
                    else:
                        strength = "Very Weak"
                    
                    # Add to result
                    result["categories"]["pitching"][cat_name] = {
                        "value": team_value,
                        "league_mean": league_stats['mean'],
                        "league_median": league_stats['median'],
                        "z_score": z_score,
                        "percentile": percentile,
                        "strength": strength
                    }
        
        # Identify strength/weakness vectors
        result["strengths"] = self._identify_strengths(result["categories"])
        result["weaknesses"] = self._identify_weaknesses(result["categories"])
        
        return result
    
    def _identify_strengths(self, categories: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, List[str]]:
        """
        Identify categorical strengths from analysis.
        
        Args:
            categories: Analyzed categories
            
        Returns:
            Dict: Strengths by category type
        """
        strengths = {
            "batting": [],
            "pitching": []
        }
        
        # Find batting strengths
        for cat_name, stats in categories.get("batting", {}).items():
            if stats.get("strength") in ["Strong", "Very Strong"]:
                strengths["batting"].append(cat_name)
        
        # Find pitching strengths
        for cat_name, stats in categories.get("pitching", {}).items():
            if stats.get("strength") in ["Strong", "Very Strong"]:
                strengths["pitching"].append(cat_name)
        
        return strengths
    
    def _identify_weaknesses(self, categories: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, List[str]]:
        """
        Identify categorical weaknesses from analysis.
        
        Args:
            categories: Analyzed categories
            
        Returns:
            Dict: Weaknesses by category type
        """
        weaknesses = {
            "batting": [],
            "pitching": []
        }
        
        # Find batting weaknesses
        for cat_name, stats in categories.get("batting", {}).items():
            if stats.get("strength") in ["Weak", "Very Weak"]:
                weaknesses["batting"].append(cat_name)
        
        # Find pitching weaknesses
        for cat_name, stats in categories.get("pitching", {}).items():
            if stats.get("strength") in ["Weak", "Very Weak"]:
                weaknesses["pitching"].append(cat_name)
        
        return weaknesses
    
    def recommend_category_improvements(self, team_id: int, 
                                       free_agents: List[Player] = None) -> Dict[str, Any]:
        """
        Recommend ways to improve a team's weak categories.
        
        Args:
            team_id: Team ID to analyze
            free_agents: List of available free agents (optional)
            
        Returns:
            Dict: Category improvement recommendations
        """
        # First get the team analysis
        team_analysis = self.analyze_team_categories(team_id)
        if "error" in team_analysis:
            return team_analysis
        
        # Initialize recommendations
        recommendations = {
            "team_id": team_id,
            "team_name": team_analysis["team_name"],
            "weaknesses": team_analysis["weaknesses"],
            "improvement_strategies": {
                "batting": {},
                "pitching": {}
            },
            "free_agent_recommendations": {
                "batting": {},
                "pitching": {}
            }
        }
        
        # Generate general improvement strategies for batting weaknesses
        batting_strategies = {
            "AVG": "Target high-contact hitters with good plate discipline",
            "HR": "Add power hitters, even if they have lower batting averages",
            "R": "Target high-OBP players and those hitting at the top of strong lineups",
            "RBI": "Look for sluggers and players hitting in the middle of the order",
            "SB": "Add speedsters and top-of-order hitters, even with less power",
            "OBP": "Prioritize players with good walk rates and plate discipline",
            "SLG": "Focus on power hitters with extra-base hit ability",
            "OPS": "Balance power and on-base skills in your hitting acquisitions",
            "TB": "Target players with extra-base hit power and consistent playing time",
            "H": "Add players with high batting averages and consistent playing time",
            "2B": "Look for gap hitters, especially those in parks with deep outfields",
            "3B": "Rare category; target speedsters in parks with large outfields",
            "BB": "Focus on patient hitters with good plate discipline",
            "XBH": "Add players with gap power and good ballparks for extra-base hits"
        }
        
        # Generate general improvement strategies for pitching weaknesses
        pitching_strategies = {
            "ERA": "Target pitchers with good underlying skills (high K%, low BB%, groundball tendencies)",
            "WHIP": "Prioritize control pitchers with low walk rates",
            "W": "Focus on starters on good teams with high strikeout ability",
            "SV": "Add established closers, especially on winning teams",
            "K": "Target high-strikeout pitchers, even with slightly higher ratios",
            "HLD": "Add setup men on good teams with high strikeout rates",
            "QS": "Look for durable starters who pitch deep into games",
            "IP": "Maximize your innings with efficient starters",
            "K/9": "Focus on high-strikeout pitchers, even in shorter outings",
            "BB/9": "Target control specialists with proven command",
            "K/BB": "Balance strikeout ability with control in your pitching staff",
            "SVH": "Add both closers and high-quality setup men"
        }
        
        # Add strategies for batting weaknesses
        for cat in team_analysis["weaknesses"]["batting"]:
            if cat in batting_strategies:
                recommendations["improvement_strategies"]["batting"][cat] = batting_strategies[cat]
        
        # Add strategies for pitching weaknesses
        for cat in team_analysis["weaknesses"]["pitching"]:
            if cat in pitching_strategies:
                recommendations["improvement_strategies"]["pitching"][cat] = pitching_strategies[cat]
        
        # If free agents are provided, analyze them for category help
        if free_agents:
            fa_df = PlayerDataProcessor.players_to_dataframe(free_agents)
            
            # Recommend batters for weak batting categories
            for cat in team_analysis["weaknesses"]["batting"]:
                if cat in self.categories['batting']:
                    col_name = self.categories['batting'][cat]
                    
                    if col_name in fa_df.columns:
                        # Filter batters
                        fa_batters = fa_df[~fa_df['positions'].str.contains('SP|RP', case=False)]
                        
                        # Get players strong in this category
                        if not fa_batters.empty:
                            # Sort by the category value
                            strong_fas = fa_batters.sort_values(col_name, ascending=False).head(5)
                            
                            # Convert to recommendations
                            recommendations["free_agent_recommendations"]["batting"][cat] = []
                            for _, player in strong_fas.iterrows():
                                recommendations["free_agent_recommendations"]["batting"][cat].append({
                                    "name": player['name'],
                                    "team": player['team'],
                                    "positions": player['positions'],
                                    "value": player[col_name]
                                })
            
            # Recommend pitchers for weak pitching categories
            for cat in team_analysis["weaknesses"]["pitching"]:
                if cat in self.categories['pitching']:
                    col_name = self.categories['pitching'][cat]
                    
                    if col_name in fa_df.columns:
                        # Filter pitchers
                        fa_pitchers = fa_df[fa_df['positions'].str.contains('SP|RP', case=False)]
                        
                        # Get players strong in this category
                        if not fa_pitchers.empty:
                            # Sort by the category value (note: for ERA, WHIP, BB/9 lower is better)
                            ascending = cat in ['ERA', 'WHIP', 'BB/9']
                            strong_fas = fa_pitchers.sort_values(col_name, ascending=ascending).head(5)
                            
                            # Convert to recommendations
                            recommendations["free_agent_recommendations"]["pitching"][cat] = []
                            for _, player in strong_fas.iterrows():
                                recommendations["free_agent_recommendations"]["pitching"][cat].append({
                                    "name": player['name'],
                                    "team": player['team'],
                                    "positions": player['positions'],
                                    "value": player[col_name]
                                })
        
        return recommendations
    
    def identify_trade_targets(self, team_id: int) -> Dict[str, Any]:
        """
        Identify potential trade targets to address team weaknesses.
        
        Args:
            team_id: Team ID to analyze
            
        Returns:
            Dict: Trade target recommendations
        """
        # First get the team analysis
        team_analysis = self.analyze_team_categories(team_id)
        if "error" in team_analysis:
            return team_analysis
        
        # Initialize recommendations
        recommendations = {
            "team_id": team_id,
            "team_name": team_analysis["team_name"],
            "trade_targets": {
                "batting": {},
                "pitching": {}
            }
        }
        
        # For each weakness, find teams strong in that category
        for category_type in ["batting", "pitching"]:
            for cat in team_analysis["weaknesses"][category_type]:
                # Skip if category not available
                if cat not in self.categories[category_type]:
                    continue
                
                col_name = self.categories[category_type][cat]
                
                # Find teams with strength in this category
                strong_teams = []
                for t in self.teams:
                    if t.team_id == team_id:
                        continue  # Skip the team being analyzed
                    
                    # Get team analysis
                    other_analysis = self.analyze_team_categories(t.team_id)
                    if "error" not in other_analysis:
                        # Check if strong in this category
                        if cat in other_analysis["categories"][category_type]:
                            cat_strength = other_analysis["categories"][category_type][cat].get("strength")
                            if cat_strength in ["Strong", "Very Strong"]:
                                strong_teams.append({
                                    "team_id": t.team_id,
                                    "team_name": t.team_name,
                                    "strength": cat_strength
                                })
                
                # If we found strong teams, look for players to target
                if strong_teams:
                    recommendations["trade_targets"][category_type][cat] = []
                    
                    for strong_team in strong_teams:
                        team_df = self.team_dfs[strong_team["team_id"]]
                        
                        # Filter for appropriate positions
                        if category_type == "batting":
                            players = team_df[~team_df['positions'].str.contains('SP|RP', case=False)]
                        else:
                            players = team_df[team_df['positions'].str.contains('SP|RP', case=False)]
                        
                        if not players.empty and col_name in players.columns:
                            # Sort players by category value
                            ascending = cat in ['ERA', 'WHIP', 'BB/9']
                            top_players = players.sort_values(col_name, ascending=ascending).head(2)
                            
                            # Add to recommendations
                            for _, player in top_players.iterrows():
                                recommendations["trade_targets"][category_type][cat].append({
                                    "name": player['name'],
                                    "team": player['team'],
                                    "positions": player['positions'],
                                    "value": player[col_name],
                                    "owner_team": strong_team["team_name"]
                                })
        
        return recommendations