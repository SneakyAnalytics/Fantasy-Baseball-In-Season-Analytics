# src/analysis/player_analysis.py
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta

from src.data.models import Player, Team
from src.data.processors import PlayerDataProcessor

# Import the new Savant client if available
try:
    from src.api.savant_client import BaseballSavantClient
    HAS_SAVANT = True
except ImportError:
    HAS_SAVANT = False
    
# Import the MLB client if available
try:
    from src.api.mlb_client import MLBStatsClient
    HAS_MLB_API = True
except ImportError:
    HAS_MLB_API = False

logger = logging.getLogger(__name__)

class PlayerAnalyzer:
    """Analyze player performance in a fantasy baseball league with advanced metrics."""
    
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
            
        # Initialize advanced stats clients if available
        self.savant_client = BaseballSavantClient() if HAS_SAVANT else None
        self.mlb_client = MLBStatsClient() if HAS_MLB_API else None
        
        # Player ID mapping cache (name -> MLB ID)
        self.player_id_mapping = {}
    
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
    
    def find_trending_players(self, min_sample_size: int = 25, player_type: str = "both") -> Dict[str, List[Dict[str, Any]]]:
        """
        Find players who are trending up based on Statcast data.
        
        Args:
            min_sample_size: Minimum sample size to consider
            player_type: Type of players to analyze ('batter', 'pitcher', or 'both')
            
        Returns:
            Dict: Lists of trending players by direction (up/down)
        """
        if not self.savant_client:
            logger.warning("Baseball Savant client not available")
            return {"trending_up": [], "trending_down": []}
        
        trending_up = []
        trending_down = []
        
        # Process batters if requested
        if player_type in ["batter", "both"]:
            try:
                # Get batters with positive trends
                batter_candidates = self.savant_client.find_breakout_candidates(
                    player_type="batter", 
                    min_sample=min_sample_size
                )
                
                # Add context and format results
                for candidate in batter_candidates:
                    # Check if player is in our player list (roster, waiver, etc.)
                    player_in_league = False
                    player_obj = None
                    
                    if self.player_df is not None:
                        # Try to match by name (could use ID mapping for better matching)
                        matches = self.player_df[self.player_df['name'].str.contains(
                            candidate['name'].split(',')[0], case=False)]
                        
                        if not matches.empty:
                            player_in_league = True
                            player_obj = self.get_player_by_name(candidate['name'].split(',')[0])
                    
                    # Create trend record
                    trend_record = {
                        'name': candidate['name'],
                        'team': candidate['team'],
                        'player_id': candidate['player_id'],
                        'breakout_score': candidate['breakout_score'],
                        'reason': candidate['reason'],
                        'metrics': candidate['metrics'],
                        'in_league': player_in_league,
                        'available': player_in_league and (player_obj.empty or not player_obj.get('rostered', True)),
                        'position': 'batter'
                    }
                    
                    # High breakout score = trending up
                    if candidate['breakout_score'] > 1.2:
                        trending_up.append(trend_record)
                    elif candidate['breakout_score'] < 0.5:
                        trending_down.append(trend_record)
            
            except Exception as e:
                logger.error(f"Error analyzing batter trends: {e}")
        
        # Process pitchers if requested
        if player_type in ["pitcher", "both"]:
            try:
                # Get pitchers with positive trends
                pitcher_candidates = self.savant_client.find_breakout_candidates(
                    player_type="pitcher", 
                    min_sample=min_sample_size
                )
                
                # Add context and format results
                for candidate in pitcher_candidates:
                    # Check if player is in our player list (roster, waiver, etc.)
                    player_in_league = False
                    player_obj = None
                    
                    if self.player_df is not None:
                        # Try to match by name (could use ID mapping for better matching)
                        matches = self.player_df[self.player_df['name'].str.contains(
                            candidate['name'].split(',')[0], case=False)]
                        
                        if not matches.empty:
                            player_in_league = True
                            player_obj = self.get_player_by_name(candidate['name'].split(',')[0])
                    
                    # Create trend record
                    trend_record = {
                        'name': candidate['name'],
                        'team': candidate['team'],
                        'player_id': candidate['player_id'],
                        'breakout_score': candidate['breakout_score'],
                        'reason': candidate['reason'],
                        'metrics': candidate['metrics'],
                        'in_league': player_in_league,
                        'available': player_in_league and (player_obj.empty or not player_obj.get('rostered', True)),
                        'position': 'pitcher'
                    }
                    
                    # High breakout score = trending up
                    if candidate['breakout_score'] > 1.2:
                        trending_up.append(trend_record)
                    elif candidate['breakout_score'] < 0.5:
                        trending_down.append(trend_record)
            
            except Exception as e:
                logger.error(f"Error analyzing pitcher trends: {e}")
        
        # Sort by breakout score
        trending_up.sort(key=lambda x: x['breakout_score'], reverse=True)
        trending_down.sort(key=lambda x: x['breakout_score'])
        
        return {
            "trending_up": trending_up[:20],  # Limit to top 20
            "trending_down": trending_down[:10]  # Limit to top 10
        }
    
    def get_player_statcast_metrics(self, player_name: str) -> Dict[str, Any]:
        """
        Get detailed Statcast metrics for a specific player.
        
        Args:
            player_name: Name of the player
            
        Returns:
            Dict: Statcast metrics and trends
        """
        if not self.savant_client:
            logger.warning("Baseball Savant client not available")
            return {"error": "Baseball Savant client not available"}
        
        # Get player from our database
        player = self.get_player_by_name(player_name)
        if player.empty:
            return {"error": f"Player '{player_name}' not found"}
        
        # Determine if player is a batter or pitcher
        positions = player.get('positions', '').upper()
        player_type = "batter"
        if any(pos in positions for pos in ['SP', 'RP', 'P']):
            player_type = "pitcher"
        
        # Get or update MLB ID mapping
        if not self.player_id_mapping:
            try:
                # Fetch player ID mapping from Baseball Savant
                self.player_id_mapping = self.savant_client.get_player_id_mapping()
            except Exception as e:
                logger.error(f"Error fetching player ID mapping: {e}")
                return {"error": "Failed to get player ID mapping"}
        
        # Find MLB ID for this player
        mlb_id = None
        # First try direct name match
        if player_name in self.player_id_mapping:
            mlb_id = self.player_id_mapping[player_name]
        else:
            # Try partial matching
            for db_name, db_id in self.player_id_mapping.items():
                if player_name.lower() in db_name.lower():
                    mlb_id = db_id
                    break
        
        if not mlb_id:
            return {"error": f"Could not find MLB ID for player '{player_name}'"}
        
        # Get Statcast data for this player
        try:
            player_trends = self.savant_client.get_statcast_player_trends(
                player_id=mlb_id,
                player_type=player_type
            )
            
            # Get leaderboard context for this player
            if player_type == "batter":
                leaderboard = self.savant_client.get_statcast_leaderboard(
                    player_type="batter", 
                    stats_type="expected"
                )
            else:
                leaderboard = self.savant_client.get_statcast_leaderboard(
                    player_type="pitcher", 
                    stats_type="expected"
                )
            
            # Find player in leaderboard
            player_row = None
            if not leaderboard.empty and 'player_id' in leaderboard.columns:
                player_row = leaderboard[leaderboard['player_id'] == mlb_id]
            
            # Combine data
            result = {
                "name": player_name,
                "player_id": mlb_id,
                "type": player_type,
                "trends": player_trends,
                "leaderboard_data": player_row.to_dict('records')[0] if not player_row.empty else None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting Statcast data for {player_name}: {e}")
            return {"error": f"Failed to get Statcast data: {str(e)}"}
    
    def find_waiver_wire_gems(self, free_agents: List[Player], min_sample_size: int = 25) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find undervalued players on the waiver wire using Statcast metrics.
        
        Args:
            free_agents: List of available free agents
            min_sample_size: Minimum sample size to consider
            
        Returns:
            Dict: Lists of recommended pickups by position
        """
        if not self.savant_client:
            logger.warning("Baseball Savant client not available")
            return {}
        
        if not free_agents:
            return {"error": "No free agent data provided"}
        
        # Process free agents into a DataFrame
        fa_df = PlayerDataProcessor.players_to_dataframe(free_agents)
        
        # Get breakout candidates
        try:
            batter_candidates = self.savant_client.find_breakout_candidates(
                player_type="batter", 
                min_sample=min_sample_size
            )
            
            pitcher_candidates = self.savant_client.find_breakout_candidates(
                player_type="pitcher", 
                min_sample=min_sample_size
            )
            
            # Match candidates to free agents
            # A more robust implementation would use IDs, but we'll match by name for simplicity
            recommendations = {
                "batters": [],
                "pitchers": []
            }
            
            # Position groups for organizing recommendations
            position_groups = {
                "C": [],
                "1B": [],
                "2B": [],
                "3B": [],
                "SS": [],
                "OF": [],
                "SP": [],
                "RP": []
            }
            
            # Process batters
            for candidate in batter_candidates:
                candidate_name = candidate['name'].split(',')[0]  # Extract last name
                # Find matches in free agents
                matches = fa_df[fa_df['name'].str.contains(candidate_name, case=False)]
                
                if not matches.empty:
                    for _, match in matches.iterrows():
                        # Create recommendation record
                        rec = {
                            'name': match['name'],
                            'team': match['team'],
                            'positions': match['positions'],
                            'breakout_score': candidate['breakout_score'],
                            'reason': candidate['reason'],
                            'key_metrics': {
                                'xba': candidate['metrics'].get('xba'),
                                'xslg': candidate['metrics'].get('xslg'),
                                'barrel_rate': candidate['metrics'].get('barrel_rate')
                            }
                        }
                        
                        # Add to general batters list
                        recommendations["batters"].append(rec)
                        
                        # Add to position-specific lists
                        for pos in position_groups.keys():
                            if pos in match['positions']:
                                position_groups[pos].append(rec)
            
            # Process pitchers
            for candidate in pitcher_candidates:
                candidate_name = candidate['name'].split(',')[0]  # Extract last name
                # Find matches in free agents
                matches = fa_df[fa_df['name'].str.contains(candidate_name, case=False)]
                
                if not matches.empty:
                    for _, match in matches.iterrows():
                        # Create recommendation record
                        rec = {
                            'name': match['name'],
                            'team': match['team'],
                            'positions': match['positions'],
                            'breakout_score': candidate['breakout_score'],
                            'reason': candidate['reason'],
                            'key_metrics': {
                                'xera': candidate['metrics'].get('xera'),
                                'xwoba': candidate['metrics'].get('xwoba'),
                                'k_rate': candidate['metrics'].get('k_rate')
                            }
                        }
                        
                        # Add to general pitchers list
                        recommendations["pitchers"].append(rec)
                        
                        # Add to position-specific lists
                        for pos in position_groups.keys():
                            if pos in match['positions']:
                                position_groups[pos].append(rec)
            
            # Sort each position group by breakout score
            for pos, players in position_groups.items():
                position_groups[pos] = sorted(players, key=lambda x: x['breakout_score'], reverse=True)
            
            # Add position groups to recommendations
            recommendations.update(position_groups)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error finding waiver wire gems: {e}")
            return {"error": f"Failed to analyze waiver wire: {str(e)}"}