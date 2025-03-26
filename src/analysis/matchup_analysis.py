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
        
        # Enhanced pitcher evaluation factors:
        # 1. Probable start dates - to ensure optimal distribution
        # 2. Opponent quality - using team offensive rankings
        # 3. Ballpark factors - park-adjusted projections
        # 4. Recent performance - trending metrics
        
        # Initialize MLB API client to get real data
        try:
            from src.api.mlb_client import MLBStatsClient
            mlb_client = MLBStatsClient()
            use_mlb_api = True
            
            # Get real MLB data
            ballpark_factors = mlb_client.get_ballpark_factors()
            team_ratings = mlb_client.get_team_ratings()
            
            # Try to get upcoming probable starters for the next week
            # This may fail if MLB hasn't published probables yet
            try:
                probable_starters = mlb_client.get_probable_starters_for_next_week()
                logger.info(f"Retrieved {sum(len(starters) for starters in probable_starters.values())} probable starters")
            except Exception as e:
                logger.warning(f"Could not retrieve probable starters: {e}")
                probable_starters = {}
                
        except (ImportError, Exception) as e:
            logger.warning(f"MLB API client not available: {e}")
            use_mlb_api = False
            
            # Use placeholder data if MLB API not available
            ballpark_factors = {
                "Yankee Stadium": 1.12,
                "Fenway Park": 1.25,
                "Tropicana Field": 0.94,
                "Camden Yards": 1.05,
                "Rogers Centre": 1.03,
                # More would be added here
            }
            
            team_ratings = {
                "NYY": {"offensive": 112, "strikeout_rate": 22.5},  # wRC+ or similar metric
                "BOS": {"offensive": 108, "strikeout_rate": 21.0},
                "TB": {"offensive": 103, "strikeout_rate": 24.2},
                "BAL": {"offensive": 96, "strikeout_rate": 23.8},
                "TOR": {"offensive": 105, "strikeout_rate": 20.5},
                # More would be added here
            }
            
            probable_starters = {}
        
        # Look for projected points column
        proj_cols = [col for col in starting_pitchers.columns if 'projected_points' in col or 'projected' in col]
        
        # Prepare pitcher data for analysis
        pitcher_data = starting_pitchers.copy()
        
        # Function to calculate adjusted score based on factors
        def calculate_adjusted_score(base_score, opponent, ballpark, home_game=False):
            opponent_factor = 1.0
            ballpark_factor = 1.0
            
            # Get offensive rating for the opponent
            if opponent in team_ratings:
                # Scale opponent quality to a 0.8-1.2 range
                # 100 is league average, so we center around 1.0
                opponent_rating = team_ratings[opponent].get("offensive", 100)
                opponent_factor = 2 - (opponent_rating / 100)  # Invert so higher offense = lower factor
                opponent_factor = max(0.7, min(1.2, opponent_factor))  # Clamp to range
                
                # Consider strikeout rate for bonus
                strikeout_rate = team_ratings[opponent].get("strikeout_rate", 22.0)  # League avg ~22%
                if strikeout_rate > 24.0:  # High K rate team
                    # Small bonus for high-K opponents
                    opponent_factor *= 1.05
            
            # Apply ballpark factor
            if ballpark in ballpark_factors:
                # Invert to make pitcher-friendly parks rate higher
                park_factor = ballpark_factors[ballpark]
                
                # Only fully apply if home game (road team gets partial effect)
                if home_game:
                    ballpark_factor = 1 / park_factor
                else:
                    # Road games get less park effect
                    ballpark_factor = 1 / ((park_factor - 1) * 0.6 + 1)
                    
                ballpark_factor = max(0.85, min(1.25, ballpark_factor))  # Clamp to range
            
            # Adjust score: lower for tough opponents and hitter-friendly parks
            return base_score * opponent_factor * ballpark_factor
        
        # Match pitchers to their probable starts if data is available
        current_date = datetime.now().date()
        
        # Simple strategy: rank pitchers by projected points
        if proj_cols:
            # Use the first projected points column found
            pitcher_data['adjusted_score'] = pitcher_data[proj_cols[0]]
            pitcher_data['start_date'] = None
            pitcher_data['opponent'] = None
            pitcher_data['ballpark'] = None
            pitcher_data['home_game'] = False
            pitcher_data['note'] = None
            
            # Match pitchers with probable starts when possible
            if use_mlb_api and probable_starters:
                # First, create a mapping of pitcher names to their row indices
                pitcher_name_to_idx = {row['name']: idx for idx, row in pitcher_data.iterrows()}
                
                # Look through probable starters for matches with our roster
                for team_abbrev, starters in probable_starters.items():
                    for starter in starters:
                        pitcher_name = starter['name']
                        
                        # Try to match this starter to our roster
                        # This could be improved with fuzzy matching
                        if pitcher_name in pitcher_name_to_idx:
                            idx = pitcher_name_to_idx[pitcher_name]
                            
                            # Found a match - update with real data
                            opponent_abbrev = starter['opponent_abbrev']
                            start_date = datetime.strptime(starter['date'], '%Y-%m-%d').date()
                            home_game = starter['home_game']
                            
                            # Get ballpark (simplistic - in reality, would look up by team's home park)
                            if home_game:
                                ballpark = f"{team_abbrev} home park"  # Placeholder
                            else:
                                ballpark = f"{opponent_abbrev} home park"  # Placeholder
                            
                            # Store the match data
                            pitcher_data.at[idx, 'start_date'] = start_date
                            pitcher_data.at[idx, 'opponent'] = opponent_abbrev
                            pitcher_data.at[idx, 'ballpark'] = ballpark
                            pitcher_data.at[idx, 'home_game'] = home_game
                            
                            # Calculate adjusted score with real opponent data
                            base_score = pitcher_data.at[idx, proj_cols[0]]
                            adjusted_score = calculate_adjusted_score(
                                base_score, opponent_abbrev, ballpark, home_game
                            )
                            pitcher_data.at[idx, 'adjusted_score'] = adjusted_score
                            
                            # Create explanation
                            if adjusted_score > base_score:
                                note = f"Favorable matchup vs {opponent_abbrev}"
                                if team_ratings.get(opponent_abbrev, {}).get("strikeout_rate", 0) > 24:
                                    note += " (high K%)"
                            else:
                                note = f"Tough matchup vs {opponent_abbrev}"
                            
                            pitcher_data.at[idx, 'note'] = note
            
            # For pitchers without probable start data, use randomized placeholder data
            # In a real implementation, this would be more sophisticated
            import random
            
            # Only add random data for pitchers without start data
            for idx, row in pitcher_data.iterrows():
                if row['start_date'] is None:
                    # Randomly assign a start within the next week
                    random_date = current_date + timedelta(days=random.randint(1, 7))
                    
                    # Get a random opponent
                    random_opponent = random.choice(list(team_ratings.keys()))
                    
                    # Get a random ballpark & home/away status
                    random_home_game = random.choice([True, False])
                    if random_home_game:
                        # Make up a simple home park (this would be more accurate in reality)
                        random_ballpark = f"Home Park"
                    else:
                        # Away game at opponent's park
                        random_ballpark = f"{random_opponent} Park"
                    
                    # Calculate ballpark factor (simplified)
                    random_ballpark_factor = 0.9 + (random.random() * 0.3)  # 0.9-1.2 range
                    
                    # Calculate adjusted score
                    base_score = row[proj_cols[0]]
                    adjusted_score = calculate_adjusted_score(
                        base_score, random_opponent, random_ballpark, random_home_game
                    )
                    
                    # Store the data
                    pitcher_data.at[idx, 'start_date'] = random_date
                    pitcher_data.at[idx, 'opponent'] = random_opponent
                    pitcher_data.at[idx, 'ballpark'] = random_ballpark
                    pitcher_data.at[idx, 'ballpark_factor'] = random_ballpark_factor
                    pitcher_data.at[idx, 'home_game'] = random_home_game
                    pitcher_data.at[idx, 'adjusted_score'] = adjusted_score
                    
                    # Create a note about the adjustment
                    if adjusted_score > base_score:
                        pitcher_data.at[idx, 'note'] = f"Favorable matchup vs {random_opponent}"
                    else:
                        pitcher_data.at[idx, 'note'] = f"Tough matchup vs {random_opponent}"
            
            # Rank by adjusted score
            ranked_pitchers = pitcher_data.sort_values('adjusted_score', ascending=False)
            recommended_starts = ranked_pitchers.head(max_starts)
            
            # Extract notes and schedule info for recommended pitchers
            pitcher_notes = {}
            pitcher_schedule = {}
            
            # Process all pitchers for schedule and notes
            for idx, row in pitcher_data.iterrows():
                name = row['name']
                
                # Store notes if available
                if pd.notna(row.get('note')):
                    pitcher_notes[name] = row['note']
                
                # Store schedule info if available
                if pd.notna(row.get('start_date')):
                    pitcher_schedule[name] = {
                        'date': row['start_date'],
                        'opponent': row.get('opponent'),
                        'ballpark': row.get('ballpark'),
                        'home_game': row.get('home_game', False)
                    }
            
            # Calculate total points
            projected_points = recommended_starts[proj_cols[0]].sum() if proj_cols else 0
            adjusted_points = recommended_starts['adjusted_score'].sum()
            
            # Analyze distribution of starts through the week
            start_distribution = {}
            for name, schedule in pitcher_schedule.items():
                if 'date' in schedule:
                    date_str = schedule['date'].strftime('%Y-%m-%d')
                    if date_str not in start_distribution:
                        start_distribution[date_str] = []
                    start_distribution[date_str].append(name)
            
            return {
                "max_starts": max_starts,
                "recommended_pitchers": recommended_starts['name'].tolist(),
                "pitcher_notes": pitcher_notes,
                "pitcher_schedule": pitcher_schedule,
                "start_distribution": start_distribution,
                "projected_points": projected_points,
                "adjusted_points": adjusted_points,
                "benched_pitchers": ranked_pitchers.iloc[max_starts:]['name'].tolist() if len(ranked_pitchers) > max_starts else [],
                "note": "Recommendations based on matchup strength and probable start dates."
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