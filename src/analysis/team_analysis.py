# src/analysis/team_analysis.py
from typing import List, Dict, Any
import pandas as pd
import logging

from src.data.models import Team
from src.data.processors import TeamDataProcessor

logger = logging.getLogger(__name__)

class TeamAnalyzer:
    """Analyze team performance in a fantasy baseball league."""
    
    def __init__(self, teams: List[Team]):
        """
        Initialize with a list of teams.
        
        Args:
            teams: List of Team objects
        """
        self.teams = teams
        self.team_df = TeamDataProcessor.teams_to_dataframe(teams)
        
    def get_standings(self) -> pd.DataFrame:
        """
        Get current league standings.
        
        Returns:
            pd.DataFrame: DataFrame sorted by standing
        """
        return self.team_df.sort_values('standing')[
            ['name', 'owner_name', 'standing', 'wins', 'losses', 'win_percentage']
        ]
    
    def get_division_standings(self) -> Dict[str, pd.DataFrame]:
        """
        Get standings by division.
        
        Returns:
            dict: Dictionary with division names as keys and DataFrames as values
        """
        if 'division_name' not in self.team_df.columns or self.team_df['division_name'].isna().all():
            logger.warning("No division information available")
            return {}
        
        divisions = {}
        for division_name, group in self.team_df.groupby('division_name'):
            if division_name:  # Skip None/NaN division names
                divisions[division_name] = group.sort_values('standing')[
                    ['name', 'owner_name', 'standing', 'wins', 'losses', 'win_percentage']
                ]
        
        return divisions
    
    def get_team_by_name(self, name: str) -> pd.Series:
        """
        Get team by name.
        
        Args:
            name: Team name
            
        Returns:
            pd.Series: Team data
        """
        # Use the column name from the DataFrame, not the original team attribute
        matches = self.team_df[self.team_df['name'].str.contains(name, case=False)]
        if len(matches) == 0:
            logger.warning(f"No team found with name containing '{name}'")
            return pd.Series()
        return matches.iloc[0]
    
    def get_team_comparison(self, team_name1: str, team_name2: str) -> Dict[str, Any]:
        """
        Compare two teams.
        
        Args:
            team_name1: First team name
            team_name2: Second team name
            
        Returns:
            dict: Comparison results
        """
        team1 = self.get_team_by_name(team_name1)
        team2 = self.get_team_by_name(team_name2)
        
        if team1.empty or team2.empty:
            return {"error": "One or both teams not found"}
        
        comparison = {
            "team1": team1['name'],
            "team2": team2['name'],
            "standings": {
                "team1_standing": team1['standing'],
                "team2_standing": team2['standing'],
                "difference": team1['standing'] - team2['standing']
            },
            "records": {
                "team1_record": f"{team1['wins']}-{team1['losses']}",
                "team2_record": f"{team2['wins']}-{team2['losses']}",
                "win_diff": team1['wins'] - team2['wins']
            }
        }
        
        return comparison