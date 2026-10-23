#!/usr/bin/env python3
"""Fetch daily sports scores and upcoming fixtures and inject them into a CleanYourTV theme.

Usage:
    python3 tools/sports_ticker.py themes/ghibli-dark
    python3 tools/sports_ticker.py themes/ghibli-dark --push
    python3 tools/sports_ticker.py themes/ghibli-dark --sports "Soccer,Fighting"
"""
import argparse
from datetime import date, datetime, timezone
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request


DEFAULT_API_KEY = "123"
DEFAULT_SPORTS = ["Soccer", "Fighting"]
DEFAULT_POPULAR_LEAGUES = ["4328", "4335", "4350", "4443", "4445", "4480"]
MONTH_NAMES = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def format_date_label(date_str, today_str=None):
    if not date_str:
        return ""
    date_str = date_str.strip()
    if today_str and date_str == today_str:
        return "Today"
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            month = int(parts[1])
            day = int(parts[2])
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{MONTH_NAMES[month]} {day}"
    except (ValueError, IndexError):
        pass
    return date_str


def local_tz():
    return datetime.now().astimezone().tzinfo


def localize_kickoff(date_str, time_str, tz):
    """TheSportsDB reports dateEvent and strTime in UTC. Return them in tz, unchanged when the time is unknown."""
    if not date_str or len(time_str) < 5 or time_str[2] != ":" or time_str[:5] == "00:00":
        return date_str, time_str
    try:
        utc = datetime.fromisoformat(f"{date_str}T{time_str[:5]}").replace(tzinfo=timezone.utc)
    except ValueError:
        return date_str, time_str
    local = utc.astimezone(tz)
    return local.date().isoformat(), local.strftime("%H:%M")


def is_event_recent(ev, today=None, max_past_days=1):
    if today is None:
        today = date.today()
    elif isinstance(today, str):
        try:
            today = date.fromisoformat(today.strip())
        except ValueError:
            today = date.today()
    date_str = (ev.get("dateEvent") or ev.get("strDate") or "").strip()
    if not date_str or date_str.lower() == "null":
        return True
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            ev_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
            if (ev_date - today).days < -max_past_days:
                return False
    except (ValueError, IndexError):
        pass
    return True


