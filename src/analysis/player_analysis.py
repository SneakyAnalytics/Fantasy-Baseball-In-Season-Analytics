# src/analysis/player_analysis.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from src.data.models import Player, Team
from src.data.processors import PlayerDataProcessor

logger = logging.getLogger(__name__)

class PlayerAnalyzer:
    """Analyze player performance in a fantasy baseball league."""
    
    def __init__(self, players: Optional[List[Player]] = None):
        """
        Initialize with a list of players.
        
        Args:
            players: List of Player objects (optional)
        """
        self.players = players
        self.player_df = None
        if players:
            self.player_df = PlayerDataProcessor.players_to_dataframe(players)
    
    def set_players(self, players: List[Player]):
        """
        Set or update the list of players.
        
        Args:
            players: List of Player objects
        """
        self.players = players
        self.player_df = PlayerDataProcessor.players_to_dataframe(players)
    
    def get_top_players(self, stat: str, limit: int = 10, ascending: bool = False) -> pd.DataFrame:
        """
        Get top players by a specific statistic.
        
        Args:
            stat: Statistic column name
            limit: Number of players to return
            ascending: Sort in ascending order if True
            
        Returns:
            pd.DataFrame: DataFrame of top players
        """
        if self.player_df is None or stat not in self.player_df.columns:
            logger.warning(f"Statistic '{stat}' not available")
            return pd.DataFrame()
        
        return self.player_df.sort_values(stat, ascending=ascending).head(limit)[
            ['name', 'team', 'positions', stat]
        ]
    
    def get_player_by_name(self, name: str) -> pd.Series:
        """
        Get player by name.
        
        Args:
            name: Player name
            
        Returns:
            pd.Series: Player data
        """
        if self.player_df is None:
            logger.warning("No player data available")
            return pd.Series()
            
        matches = self.player_df[self.player_df['name'].str.contains(name, case=False)]
        if len(matches) == 0:
            logger.warning(f"No player found with name containing '{name}'")
            return pd.Series()
        return matches.iloc[0]
    
    def get_players_by_position(self, position: str) -> pd.DataFrame:
        """
        Get players by position.
        
        Args:
            position: Player position
            
        Returns:
            pd.DataFrame: DataFrame of players at the specified position
        """
        if self.player_df is None:
            logger.warning("No player data available")
            return pd.DataFrame()
            
        return self.player_df[self.player_df['positions'].str.contains(position, case=False)]
    
    def compare_players(self, player1_name: str, player2_name: str, stats: List[str]) -> Dict[str, Any]:
        """
        Compare two players across specified statistics.
        
        Args:
            player1_name: Name of first player
            player2_name: Name of second player
            stats: List of statistics to compare
            
        Returns:
            dict: Comparison results
        """
        if self.player_df is None:
            logger.warning("No player data available")
            return {"error": "No player data available"}
            
        player1 = self.get_player_by_name(player1_name)
        player2 = self.get_player_by_name(player2_name)
        
        if player1.empty or player2.empty:
            return {"error": "One or both players not found"}
        
        comparison = {
            "player1": player1['name'],
            "player2": player2['name'],
            "statistics": {}
        }
        
        for stat in stats:
            if stat in player1 and stat in player2:
                val1 = player1[stat]
                val2 = player2[stat]
                comparison["statistics"][stat] = {
                    "player1_value": val1,
                    "player2_value": val2,
                    "difference": val1 - val2,
                    "percentage_diff": (val1 - val2) / val2 * 100 if val2 != 0 else None
                }
        
        return comparison

    def analyze_team_roster(self, team: Team) -> Dict[str, Any]:
        """
        Analyze a team's roster.
        
        Args:
            team: Team object
            
        Returns:
            dict: Analysis results
        """
        if not team.roster:
            return {"error": "Team has no roster data"}
        
        # Create DataFrame from roster
        roster_df = PlayerDataProcessor.players_to_dataframe(team.roster)
        
        # Identify team strengths and weaknesses by position
        positions = {}
        for pos in set(','.join(roster_df['positions']).split(',')):
            pos = pos.strip()
            if not pos:
                continue
                
            players = roster_df[roster_df['positions'].str.contains(pos, case=False)]
            if not players.empty:
                positions[pos] = {
                    "count": len(players),
                    "players": players['name'].tolist()
                }
        
        # Analyze team statistics if available
        stats_analysis = {}
        stat_cols = [col for col in roster_df.columns if col.startswith(('total_', 'avg_'))]
        
        if stat_cols:
            for stat in stat_cols:
                stats_analysis[stat] = {
                    "total": roster_df[stat].sum(),
                    "average": roster_df[stat].mean(),
                    "top_player": roster_df.loc[roster_df[stat].idxmax(), 'name'] if not roster_df[stat].isna().all() else None
                }
        
        return {
            "team_name": getattr(team, 'team_name', 'Unknown Team'),
            "roster_size": len(team.roster),
            "positions": positions,
            "statistics": stats_analysis
        }