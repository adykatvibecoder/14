import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BRAWL_API_KEY = os.getenv("BRAWL_API_KEY")
VERIFY_CLUB_TAG = os.getenv("VERIFY_CLUB_TAG")