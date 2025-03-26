# src/data/adapters.py
"""
Adapter classes to help normalize data from the ESPN API.
"""

from src.data.models import Team, Matchup

class SimpleMatchup:
    """
    A simplified matchup class that can be used when full ESPN API data is not available.
    This is especially useful at the beginning of the season or for future matchups.
    """
    
    def __init__(self, team1, team2, week=1):
        """
        Initialize a simplified matchup.
        
        Args:
            team1: First team in matchup
            team2: Second team in matchup
            week: Week number (default: 1)
        """
        self.team_1 = team1
        self.team_2 = team2
        self.team_1_score = 0.0
        self.team_2_score = 0.0
        self.week = week
        self.home_team = team1  # For compatibility with ESPN API structure
        self.away_team = team2  # For compatibility with ESPN API structure
        self.home_score = 0.0   # For compatibility with ESPN API structure
        self.away_score = 0.0   # For compatibility with ESPN API structure
        
    @classmethod
    def from_schedule_entry(cls, schedule_entry, my_team_id):
        """
        Create a SimpleMatchup from a schedule entry.
        
        Args:
            schedule_entry: Entry from team.schedule
            my_team_id: ID of the user's team
            
        Returns:
            SimpleMatchup: New matchup object
        """
        # Try to extract teams from the schedule entry
        team1 = None
        team2 = None
        
        # Attempt different ways to get the teams
        if hasattr(schedule_entry, 'home_team') and hasattr(schedule_entry, 'away_team'):
            team1 = schedule_entry.home_team
            team2 = schedule_entry.away_team
        else:
            # Try to find teams as attributes
            for attr_name in dir(schedule_entry):
                if attr_name.startswith('_'):
                    continue
                    
                attr_value = getattr(schedule_entry, attr_name)
                if hasattr(attr_value, 'team_id'):
                    if team1 is None:
                        team1 = attr_value
                    else:
                        team2 = attr_value
                        break
        
        # Ensure the user's team is team_1
        if team1 and team2:
            if str(team1.team_id) != str(my_team_id):
                team1, team2 = team2, team1
                
        return cls(team1, team2)

class SimplePlayer:
    """
    A simplified player class that can be used when full ESPN API data is not available.
    """
    
    def __init__(self, name, team, position, projected_points=0.0):
        """
        Initialize a simplified player.
        
        Args:
            name: Player name
            team: MLB team
            position: Position(s)
            projected_points: Projected fantasy points
        """
        self.name = name
        self.proTeam = team
        self.eligibleSlots = [position] if isinstance(position, str) else position
        self.stats = {'0_projected_points': projected_points}
        self.playerId = 0  # Dummy ID