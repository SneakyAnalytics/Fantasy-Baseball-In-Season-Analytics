#!/usr/bin/env python
"""
Utility to find your team ID in the ESPN Fantasy Baseball league.
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.api.client import ESPNFantasyClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to find team IDs."""
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
    
    print(f"\nFound {len(teams)} teams in league: {client.league.settings.name}")
    print("\nTEAM ID LOOKUP")
    print("=" * 50)
    print(f"{'ID':<7} {'Team Name':<25} {'Owner':<25}")
    print("-" * 50)
    
    for team in teams:
        # Handle team name
        team_name = getattr(team, 'team_name', None)
        if team_name is None:
            # Try alternative attribute names
            team_name = getattr(team, 'name', 'Unknown Team')
        
        # Handle owners which may be a list or dictionary
        owner_name = "Unknown Owner"
        
        if hasattr(team, 'owners'):
            owners = team.owners
            if isinstance(owners, list):
                if owners and isinstance(owners[0], dict) and 'displayName' in owners[0]:
                    owner_name = owners[0]['displayName']
                elif owners:
                    owner_name = str(owners[0])
            else:
                owner_name = str(owners)
        
        print(f"{team.team_id:<7} {team_name[:25]:<25} {owner_name[:25]:<25}")
    
    print("\nINSTRUCTIONS:")
    print("1. Find your team in the list above")
    print("2. Add the following line to your config/settings.py file:")
    print("   MY_TEAM_ID = <your_team_id>  # Replace with your actual team ID")
    print("\nAfter setting MY_TEAM_ID, you'll be able to run the report scripts without")
    print("specifying the team ID as a command-line argument.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())