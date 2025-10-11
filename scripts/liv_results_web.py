#!/usr/bin/env python3
import re, sys, json
from datetime import date, datetime, timezone
from typing import List, Dict, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparse

from zoneinfo import ZoneInfo

TEAM_ID = 364  # Liverpool (ESPN)
START_DATE = date(2025, 9, 27)  # fixed start
TODAY_UTC = datetime.now(ZoneInfo("Asia/Bangkok")).date()

CANDIDATE_URLS = [
    f"https://www.espn.com/soccer/team/results/_/id/{TEAM_ID}/eng.liverpool",
    f"https://www.espn.com/soccer/team/results/_/id/{TEAM_ID}/liverpool",
    f"https://www.espn.com/soccer/team/results/_/id/{TEAM_ID}/season/{START_DATE.year}",
    f"https://www.espn.com/soccer/team/results/_/id/{TEAM_ID}",
]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.espn.com/soccer/",
}

SCORE_RE = re.compile(r"(\d+)\s*[-–]\s*(\d+)", re.I)

def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text

def parse_row_generic(tr: BeautifulSoup) -> Optional[Dict]:
    tds = tr.find_all("td")
    if not tds:
        return None

    # Date (first cell)
    raw_date = tds[0].get_text(" ", strip=True)
    try:
        d = dtparse.parse(raw_date, fuzzy=True).date()
    except Exception:
        return None  # header-ish row

    # Home/Away via team links (first=home, last=away)
    team_links = tr.select('a[href*="/team/"]')
    names = [a.get_text(strip=True) for a in team_links if a.get_text(strip=True)]
    if len(names) < 2:
        return None
    home_team, away_team = names[0], names[-1]

    # Score anywhere in row
    row_text = tr.get_text(" ", strip=True)
    m = SCORE_RE.search(row_text)
    if m:
        hg, ag = int(m.group(1)), int(m.group(2))
    else:
        # no score => future/invalid row
        return None

    up = row_text.upper()
    if   "FT"  in up: status = "FT"
    elif "PEN" in up: status = "PEN"
    elif "AET" in up: status = "AET"
    else:             status = "FT"

    comp_text = tds[-1].get_text(" ", strip=True)

    # W/D/L relative to Liverpool
    home_is_lfc = home_team.lower().startswith("liverpool")
    away_is_lfc = away_team.lower().startswith("liverpool")
    if not (home_is_lfc or away_is_lfc):
        return None  # shouldn't happen on the team page

    gf, ga = (hg, ag) if home_is_lfc else (ag, hg)
    if gf > ga: res = "W"
    elif gf < ga: res = "L"
    else:        res = "D"  # regulation draw; treat pens separately if you prefer

    return {
        "date": d,
        "home": home_team,
        "away": away_team,
        "competition": comp_text,
        "score_text": f"{hg} - {ag}",
        "status": status,
        "result": res
    }

def scrape_results() -> Tuple[List[Dict], Dict]:
    last_diag = {}
    for url in CANDIDATE_URLS:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        collected = []
        diag = {"url": url, "tables_checked": 0, "rows_parsed": 0}

        for tbl in soup.select("table.Table, table[role='table']"):
            diag["tables_checked"] += 1
            tbody = tbl.find("tbody")
            if not tbody:
                continue
            for tr in tbody.find_all("tr"):
                row = parse_row_generic(tr)
                if row:
                    collected.append(row)

        if collected:
            diag["rows_parsed"] = len(collected)
            return collected, diag
        last_diag = diag
    raise RuntimeError(f"No usable rows from ESPN. Last diagnostics: {last_diag}")

def main():
    try:
        rows, diag = scrape_results()
    except Exception as e:
        print(f"Scrape failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Filter START_DATE → TODAY_UTC
    window = [r for r in rows if isinstance(r.get("date"), date)
              and START_DATE <= r["date"] <= TODAY_UTC]

    # Sort by date
    window.sort(key=lambda r: r["date"])

    # Tally finished
    w = sum(1 for r in window if r["result"] == "W")
    d = sum(1 for r in window if r["result"] == "D")
    l = sum(1 for r in window if r["result"] == "L")

    out = {
        "from": START_DATE.isoformat(),
        "to": TODAY_UTC.isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": {"wins": w, "draws": d, "losses": l},
        "rows": [
            {
                **r,
                "date": r["date"].isoformat(),
            } for r in window
        ],
        "source_url": diag.get("url"),
    }

    # Write JSON for the website
    import os, pathlib
    pathlib.Path("data").mkdir(parents=True, exist_ok=True)
    with open("data/fixtures.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote data/fixtures.json with {len(window)} rows | W:{w} D:{d} L:{l} | Source: {diag.get('url')}")

if __name__ == "__main__":
    import sys
    main()
