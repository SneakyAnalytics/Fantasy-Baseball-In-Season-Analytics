#!/usr/bin/env python
"""
Debug script to identify team ID issues in the ESPN Fantasy API.
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.api.client import ESPNFantasyClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Debug function to examine team objects."""
    print("Connecting to ESPN Fantasy Baseball API...")
    
    # Connect to ESPN API
    client = ESPNFantasyClient(
        league_id=settings.LEAGUE_ID,
        year=settings.YEAR,
        espn_s2=settings.ESPN_S2,
        swid=settings.SWID
    )
    
    if not client.connect():
        print("Failed to connect to ESPN API. Please check your credentials.")
        return 1
    
    # Get teams
    teams = client.get_teams()
    
    if not teams:
        print("No teams found in the league.")
        return 1
    
    print(f"\nDetailed Team Information for {client.league.settings.name}")
    print("=" * 60)
    
    for team in teams:
        print(f"\nTeam: {getattr(team, 'team_name', 'Unknown')}")
        print("-" * 40)
        
        # Print all attributes for debugging
        for attr_name in dir(team):
            # Skip private and method attributes
            if attr_name.startswith('_') or callable(getattr(team, attr_name)):
                continue
                
            attr_value = getattr(team, attr_name)
            print(f"{attr_name}: {attr_value}")
        
        # Check specifically for team_id and id attributes
        team_id = getattr(team, 'team_id', None)
        alt_id = getattr(team, 'id', None)
        
        if team_id != alt_id and alt_id is not None:
            print(f"Note: This team has both team_id ({team_id}) and id ({alt_id}) attributes!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())