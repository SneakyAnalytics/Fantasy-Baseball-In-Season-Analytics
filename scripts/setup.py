#!/usr/bin/env python
"""
Setup script for ESPN Fantasy Baseball Analyzer.
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.api.client import ESPNFantasyClient
from src.api.auth import ESPNAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('espn_fantasy.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main setup function."""
    print("Setting up ESPN Fantasy Baseball Analyzer...")
    
    # Create cache directory if it doesn't exist
    if not os.path.exists(settings.CACHE_DIR):
        os.makedirs(settings.CACHE_DIR)
        print(f"Created cache directory: {settings.CACHE_DIR}")
    
    # Test connection to ESPN API
    client = ESPNFantasyClient(
        league_id=settings.LEAGUE_ID,
        year=settings.YEAR,
        espn_s2=settings.ESPN_S2,
        swid=settings.SWID
    )
    
    if client.connect():
        print(f"Successfully connected to ESPN Fantasy Baseball league {settings.LEAGUE_ID}")
        
        # Get basic league info
        league_info = client.get_league_info()
        print(f"League Name: {league_info.get('name', 'Unknown')}")
        print(f"Teams: {league_info.get('size', 'Unknown')}")
        print(f"Scoring Type: {league_info.get('scoring_type', 'Unknown')}")
        
        # Let's also examine and print what attributes are actually available
        print("\nExamining league settings structure...")
        settings_dir = dir(client.league.settings)
        print("Available settings attributes:", ', '.join(attr for attr in settings_dir if not attr.startswith('_')))
        
        # Get teams
        teams = client.get_teams()
        print(f"\nFound {len(teams)} teams:")
        for team in teams:
            # Handle potential differences in API structure
            team_name = getattr(team, 'team_name', None)
            if team_name is None:
                # Try alternative attribute names
                team_name = getattr(team, 'name', 'Unknown Team')
            
            # Handle owners which may be a list
            owner_info = getattr(team, 'owners', None)
            if owner_info is None:
                # Try alternative attribute
                owner_info = getattr(team, 'owner', 'Unknown Owner')
            
            # If owners is a list, get the first one
            if isinstance(owner_info, list) and len(owner_info) > 0:
                owner = owner_info[0]
            else:
                owner = str(owner_info)
            
            print(f"  - {team_name} (Owner: {owner})")

        # Also add debugging to print all available team attributes
        if teams and len(teams) > 0:
            first_team = teams[0]
            print("\nTeam object structure:")
            team_attrs = [attr for attr in dir(first_team) if not attr.startswith('_')]
            print("Available team attributes:", ', '.join(team_attrs))
    else:
        print("Failed to connect to ESPN API. Please check your credentials.")
        return 1
    
    print("\nSetup complete! You're ready to start analyzing your fantasy baseball league.")
    return 0

if __name__ == "__main__":
    sys.exit(main())