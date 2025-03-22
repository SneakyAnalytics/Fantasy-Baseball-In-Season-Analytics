import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ESPN API settings
LEAGUE_ID = int(os.getenv('LEAGUE_ID'))
YEAR = int(os.getenv('YEAR'))
ESPN_S2 = os.getenv('ESPN_S2', None)
SWID = os.getenv('SWID', None)

# Data settings
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

# Application settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'