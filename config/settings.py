import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ESPN API settings
LEAGUE_ID = int(os.getenv('LEAGUE_ID'))
YEAR = int(os.getenv('YEAR'))
ESPN_S2 = os.getenv('ESPN_S2', None)
SWID = os.getenv('SWID', None)

# Team ID and Email List
TEAM_ID = os.getenv('TEAM_ID', None)
EMAIL_LIST = os.getenv('EMAIL_LIST', '').split(',') if os.getenv('EMAIL_LIST') else []
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', None)
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', None)

# Data settings
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

# Application settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Team settings
MY_TEAM_ID = TEAM_ID  # Replace with your team ID (you'll find this from running setup.py)
MY_TEAM_NAME = None  # Optional, will be fetched from API if not provided

# League settings (based on your league configuration)
MAX_PITCHER_STARTS = 12
MAX_ACQUISITIONS_PER_MATCHUP = 8

# Email notification settings
EMAIL_ENABLED = False
EMAIL_FROM = 'ljacobrobinsonl@gmail.com'  # Your email address
EMAIL_TO = [EMAIL_LIST]  # List of email recipients
EMAIL_SUBJECT_PREFIX = '[Fantasy Baseball] '
EMAIL_SMTP_SERVER = 'smtp.gmail.com'  # Example for Gmail
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = EMAIL_USERNAME  # Your email username
EMAIL_PASSWORD = EMAIL_PASSWORD  # Your email password or app password
# Note: For Gmail, you may need to create an App Password

# Report settings
REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
DAILY_REPORT_ENABLED = True
WEEKLY_PREVIEW_ENABLED = True