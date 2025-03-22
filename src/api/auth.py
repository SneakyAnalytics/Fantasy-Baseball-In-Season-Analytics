import os
import json
import datetime
import logging

logger = logging.getLogger(__name__)

class ESPNAuth:
    """Utilities for handling ESPN authentication."""
    
    def __init__(self, credentials_file='.espn_credentials'):
        """
        Initialize the authentication utility.
        
        Args:
            credentials_file (str): Path to the credentials file
        """
        self.credentials_file = credentials_file
        
    def load_credentials(self):
        """
        Load ESPN credentials from file.
        
        Returns:
            dict: Dictionary containing SWID and ESPN_S2 cookies
        """
        if not os.path.exists(self.credentials_file):
            logger.warning(f"Credentials file {self.credentials_file} not found")
            return None
            
        try:
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
                
            # Check if credentials have expired
            if 'expiry' in credentials:
                expiry = datetime.datetime.fromisoformat(credentials['expiry'])
                if expiry < datetime.datetime.now():
                    logger.warning("Credentials have expired")
                    return None
                    
            return credentials
        except Exception as e:
            logger.error(f"Failed to load credentials: {str(e)}")
            return None
            
    def save_credentials(self, espn_s2, swid, expiry_days=30):
        """
        Save ESPN credentials to file.
        
        Args:
            espn_s2 (str): ESPN S2 cookie
            swid (str): SWID cookie
            expiry_days (int): Number of days until credentials expire
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            expiry = datetime.datetime.now() + datetime.timedelta(days=expiry_days)
            
            credentials = {
                'ESPN_S2': espn_s2,
                'SWID': swid,
                'expiry': expiry.isoformat()
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(credentials, f)
                
            logger.info(f"Credentials saved to {self.credentials_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {str(e)}")
            return False