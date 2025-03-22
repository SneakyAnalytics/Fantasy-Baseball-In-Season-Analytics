from espn_api.baseball import League
import logging

logger = logging.getLogger(__name__)

class ESPNFantasyClient:
    """Client for interacting with the ESPN Fantasy Baseball API."""
    
    def __init__(self, league_id, year, espn_s2=None, swid=None):
        """
        Initialize the ESPN Fantasy Baseball client.
        
        Args:
            league_id (int): ESPN league ID
            year (int): Season year
            espn_s2 (str, optional): ESPN S2 cookie for private leagues
            swid (str, optional): SWID cookie for private leagues
        """
        self.league_id = league_id
        self.year = year
        self.espn_s2 = espn_s2
        self.swid = swid
        self.league = None
        
    def connect(self):
        """
        Establish connection to the ESPN Fantasy API.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            self.league = League(
                league_id=self.league_id,
                year=self.year,
                espn_s2=self.espn_s2,
                swid=self.swid
            )
            logger.info(f"Connected to ESPN Fantasy Baseball league {self.league_id} for year {self.year}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ESPN API: {str(e)}")
            return False
    
    def get_league_info(self):
        """
        Get basic information about the league.
        
        Returns:
            dict: League information including settings
        """
        if not self.league:
            self.connect()
            
        # Create a more robust response that checks for attribute existence
        league_info = {
            'name': getattr(self.league.settings, 'name', 'Unknown'),
            'size': getattr(self.league.settings, 'team_count', 0),
            'scoring_type': getattr(self.league.settings, 'scoring_type', 'Unknown')
        }
        
        # Try to get roster positions if available
        try:
            league_info['roster_positions'] = self.league.settings.roster
        except AttributeError:
            league_info['roster_positions'] = {}
        
        # Try to get stat categories if available
        try:
            league_info['stat_categories'] = self.league.settings.stat_categories
        except AttributeError:
            league_info['stat_categories'] = {}
        
        return league_info
    
    def get_teams(self):
        """
        Retrieve all teams in the league.
        
        Returns:
            list: List of Team objects
        """
        if not self.league:
            self.connect()
        
        # Let's print some debugging info about the team object structure
        if self.league.teams and len(self.league.teams) > 0:
            first_team = self.league.teams[0]
            team_attrs = [attr for attr in dir(first_team) if not attr.startswith('_')]
            logger.debug(f"Team attributes: {', '.join(team_attrs)}")
        
        return self.league.teams
    
    def get_team_by_id(self, team_id):
        """
        Get a specific team by ID.
        
        Args:
            team_id (int): Team ID
            
        Returns:
            Team: Team object if found, None otherwise
        """
        if not self.league:
            self.connect()
            
        for team in self.league.teams:
            if team.team_id == team_id:
                return team
        return None
    
    def get_free_agents(self, size=50, position=None):
        """
        Get list of free agents.
        
        Args:
            size (int): Number of free agents to return
            position (str, optional): Filter by position
            
        Returns:
            list: List of Player objects
        """
        if not self.league:
            self.connect()
        return self.league.free_agents(size=size, position=position)
    
    def get_rostered_players(self):
        """
        Get all players rostered in the league.
        
        Returns:
            list: List of rostered Player objects
        """
        if not self.league:
            self.connect()
        rostered = []
        for team in self.league.teams:
            rostered.extend(team.roster)
        return rostered
    
    def get_player_by_id(self, player_id):
        """
        Get player by ID.
        
        Args:
            player_id (int): Player ID
            
        Returns:
            Player: Player object if found, None otherwise
        """
        if not self.league:
            self.connect()
            
        rostered = self.get_rostered_players()
        for player in rostered:
            if player.playerId == player_id:
                return player
                
        # If not found in rostered players, check free agents
        free_agents = self.get_free_agents(size=500)  # Get a large batch of free agents
        for player in free_agents:
            if player.playerId == player_id:
                return player
                
        return None
    
    def get_matchups(self, week=None):
        """
        Get matchups for a specific week.
        
        Args:
            week (int, optional): Week number. If None, returns current week.
            
        Returns:
            list: List of matchup objects
        """
        if not self.league:
            self.connect()
        return self.league.box_scores(matchup_period=week)
    
    def get_standings(self):
        """
        Get current league standings.
        
        Returns:
            list: Teams sorted by rank
        """
        if not self.league:
            self.connect()
        return sorted(self.league.teams, key=lambda x: x.standing)