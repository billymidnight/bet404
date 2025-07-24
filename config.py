"""Promo Conversion Hub."""

import pathlib
import os
from dotenv import load_dotenv  



PROJECT_ROOT = pathlib.Path(__file__).resolve().parent  
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
GPT_API_KEY = os.getenv("GPT_API_KEY")
print(f"The gpt api key is {GPT_API_KEY}")

APPLICATION_ROOT = '/'

SECRET_KEY = b'\xa3\xb2\xd8&\x1b\xe9\x85\x7fJ\x8b\x19\xf6\xda\xb7\xe2\xe1\x9b\xce'

LEAGUE_ROOT = pathlib.Path(__file__).resolve().parent
UPLOAD_FOLDER = LEAGUE_ROOT / 'app' / 'static' / 'images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# Database file is var/football_league.sqlite3
DATABASE_FILENAME = LEAGUE_ROOT / 'trajanbet' / 'var' / 'trajanbet.sqlite3'
