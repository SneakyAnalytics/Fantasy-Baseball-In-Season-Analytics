from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import datetime


@dataclass
class Player:
    """Player data model."""
    
    playerId: int  # Changed from player_id to playerId to match ESPN API
    name: str
    proTeam: str  # Changed from team to proTeam to match ESPN API
    eligibleSlots: List[str]  # Changed from positions to eligibleSlots to match ESPN API
    stats: Dict[str, Any] = None
    
    @classmethod
    def from_espn(cls, espn_player):
        """
        Create a Player instance from an ESPN API player object.
        
        Args:
            espn_player: ESPN API player object
            
        Returns:
            Player: New Player instance
        """
        # Convert ESPN player to our model
        return cls(
            playerId=getattr(espn_player, 'playerId', 0),
            name=getattr(espn_player, 'name', 'Unknown'),
            proTeam=getattr(espn_player, 'proTeam', 'Unknown'),
            eligibleSlots=getattr(espn_player, 'eligibleSlots', []),
            stats=getattr(espn_player, 'stats', {})
        )

@dataclass
class Owner:
    """Team owner data model."""
    
    id: str
    display_name: str
    first_name: str
    last_name: str
    
    @classmethod
    def from_espn(cls, espn_owner):
        """Create an Owner instance from ESPN API owner data."""
        return cls(
            id=espn_owner.get('id', ''),
            display_name=espn_owner.get('displayName', ''),
            first_name=espn_owner.get('firstName', ''),
            last_name=espn_owner.get('lastName', '')
        )

@dataclass
class Team:
    """Team data model."""
    
    team_id: int
    name: str
    abbreviation: str
    owners: List[Owner]
    division_id: Optional[int] = None
    division_name: Optional[str] = None
    logo_url: Optional[str] = None
    standing: Optional[int] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    ties: Optional[int] = None
    roster: Optional[List[Player]] = None
    schedule: Optional[List[Any]] = None
    stats: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_espn(cls, espn_team):
        """
        Create a Team instance from an ESPN API team object.
        
        Args:
            espn_team: ESPN API team object
            
        Returns:
            Team: New Team instance
        """
        # Convert roster if available
        roster = None
        if hasattr(espn_team, 'roster') and espn_team.roster:
            roster = [Player.from_espn(player) for player in espn_team.roster]
        
        # Process owners
        owners = []
        if hasattr(espn_team, 'owners'):
            if isinstance(espn_team.owners, list):
                for owner_data in espn_team.owners:
                    if isinstance(owner_data, dict):
                        owners.append(Owner.from_espn(owner_data))
                    else:
                        owners.append(Owner(id='', display_name=str(owner_data), first_name='', last_name=''))
            else:
                owners.append(Owner(id='', display_name=str(espn_team.owners), first_name='', last_name=''))
        
        # Get standing information
        standing = getattr(espn_team, 'standing', None)
        wins = getattr(espn_team, 'wins', 0)
        losses = getattr(espn_team, 'losses', 0)
        ties = getattr(espn_team, 'ties', 0)
        
        # Get division information
        division_id = getattr(espn_team, 'division_id', None)
        division_name = getattr(espn_team, 'division_name', None)
            
        return cls(
            team_id=espn_team.team_id,
            name=espn_team.team_name,
            abbreviation=espn_team.team_abbrev,
            owners=owners,
            division_id=division_id,
            division_name=division_name,
            logo_url=getattr(espn_team, 'logo_url', None),
            standing=standing,
            wins=wins,
            losses=losses,
            ties=ties,
            roster=roster,
            schedule=getattr(espn_team, 'schedule', None),
            stats=getattr(espn_team, 'stats', None)
        )

@dataclass
class Matchup:
    """Weekly matchup data model."""
    
    week: int
    team_1: Team
    team_2: Team
    team_1_score: float
    team_2_score: float
    winner: Optional[Team] = None
    
    @classmethod
    def from_espn(cls, espn_matchup, week):
        """
        Create a Matchup instance from an ESPN API matchup object.
        
        Args:
            espn_matchup: ESPN API matchup object
            week: Week number
            
        Returns:
            Matchup: New Matchup instance
        """
        team_1 = Team.from_espn(espn_matchup.home_team)
        team_2 = Team.from_espn(espn_matchup.away_team)
        
        # Determine winner
        winner = None
        if espn_matchup.home_score > espn_matchup.away_score:
            winner = team_1
        elif espn_matchup.away_score > espn_matchup.home_score:
            winner = team_2
            
        return cls(
            week=week,
            team_1=team_1,
            team_2=team_2,
            team_1_score=espn_matchup.home_score,
            team_2_score=espn_matchup.away_score,
            winner=winner
        )

@dataclass
class League:
    """League data model."""
    
    league_id: int
    name: str
    year: int
    teams: List[Team]
    settings: Dict[str, Any]