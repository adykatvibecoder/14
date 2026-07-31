import requests
import os

BRAWL_API_KEY = os.getenv("BRAWL_API_KEY")
tag = "RQ02QQ8V0"

r = requests.get(
    f"https://api.brawlstars.com/v1/players/%23{tag}",
    headers={"Authorization": f"Bearer {BRAWL_API_KEY}"}
)
print("Status:", r.status_code)
print("Response:", r.text[:200])
