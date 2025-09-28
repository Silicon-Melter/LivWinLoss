#!/usr/bin/env python3
import os, sys, json, datetime, requests

BASE = "https://v3.football.api-sports.io"
# We’ll lock team lookup to Liverpool (England) once and reuse the ID.
TEAM_NAME = "Liverpool"
COUNTRY = "England"

# Fetch Liverpool team id
def find_team_id(api_key):
    r = requests.get(f"{BASE}/teams",
        headers={"x-apisports-key": api_key},
        params={"search": TEAM_NAME, "country": COUNTRY},
        timeout=30)
    r.raise_for_status()
    for item in r.json().get("response", []):
        t = item.get("team", {})
        if t.get("name","").lower().startswith("liverpool"):
            return t["id"]
    raise RuntimeError("Liverpool team id not found")

# Pull fixtures for a wide range that includes your window
def fetch_fixtures(api_key, team_id, date_from, date_to):
    params = {"team": team_id, "from": date_from, "to": date_to, "timezone": "UTC"}
    r = requests.get(f"{BASE}/fixtures",
        headers={"x-apisports-key": api_key},
        params=params, timeout=60)
    r.raise_for_status()
    return r.json().get("response", [])

def main():
    api_key = os.environ.get("X_APISPORTS_KEY")
    if not api_key:
        print("Missing X_APISPORTS_KEY", file=sys.stderr)
        sys.exit(1)

    # Your fixed window
    DATE_FROM = os.environ.get("DATE_FROM", "2025-09-01")  # a little buffer
    DATE_TO   = os.environ.get("DATE_TO",   "2026-04-15")  # a little buffer

    team_id = find_team_id(api_key)
    fixtures = fetch_fixtures(api_key, team_id, DATE_FROM, DATE_TO)

    out = {
        "team_id": team_id,
        "from": DATE_FROM,
        "to": DATE_TO,
        "generated_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "response": fixtures
    }

    os.makedirs("data", exist_ok=True)
    with open("data/fixtures.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote data/fixtures.json with {len(fixtures)} fixtures")

if __name__ == "__main__":
    main()
