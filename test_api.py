import requests
import os

BRAWL_API_KEY = os.getenv("BRAWL_API_KEY")
club_tag = "88002RPQC"
player_tag = "RQ02QQ8V0"

r = requests.get(
    f"https://api.brawlstars.com/v1/clubs/%23{club_tag}/members",
    headers={"Authorization": f"Bearer {BRAWL_API_KEY}"}
)
print("Status:", r.status_code)
members = r.json().get("items", [])
print("Members count:", len(members))
for m in members:
    print(m["tag"], m["name"])
    if m["tag"].replace("#", "") == player_tag:
        print("^^^ ТВОЙ ТЕГ НАЙДЕН!")
