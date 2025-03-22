# src/analysis/fantasy_analysis.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from src.data.models import Player, Team
from src.data.processors import PlayerDataProcessor

logger = logging.getLogger(__name__)

class FantasyAnalyzer:
    """Fantasy baseball specific analysis tools."""
    
    def __init__(self, players: Optional[List[Player]] = None, teams: Optional[List[Team]] = None):
        """
        Initialize with player and team data.
        
        Args:
            players: List of Player objects
            teams: List of Team objects
        """
        self.players = players
        self.teams = teams
        self.player_df = None
        
        if players:
            self.player_df = PlayerDataProcessor.players_to_dataframe(players)
    
    def identify_undervalued_players(self, actual_stat: str, projected_stat: str, threshold: float = 0.2) -> pd.DataFrame:
        """
        Identify players who are underperforming their projections but likely to improve.
        
        Args:
            actual_stat: Column name for actual performance stat
            projected_stat: Column name for projected stat
            threshold: Minimum difference threshold (as a fraction of projection)
            
        Returns:
            pd.DataFrame: Undervalued players
        """
        if self.player_df is None or actual_stat not in self.player_df.columns or projected_stat not in self.player_df.columns:
            logger.warning(f"Required statistics not available: {actual_stat}, {projected_stat}")
            return pd.DataFrame()
        
        # Filter to numeric columns and rows with both stats available
        df = self.player_df[self.player_df[actual_stat].notna() & self.player_df[projected_stat].notna()]
        
        # Calculate difference between actual and projected
        df['diff'] = df[projected_stat] - df[actual_stat]
        df['diff_pct'] = df['diff'] / df[projected_stat]
        
        # Find players with significant positive difference (undervalued)
        undervalued = df[df['diff_pct'] > threshold].sort_values('diff_pct', ascending=False)
        
        return undervalued[['name', 'team', 'positions', actual_stat, projected_stat, 'diff', 'diff_pct']]
    
    def identify_overperforming_players(self, actual_stat: str, projected_stat: str, threshold: float = 0.2) -> pd.DataFrame:
        """
        Identify players who are significantly outperforming their projections.
        
        Args:
            actual_stat: Column name for actual performance stat
            projected_stat: Column name for projected stat
            threshold: Minimum difference threshold (as a fraction of projection)
            
        Returns:
            pd.DataFrame: Overperforming players
        """
        if self.player_df is None or actual_stat not in self.player_df.columns or projected_stat not in self.player_df.columns:
            logger.warning(f"Required statistics not available: {actual_stat}, {projected_stat}")
            return pd.DataFrame()
        
        # Filter to numeric columns and rows with both stats available
        df = self.player_df[self.player_df[actual_stat].notna() & self.player_df[projected_stat].notna()]
        
        # Calculate difference between actual and projected
        df['diff'] = df[actual_stat] - df[projected_stat]
        df['diff_pct'] = df['diff'] / df[projected_stat]
        
        # Find players with significant positive difference (overperforming)
        overperforming = df[df['diff_pct'] > threshold].sort_values('diff_pct', ascending=False)
        
        return overperforming[['name', 'team', 'positions', actual_stat, projected_stat, 'diff', 'diff_pct']]
    
    def find_position_scarcity(self) -> Dict[str, Any]:
        """
        Analyze position scarcity in the league.
        
        Returns:
            Dict: Position scarcity analysis
        """
        if self.player_df is None:
            logger.warning("No player data available")
            return {}
        
        # Extract positions
        all_positions = []
        for pos_list in self.player_df['positions'].str.split(',').dropna():
            all_positions.extend([p.strip() for p in pos_list if p.strip()])
        
        # Count players by position
        position_counts = pd.Series(all_positions).value_counts().to_dict()
        
        # Get available performance stats
        perf_stats = [col for col in self.player_df.columns 
                     if col not in ['player_id', 'name', 'team', 'positions'] 
                     and pd.api.types.is_numeric_dtype(self.player_df[col])]
        
        # Analyze position depth - performance drop-off between top and average players
        position_depth = {}
        for pos in position_counts.keys():
            pos_players = self.player_df[self.player_df['positions'].str.contains(pos)]
            
            if len(pos_players) > 5:  # Need at least a few players to analyze
                depth_metrics = {}
                for stat in perf_stats:
                    if pos_players[stat].notna().sum() > 5:
                        # Sort by this stat (assuming higher is better)
                        sorted_players = pos_players.sort_values(stat, ascending=False)
                        
                        # Calculate metrics
                        top_avg = sorted_players.iloc[:5][stat].mean()
                        mid_avg = sorted_players.iloc[5:15][stat].mean() if len(sorted_players) > 15 else sorted_players.iloc[5:][stat].mean()
                        
                        # Calculate drop-off
                        if mid_avg > 0:
                            dropoff = (top_avg - mid_avg) / mid_avg
                            depth_metrics[stat] = {
                                'top_avg': top_avg,
                                'mid_avg': mid_avg,
                                'dropoff': dropoff
                            }
                
                if depth_metrics:
                    position_depth[pos] = depth_metrics
        
        return {
            'position_counts': position_counts,
            'position_depth': position_depth
        }
    
    def suggest_trade_targets(self, team_id: int) -> Dict[str, Any]:
        """
        Suggest potential trade targets for a team.
        
        Args:
            team_id: ID of the team to analyze
            
        Returns:
            Dict: Trade target suggestions
        """
        if self.player_df is None or not self.teams:
            logger.warning("Insufficient data for trade analysis")
            return {}
        
        # Find the team
        target_team = None
        for team in self.teams:
            if team.team_id == team_id:
                target_team = team
                break
        
        if not target_team:
            logger.warning(f"Team with ID {team_id} not found")
            return {}
        
        # Get team roster
        if not hasattr(target_team, 'roster') or not target_team.roster:
            logger.warning(f"No roster data for team {target_team.team_name}")
            return {}
        
        # Convert roster to DataFrame
        roster_df = PlayerDataProcessor.players_to_dataframe(target_team.roster)
        
        # Analyze team positions
        team_positions = []
        for pos_list in roster_df['positions'].str.split(',').dropna():
            team_positions.extend([p.strip() for p in pos_list if p.strip()])
        
        team_position_counts = pd.Series(team_positions).value_counts().to_dict()
        
        # Find positions where team is weak
        position_scarcity = self.find_position_scarcity()
        
        weak_positions = []
        for pos, count in position_scarcity.get('position_counts', {}).items():
            team_count = team_position_counts.get(pos, 0)
            if team_count < count * 0.1:  # Team has less than 10% of available players at this position
                weak_positions.append(pos)
        
        # Find potential trade targets for weak positions
        trade_targets = {}
        for pos in weak_positions:
            pos_players = self.player_df[self.player_df['positions'].str.contains(pos)]
            
            # Get projected stats
            proj_stats = [col for col in pos_players.columns 
                         if col.startswith('projected_') and pd.api.types.is_numeric_dtype(pos_players[col])]
            
            if proj_stats:
                # Use first projected stat for ranking
                stat = proj_stats[0]
                targets = pos_players.sort_values(stat, ascending=False).head(5)
                
                trade_targets[pos] = targets[['name', 'team', 'positions', stat]].to_dict('records')
        
        return {
            'team_name': target_team.team_name,
            'weak_positions': weak_positions,
            'trade_targets': trade_targets
        }