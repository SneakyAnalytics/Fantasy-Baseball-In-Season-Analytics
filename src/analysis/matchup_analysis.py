# src/analysis/matchup_analysis.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

from src.data.models import Team, Player, Matchup
from src.data.processors import PlayerDataProcessor

logger = logging.getLogger(__name__)

class MatchupAnalyzer:
    """Analyze fantasy baseball matchups and provide strategic insights."""
    
    def __init__(self, matchup: Optional[Matchup] = None, 
                 team: Optional[Team] = None, opponent: Optional[Team] = None,
                 all_players: Optional[List[Player]] = None,
                 free_agents: Optional[List[Player]] = None):
        """
        Initialize the matchup analyzer.
        
        Args:
            matchup: Matchup object (optional)
            team: User's team (optional, can be extracted from matchup)
            opponent: Opponent's team (optional, can be extracted from matchup)
            all_players: List of all players in the league (optional)
            free_agents: List of available free agents (optional)
        """
        self.matchup = matchup
        
        # If matchup is provided, extract team and opponent
        if matchup:
            if team:
                # User's team is provided, so the opponent is the other team
                self.team = team
                self.opponent = matchup.team_1 if matchup.team_1.team_id != team.team_id else matchup.team_2
            else:
                # Assume team_1 is the user's team for now (will be configurable)
                self.team = matchup.team_1
                self.opponent = matchup.team_2
        else:
            self.team = team
            self.opponent = opponent
        
        self.all_players = all_players
        self.free_agents = free_agents
        
        # Convert player lists to DataFrames for easier analysis
        self.all_players_df = PlayerDataProcessor.players_to_dataframe(all_players) if all_players else None
        self.free_agents_df = PlayerDataProcessor.players_to_dataframe(free_agents) if free_agents else None
        
        # Get team rosters as DataFrames
        self.team_roster_df = PlayerDataProcessor.players_to_dataframe(self.team.roster) if self.team and self.team.roster else None
        self.opponent_roster_df = PlayerDataProcessor.players_to_dataframe(self.opponent.roster) if self.opponent and self.opponent.roster else None
    
    def analyze_position_matchups(self) -> Dict[str, Any]:
        """
        Analyze matchups position by position.
        
        Returns:
            Dict: Analysis of each position matchup including projected points
        """
        if not self.team_roster_df is not None or self.opponent_roster_df is not None:
            logger.warning("Team roster data is not available")
            return {}
        
        # Define positions to analyze (based on league settings)
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'UTIL', 'SP', 'RP']
        
        position_analysis = {}
        for pos in positions:
            # Find players at this position on each team
            team_pos_players = self.team_roster_df[self.team_roster_df['positions'].str.contains(pos, case=False)]
            opp_pos_players = self.opponent_roster_df[self.opponent_roster_df['positions'].str.contains(pos, case=False)]
            
            # Get projected points if available
            team_proj = self._calculate_position_projection(team_pos_players, pos)
            opp_proj = self._calculate_position_projection(opp_pos_players, pos)
            
            # Determine advantage
            advantage = "team" if team_proj > opp_proj else "opponent" if opp_proj > team_proj else "even"
            diff = abs(team_proj - opp_proj)
            
            position_analysis[pos] = {
                "team_projection": team_proj,
                "opponent_projection": opp_proj,
                "advantage": advantage,
                "difference": diff,
                "team_players": team_pos_players['name'].tolist() if not team_pos_players.empty else [],
                "opponent_players": opp_pos_players['name'].tolist() if not opp_pos_players.empty else []
            }
        
        return position_analysis
    
    def _calculate_position_projection(self, players_df: pd.DataFrame, position: str) -> float:
        """
        Calculate projected points for a position.
        
        Args:
            players_df: DataFrame of players at this position
            position: Position to calculate for
            
        Returns:
            float: Projected points
        """
        if players_df.empty:
            return 0.0
        
        # Look for projected points column
        proj_cols = [col for col in players_df.columns if 'projected_points' in col]
        if proj_cols:
            # Use the first projected points column found
            return players_df[proj_cols[0]].sum()
        
        # If no projection column, estimate from available stats
        # This would be expanded with a more sophisticated projection algorithm
        return 0.0
    
    def optimize_pitcher_starts(self, max_starts: int = 12) -> Dict[str, Any]:
        """
        Optimize pitcher starts within the maximum allowed.
        
        Args:
            max_starts: Maximum number of pitcher starts allowed per matchup
            
        Returns:
            Dict: Optimal pitching strategy
        """
        if self.team_roster_df is None:
            logger.warning("Team roster data is not available")
            return {}
        
        # Get starting pitchers
        starting_pitchers = self.team_roster_df[self.team_roster_df['positions'].str.contains('SP', case=False)]
        if starting_pitchers.empty:
            return {"error": "No starting pitchers found on roster"}
        
        # For now, use a simple projection-based strategy
        # In reality, you'd want to factor in:
        # - Probable start dates for each pitcher
        # - Opponent quality
        # - Ballpark factors
        # - Recent performance
        
        # Look for projected points column
        proj_cols = [col for col in starting_pitchers.columns if 'projected_points' in col or 'projected' in col]
        
        # Simple strategy: rank pitchers by projected points
        if proj_cols:
            # Use the first projected points column found
            ranked_pitchers = starting_pitchers.sort_values(proj_cols[0], ascending=False)
            recommended_starts = ranked_pitchers.head(max_starts)
            
            return {
                "max_starts": max_starts,
                "recommended_pitchers": recommended_starts['name'].tolist(),
                "projected_points": recommended_starts[proj_cols[0]].sum() if proj_cols else 0,
                "benched_pitchers": ranked_pitchers.iloc[max_starts:]['name'].tolist() if len(ranked_pitchers) > max_starts else []
            }
        
        # If no projections available, just return all pitchers
        return {
            "max_starts": max_starts,
            "recommended_pitchers": starting_pitchers['name'].tolist(),
            "note": "No projections available, recommendation based on roster only"
        }
    
    def recommend_acquisitions(self, limit: int = 8) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recommend waiver wire pickups based on team needs.
        
        Args:
            limit: Maximum number of acquisitions per matchup
            
        Returns:
            Dict: Recommended acquisitions by position
        """
        if self.free_agents_df is None or self.team_roster_df is None:
            logger.warning("Free agent or team roster data is not available")
            return {}
        
        recommendations = {}
        
        # Identify team weaknesses by position
        team_strength = self._analyze_team_position_strength()
        
        # Positions to check (excluding RP for now)
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'SP']
        
        for pos in positions:
            if pos in team_strength and team_strength[pos]["strength"] < 0.7:  # Arbitrary threshold
                # This position is a weakness, look for upgrades
                pos_free_agents = self.free_agents_df[self.free_agents_df['positions'].str.contains(pos, case=False)]
                
                if not pos_free_agents.empty:
                    # Look for projected points column
                    proj_cols = [col for col in pos_free_agents.columns if 'projected_points' in col or 'projected' in col]
                    
                    if proj_cols:
                        # Rank free agents by projection
                        ranked_fas = pos_free_agents.sort_values(proj_cols[0], ascending=False)
                        
                        # Get top 3 free agents
                        top_fas = ranked_fas.head(3)
                        
                        recommendations[pos] = top_fas[['name', 'team', proj_cols[0]]].to_dict('records')
        
        # Add streaming pitcher recommendations
        streaming_sp = self._recommend_streaming_pitchers()
        if streaming_sp:
            recommendations["streaming_sp"] = streaming_sp
        
        return recommendations
    
    def _analyze_team_position_strength(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze team strength by position.
        
        Returns:
            Dict: Position strength analysis
        """
        if self.team_roster_df is None or self.all_players_df is None:
            return {}
        
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'SP', 'RP']
        strength_analysis = {}
        
        for pos in positions:
            # Find players at this position on team
            team_pos_players = self.team_roster_df[self.team_roster_df['positions'].str.contains(pos, case=False)]
            
            if team_pos_players.empty:
                strength_analysis[pos] = {"strength": 0.0, "note": "No players at this position"}
                continue
            
            # Find all players at this position
            all_pos_players = self.all_players_df[self.all_players_df['positions'].str.contains(pos, case=False)]
            
            if all_pos_players.empty:
                continue
            
            # Look for projected points column
            proj_cols = [col for col in all_pos_players.columns if 'projected_points' in col or 'projected' in col]
            
            if proj_cols:
                # Calculate team strength as percentile of all players
                team_avg = team_pos_players[proj_cols[0]].mean() if not team_pos_players.empty else 0
                all_avg = all_pos_players[proj_cols[0]].mean()
                all_std = all_pos_players[proj_cols[0]].std()
                
                if all_std > 0:
                    z_score = (team_avg - all_avg) / all_std
                    # Convert z-score to percentile (simplified)
                    percentile = min(max((z_score + 3) / 6, 0), 1)  # Crude mapping of z-scores to 0-1 range
                else:
                    percentile = 0.5  # Default if no variation
                
                strength_analysis[pos] = {
                    "strength": percentile,
                    "team_avg": team_avg,
                    "league_avg": all_avg
                }
        
        return strength_analysis
    
    def _recommend_streaming_pitchers(self) -> List[Dict[str, Any]]:
        """
        Recommend pitchers for streaming starts.
        
        Returns:
            List: Recommended streaming pitchers
        """
        if self.free_agents_df is None:
            return []
        
        # Get SPs from free agents
        fa_sp = self.free_agents_df[self.free_agents_df['positions'].str.contains('SP', case=False)]
        
        if fa_sp.empty:
            return []
        
        # Look for projected points column
        proj_cols = [col for col in fa_sp.columns if 'projected_points' in col or 'projected' in col]
        
        if not proj_cols:
            return []
        
        # Rank by projected points
        ranked_sp = fa_sp.sort_values(proj_cols[0], ascending=False)
        
        # Get top 5 streaming options
        top_sp = ranked_sp.head(5)
        
        return top_sp[['name', 'team', proj_cols[0]]].to_dict('records')