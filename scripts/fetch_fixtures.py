#!/usr/bin/env python3
import os, sys, json, datetime, requests

BASE = "https://v3.football.api-sports.io"
TEAM_NAME = "Liverpool"
COUNTRY = "England"

def _hdr(api_key):
    return {"x-apisports-key": api_key}

def _get(url, headers, params, timeout=30):
    r = requests.get(url, headers=headers, params=params, timeout=timeout)
    # If unauthorized/forbidden, surface a clear message
    if r.status_code in (401, 403):
        raise RuntimeError(
            f"API auth error {r.status_code}. "
            "Check X_APISPORTS_KEY (secret name/value) and that your plan allows /teams and /fixtures."
        )
    r.raise_for_status()
    return r

def find_team_id(api_key):
    """Find Liverpool team id with multiple fallbacks and clear errors."""
    # 1) If user provided TEAM_ID, trust it
    env_id = os.environ.get("TEAM_ID")
    if env_id:
        return int(env_id)

    # 2) Try /teams?search=...&country=England
    url = f"{BASE}/teams"
    headers = _hdr(api_key)

    def choose(resp):
        # prefer exact name + England
        for item in resp.get("response", []):
            t = item.get("team", {}) or {}
            c = item.get("country") or item.get("team", {}).get("country")
            if t.get("name","").lower() == TEAM_NAME.lower() and c == COUNTRY:
                return t.get("id")
        # then any “starts with” + England
        for item in resp.get("response", []):
            t = item.get("team", {}) or {}
            c = item.get("country") or item.get("team", {}).get("country")
            if t.get("name","").lower().startswith(TEAM_NAME.lower()) and c == COUNTRY:
                return t.get("id")
        # last resort: exact name ignoring country (risky but better than fail)
        for item in resp.get("response", []):
            t = item.get("team", {}) or {}
            if t.get("name","").lower() == TEAM_NAME.lower():
                return t.get("id")
        return None

    # attempt A: with country
    r = _get(url, headers, {"search": TEAM_NAME, "country": COUNTRY})
    tid = choose(r.json())
    if tid: return tid

    # attempt B: without country (some plans ignore the country filter)
    r = _get(url, headers, {"search": TEAM_NAME})
    tid = choose(r.json())
    if tid: return tid

    # Hard fallback: known id 40 (Liverpool, England) – verify with /teams?id=40
    r = _get(url, headers, {"id": 40})
    resp = r.json().get("response", [])
    if resp and (resp[0].get("team", {}).get("name","").lower().startswith("liverpool")):
        return 40

    # If we’re here, log raw snippets to help debug
    raise RuntimeError(
        "Liverpool team id not found after multiple strategies. "
        "Possible causes: invalid API key/plan or endpoint limits."
    )

def fetch_fixtures(api_key, team_id, date_from, date_to):
    url = f"{BASE}/fixtures"
    r = _get(url, _hdr(api_key), {
        "team": team_id, "from": date_from, "to": date_to, "timezone": "UTC"
    }, timeout=60)
    return r.json().get("response", [])

def main():
    api_key = os.environ.get("X_APISPORTS_KEY")
    if not api_key:
        print("Missing X_APISPORTS_KEY env var (add repo secret and map it in the workflow).", file=sys.stderr)
        sys.exit(1)

    DATE_FROM = os.environ.get("DATE_FROM", "2025-09-27")
    DATE_TO   = os.environ.get("DATE_TO",   "2026-03-31")

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
