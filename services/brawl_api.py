import requests
from config import BRAWL_API_KEY

HEADERS = {"Authorization": f"Bearer {BRAWL_API_KEY}"}
BASE_URL = "https://api.brawlstars.com/v1"

def get_player(tag: str):
    tag_clean = tag.replace("#", "").strip()
    url = f"{BASE_URL}/players/%23{tag_clean}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    return None

def get_club_members(club_tag: str):
    tag_clean = club_tag.replace("#", "").strip()
    url = f"{BASE_URL}/clubs/%23{tag_clean}/members"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("items", [])
    return []

def is_tag_in_club(tag: str, club_tag: str) -> bool:
    members = get_club_members(club_tag)
    tag_clean = tag.replace("#", "").strip().upper()
    for member in members:
        member_tag = member["tag"].replace("#", "").strip().upper()
        if member_tag == tag_clean:
            return True
    return False