def fetch_league_events(league_id, api_key=DEFAULT_API_KEY):
    events = []
    for endpoint in ("eventspastleague.php", "eventsnextleague.php"):
        url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/{endpoint}?id={league_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 CleanYourTV/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                events.extend(parse_events(data))
        except Exception as e:
            print(f"Warning: failed to fetch league {league_id} ({endpoint}): {e}", file=sys.stderr)
        time.sleep(0.8)
    return events


def fetch_all_leagues(leagues, api_key=DEFAULT_API_KEY):
    combined = []
    for lid in leagues:
        events = fetch_league_events(str(lid).strip(), api_key=api_key)
        combined.extend(events)
    return combined


def fetch_sports_day(sport, query_date=None, api_key=DEFAULT_API_KEY):
    if query_date is None:
        query_date = date.today().strftime("%Y-%m-%d")
    encoded_sport = urllib.parse.quote(sport)
    url = f"https://www.thesportsdb.com/api/v1/json/{api_key}/eventsday.php?d={query_date}&s={encoded_sport}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 CleanYourTV/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return parse_events(data)
    except Exception as e:
        print(f"Warning: failed to fetch sports day for {sport}: {e}", file=sys.stderr)
        return []


def parse_events(data):
    if not isinstance(data, dict):
        return []
    raw = data.get("events")
    if not isinstance(raw, list):
        return []
    valid = []
    for ev in raw:
        if not isinstance(ev, dict):
            continue
        has_teams = bool(ev.get("strHomeTeam") and ev.get("strAwayTeam"))
        has_event_name = bool(ev.get("strEvent"))
        if has_teams or has_event_name:
            valid.append(ev)
    return valid


def format_event(ev, today_str=None, max_past_days=1, tz=timezone.utc):
    if today_str is None:
        today_str = datetime.now(tz).date().isoformat()
    date_str = (ev.get("dateEvent") or ev.get("strDate") or "").strip()
    if date_str.lower() == "null":
        date_str = ""
    time_str = (ev.get("strTime") or "").strip()
    date_str, time_str = localize_kickoff(date_str, time_str, tz)
    if not is_event_recent({"dateEvent": date_str}, today=today_str, max_past_days=max_past_days):
        return ""
    home =(ev.get("strHomeTeam") or "").strip()
    away = (ev.get("strAwayTeam") or "").strip()
    event_name = (ev.get("strEvent") or "").strip()
    if home.lower() == "null":
        home = ""
    if away.lower() == "null":
        away = ""
    if event_name.lower() == "null":
        event_name = ""
    home_score = ev.get("intHomeScore")
    away_score = ev.get("intAwayScore")
    status = (ev.get("strStatus") or "").strip()
    if status.lower() == "null":
        status = ""
    if len(time_str) >= 5 and time_str[2] == ":":
        time_str = time_str[:5]
        if time_str == "00:00":
            time_str = ""

    date_label = format_date_label(date_str, today_str)

    has_scores = (
        home_score is not None
        and away_score is not None
        and str(home_score).strip() != ""
        and str(away_score).strip() != ""
    )
    upper_status = status.upper()
    is_finished = has_scores or upper_status in ("FT", "AOT", "AET", "PEN", "FINAL")

    if home and away:
        if has_scores:
            stat = status if status and upper_status != "NS" else "FT"
            if date_label and date_label != "Today":
                return f"{home} {home_score}-{away_score} {away} ({stat}, {date_label})"
            return f"{home} {home_score}-{away_score} {away} ({stat})"
        sched = []
        if date_label:
            sched.append(date_label)
        if time_str:
            sched.append(time_str)
        if sched:
            sep = " " if date_label == "Today" else ", "
            return f"{home} vs {away} ({sep.join(sched)})"
        return f"{home} vs {away}"

    if event_name:
        if is_finished:
            stat = status if status and upper_status != "NS" else "FT"
            if date_label and date_label != "Today":
                return f"{event_name} ({stat}, {date_label})"
            return f"{event_name} ({stat})"
        sched = []
        if date_label:
            sched.append(date_label)
        if time_str:
            sched.append(time_str)
        if sched:
            sep = " " if date_label == "Today" else ", "
            return f"{event_name} ({sep.join(sched)})"
        return event_name

    return ""


def assemble_ticker_board(events, separator="     ", today_str=None, tz=timezone.utc):
    if not events:
        return "", "", ""
    formatted = [f for f in (format_event(ev, today_str=today_str, tz=tz) for ev in events) if f]
    headline = formatted[0] if len(formatted) > 0 else ""
    row1 = separator.join(formatted[1:4]) if len(formatted) > 1 else ""
    row2 = separator.join(formatted[4:7]) if len(formatted) > 4 else ""
    return headline, row1, row2


def fetch_all_sports(sports, query_date=None, api_key=DEFAULT_API_KEY):
    combined = []
    for sport in sports:
        events = fetch_sports_day(sport.strip(), query_date=query_date, api_key=api_key)
        combined.extend(events)
    return combined


def update_theme(theme_dir, api_key=DEFAULT_API_KEY, sports=None, leagues=None, query_date=None, push=False):
    config_path = os.path.join(theme_dir, "config.json")
    if not os.path.exists(config_path):
        sys.exit(f"Error: {config_path} does not exist.")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    target_leagues = leagues
    if target_leagues is None:
        target_leagues = config.get("sports_leagues")
    if target_leagues is None:
        target_leagues = DEFAULT_POPULAR_LEAGUES

    all_events = fetch_all_leagues(target_leagues, api_key=api_key)
    if not all_events:
        if sports is None:
            configured_sports = config.get("sports_list")
            if isinstance(configured_sports, list) and configured_sports:
                sports = configured_sports
            else:
                sports = DEFAULT_SPORTS
        all_events = fetch_all_sports(sports, query_date=query_date, api_key=api_key)

    if not all_events:
        print("Warning: no sports events fetched, preserving existing config.", file=sys.stderr)
        return

    headline, row1, row2 = assemble_ticker_board(all_events, tz=local_tz())

    kicker = config.get("sports_kicker")
    if not kicker or kicker == "TODAY'S GAMES":
        kicker = "SPORTS"
    config["sports_kicker"] = kicker
    config["sports_headline"] = headline
    config["sports_tickers_1"] = row1
    config["sports_tickers_2"] = row2
    if leagues is not None:
        config["sports_leagues"] = leagues

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated {config_path}:")
    print(f"  Kicker:    {config['sports_kicker']}")
    print(f"  Headline:  {headline}")
    print(f"  Row 1:     {row1}")
    print(f"  Row 2:     {row2}")

    if push:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        theme_sh = os.path.join(repo_root, "tools", "theme.sh")
        print(f"Pushing {theme_dir} to TV...")
        subprocess.run(["bash", theme_sh, theme_dir], check=True)


def main():
    parser = argparse.ArgumentParser(description="Fetch sports events and update CleanYourTV theme.")
    parser.add_argument("theme", help="Path to theme directory (e.g. themes/ghibli-dark)")
    parser.add_argument("--api-key", default=os.environ.get("THESPORTSDB_API_KEY", DEFAULT_API_KEY),
                        help="TheSportsDB API key (default: 123)")
    parser.add_argument("--sports", default=None,
                        help="Comma-separated list of sports (e.g. 'Soccer,Fighting')")
    parser.add_argument("--leagues", default=None,
                        help="Comma-separated list of league IDs (e.g. '4328,4335,4350')")
    parser.add_argument("--date", default=None, help="Query date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--push", action="store_true", help="Push theme to TV after updating")
    args = parser.parse_args()

    sports_list = [s.strip() for s in args.sports.split(",") if s.strip()] if args.sports else None
    leagues_list = [l.strip() for l in args.leagues.split(",") if l.strip()] if args.leagues else None
    update_theme(args.theme, api_key=args.api_key, sports=sports_list, leagues=leagues_list, query_date=args.date, push=args.push)


if __name__ == "__main__":
    main()
