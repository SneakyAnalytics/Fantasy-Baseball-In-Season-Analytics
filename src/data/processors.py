# src/data/processors.py
import pandas as pd
import logging
from typing import List, Dict, Any

from src.data.models import Team, Player

logger = logging.getLogger(__name__)

class TeamDataProcessor:
    """Process team data for analysis."""

    @staticmethod
    def teams_to_dataframe(teams: List[Team]) -> pd.DataFrame:
        """
        Convert a list of Team objects to a pandas DataFrame.
        
        Args:
            teams: List of Team objects
            
        Returns:
            pd.DataFrame: DataFrame containing team data
        """
        team_data = []
        for team in teams:
            # First, let's examine what attributes are actually available
            team_dict = {}
            
            # Handle the team name/ID
            team_dict['team_id'] = getattr(team, 'team_id', None)
            team_dict['name'] = getattr(team, 'team_name', None)  # Use team_name instead of name
            team_dict['abbreviation'] = getattr(team, 'team_abbrev', None)
            
            # Handle owners - could be a dictionary or something else
            owners_info = getattr(team, 'owners', None)
            if owners_info:
                if isinstance(owners_info, list) and isinstance(owners_info[0], dict):
                    team_dict['owner_name'] = owners_info[0].get('displayName', 'Unknown')
                else:
                    team_dict['owner_name'] = str(owners_info)
            else:
                team_dict['owner_name'] = 'Unknown'
            
            # Other team attributes
            team_dict['division_id'] = getattr(team, 'division_id', None)
            team_dict['division_name'] = getattr(team, 'division_name', None)
            team_dict['standing'] = getattr(team, 'standing', None)
            team_dict['wins'] = getattr(team, 'wins', 0)
            team_dict['losses'] = getattr(team, 'losses', 0)
            team_dict['ties'] = getattr(team, 'ties', 0)
            
            # Calculate win percentage
            total_games = team_dict['wins'] + team_dict['losses']
            team_dict['win_percentage'] = (team_dict['wins'] / total_games * 100) if total_games > 0 else 0
            
            # Roster size
            roster = getattr(team, 'roster', None)
            team_dict['roster_size'] = len(roster) if roster else 0
            
            # Logo URL
            team_dict['logo_url'] = getattr(team, 'logo_url', None)
            
            team_data.append(team_dict)
        
        return pd.DataFrame(team_data)
    
    @staticmethod
    def calculate_team_stats(teams: List[Team]) -> Dict[str, Any]:
        """
        Calculate various statistics for teams.
        
        Args:
            teams: List of Team objects
            
        Returns:
            dict: Dictionary containing team statistics
        """
        df = TeamDataProcessor.teams_to_dataframe(teams)
        
        stats = {
            'total_teams': len(teams),
            'avg_wins': df['wins'].mean(),
            'avg_losses': df['losses'].mean(),
            'max_wins': df['wins'].max(),
            'min_wins': df['wins'].min(),
            'standings': df.sort_values('standing')[['name', 'standing', 'wins', 'losses']].to_dict('records')
        }
        
        # Calculate division stats if available
        if df['division_id'].notna().any():
            division_stats = df.groupby('division_name').agg({
                'wins': 'mean',
                'losses': 'mean',
                'team_id': 'count'
            }).rename(columns={'team_id': 'team_count'}).to_dict('index')
            
            stats['division_stats'] = division_stats
        
        return stats

class PlayerDataProcessor:
    """Process player data for analysis."""
    
    @staticmethod
    def players_to_dataframe(players: List[Player]) -> pd.DataFrame:
        """
        Convert a list of Player objects to a pandas DataFrame.
        
        Args:
            players: List of Player objects
            
        Returns:
            pd.DataFrame: DataFrame containing player data
        """
        player_data = []
        for player in players:
            # Use getattr to safely access attributes with fallbacks
            player_dict = {
                'player_id': getattr(player, 'playerId', None),
                'name': getattr(player, 'name', 'Unknown'),
                'team': getattr(player, 'proTeam', getattr(player, 'team', 'Unknown')),
                'positions': ', '.join(str(pos) for pos in getattr(player, 'eligibleSlots', [])) 
                            if hasattr(player, 'eligibleSlots') else '',
            }
            
            # Add stats if available
            stats = getattr(player, 'stats', None)
            if stats and isinstance(stats, dict):
                for stat_type, stat_values in stats.items():
                    if isinstance(stat_values, dict):
                        for stat_name, stat_value in stat_values.items():
                            # Only add the stat if it's a simple value, not another dictionary
                            if not isinstance(stat_value, dict) and not isinstance(stat_value, list):
                                stat_key = f'{stat_type}_{stat_name}'
                                player_dict[stat_key] = stat_value
                    elif not isinstance(stat_values, dict) and not isinstance(stat_values, list):
                        # If stat_values is not a dictionary or list, add it directly
                        player_dict[stat_type] = stat_values
            
            player_data.append(player_dict)
        
        return pd.DataFrame(player_data)