from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from tools.sports_ticker import (
    DEFAULT_POPULAR_LEAGUES,
    assemble_ticker_board,
    format_event,
    is_event_recent,
    parse_events,
    update_theme,
)


SAMPLE_EVENTS_SOCCER = {
    "events": [
        {
            "idEvent": "1001",
            "strSport": "Soccer",
            "strLeague": "English Premier League",
            "strHomeTeam": "Liverpool",
            "strAwayTeam": "Brighton",
            "intHomeScore": "2",
            "intAwayScore": "1",
            "strStatus": "FT",
            "strTime": "14:00:00"
        },
        {
            "idEvent": "1002",
            "strSport": "Soccer",
            "strLeague": "English Premier League",
            "strHomeTeam": "Arsenal",
            "strAwayTeam": "Chelsea",
            "intHomeScore": None,
            "intAwayScore": None,
            "strStatus": "NS",
            "strTime": "16:30:00"
        }
    ]
}

SAMPLE_EVENTS_FIGHTING = {
    "events": [
        {
            "idEvent": "2001",
            "strSport": "Fighting",
            "strLeague": "Boxing",
            "strEvent": "Dalton Smith vs Alberto Puello",
            "strHomeTeam": None,
            "strAwayTeam": None,
            "intHomeScore": None,
            "intAwayScore": None,
            "strStatus": "",
            "strTime": "21:00:00"
        },
        {
            "idEvent": "2002",
            "strSport": "Fighting",
            "strLeague": "UFC",
            "strEvent": "UFC 333 Volkanovski vs Evloev",
            "strHomeTeam": None,
            "strAwayTeam": None,
            "intHomeScore": None,
            "intAwayScore": None,
            "strStatus": "",
            "strTime": "16:00:00"
        }
    ]
}


class SportsTickerTest(unittest.TestCase):
    def test_format_finished_soccer_event(self):
        event = SAMPLE_EVENTS_SOCCER["events"][0]
        formatted = format_event(event)
        self.assertEqual(formatted, "Liverpool 2-1 Brighton (FT)")

    def test_format_upcoming_soccer_event(self):
        event = SAMPLE_EVENTS_SOCCER["events"][1]
        formatted = format_event(event)
        self.assertEqual(formatted, "Arsenal vs Chelsea (16:30)")

    def test_format_combat_event_with_null_teams(self):
        boxing = SAMPLE_EVENTS_FIGHTING["events"][0]
        formatted = format_event(boxing)
        self.assertEqual(formatted, "Dalton Smith vs Alberto Puello (21:00)")

        ufc = SAMPLE_EVENTS_FIGHTING["events"][1]
        formatted_ufc = format_event(ufc)
        self.assertEqual(formatted_ufc, "UFC 333 Volkanovski vs Evloev (16:00)")

    def test_format_upcoming_with_future_date(self):
        event = {
            "strHomeTeam": "Ipswich Town",
            "strAwayTeam": "Nottingham Forest",
            "strTime": "19:00:00",
            "dateEvent": "2026-10-23",
        }
        formatted = format_event(event, today_str="2026-10-22")
        self.assertEqual(formatted, "Ipswich Town vs Nottingham Forest (Oct 23, 19:00)")

    def test_format_finished_with_yesterday_date(self):
        event = {
            "strHomeTeam": "Club Brugge",
            "strAwayTeam": "Lens",
            "intHomeScore": "3",
            "intAwayScore": "0",
            "strStatus": "FT",
            "dateEvent": "2026-10-21",
        }
        formatted = format_event(event, today_str="2026-10-22")
        self.assertEqual(formatted, "Club Brugge 3-0 Lens (FT, Oct 21)")

    def test_format_drops_events_older_than_one_day(self):
        event = {
            "strHomeTeam": "Tottenham Hotspur",
            "strAwayTeam": "Coventry City",
            "intHomeScore": "3",
            "intAwayScore": "1",
            "strStatus": "FT",
            "dateEvent": "2026-10-19",
        }
        formatted = format_event(event, today_str="2026-10-22")
        self.assertEqual(formatted, "")
        self.assertFalse(is_event_recent(event, today="2026-10-22", max_past_days=1))

    def test_format_upcoming_today(self):
        event = {
            "strHomeTeam": "Arsenal",
            "strAwayTeam": "Chelsea",
            "strTime": "16:30:00",
            "dateEvent": "2026-10-22",
        }
        formatted = format_event(event, today_str="2026-10-22")
        self.assertEqual(formatted, "Arsenal vs Chelsea (Today 16:30)")

    def test_format_combat_with_date_no_time(self):
        event = {
            "strEvent": "Dalton Smith vs Alberto Puello",
            "dateEvent": "2026-10-24",
            "strTime": "00:00:00",
        }
        formatted = format_event(event, today_str="2026-10-22")
        self.assertEqual(formatted, "Dalton Smith vs Alberto Puello (Oct 24)")

    def test_assemble_ticker_board(self):
        all_events = [
            SAMPLE_EVENTS_SOCCER["events"][0],
            SAMPLE_EVENTS_SOCCER["events"][1],
            SAMPLE_EVENTS_FIGHTING["events"][0],
            SAMPLE_EVENTS_FIGHTING["events"][1],
            {"strEvent": "Fifth Match", "strTime": "20:00:00"}
        ]
        headline, row1, row2 = assemble_ticker_board(all_events)
        self.assertEqual(headline, "Liverpool 2-1 Brighton (FT)")
        self.assertEqual(row1, "Arsenal vs Chelsea (16:30)     Dalton Smith vs Alberto Puello (21:00)     UFC 333 Volkanovski vs Evloev (16:00)")
        self.assertEqual(row2, "Fifth Match (20:00)")

    def test_update_theme_updates_config_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            theme_path = Path(tmpdir)
            cfg_file = theme_path / "config.json"
            cfg_file.write_text(json.dumps({"market_kicker": "MARKETS"}))

            all_events = [
                SAMPLE_EVENTS_SOCCER["events"][0],
                SAMPLE_EVENTS_SOCCER["events"][1],
                SAMPLE_EVENTS_FIGHTING["events"][0],
                SAMPLE_EVENTS_FIGHTING["events"][1],
                {"strEvent": "Fifth Match", "strTime": "20:00:00"}
            ]
            with patch("tools.sports_ticker.fetch_all_leagues", return_value=all_events):
                update_theme(str(theme_path), api_key="123", push=False)

            updated = json.loads(cfg_file.read_text())
            self.assertEqual(updated["sports_kicker"], "SPORTS")
            self.assertEqual(updated["sports_headline"], "Liverpool 2-1 Brighton (FT)")
            self.assertEqual(updated["sports_tickers_1"], "Arsenal vs Chelsea (16:30)     Dalton Smith vs Alberto Puello (21:00)     UFC 333 Volkanovski vs Evloev (16:00)")
            self.assertEqual(updated["sports_tickers_2"], "Fifth Match (20:00)")
            self.assertEqual(updated["market_kicker"], "MARKETS")


    def test_default_popular_leagues_includes_marquee_soccer(self):
        self.assertEqual(DEFAULT_POPULAR_LEAGUES, ["4328", "4335", "4350", "4443", "4445", "4480"])

    def test_format_liga_mx_finished_event(self):
        event = {
            "strLeague": "Mexican Liga MX",
            "strHomeTeam": "Pachuca",
            "strAwayTeam": "Cruz Azul",
            "intHomeScore": "1",
            "intAwayScore": "2",
            "strStatus": "FT",
            "dateEvent": "2026-10-22",
        }
        formatted = format_event(event, today_str="2026-10-23")
        self.assertEqual(formatted, "Pachuca 1-2 Cruz Azul (FT, Oct 22)")

    def test_format_la_liga_upcoming_today(self):
        event = {
            "strLeague": "Spanish La Liga",
            "strHomeTeam": "Deportivo Alavés",
            "strAwayTeam": "Málaga",
            "strTime": "19:00:00",
            "dateEvent": "2026-10-23",
        }
        formatted = format_event(event, today_str="2026-10-23")
        self.assertEqual(formatted, "Deportivo Alavés vs Málaga (Today 19:00)")

    def _upcoming(self, time_str, date_str, **extra):
        return {"strHomeTeam": "Arsenal", "strAwayTeam": "Chelsea", "strTime": time_str, "dateEvent": date_str, **extra}

    def test_kickoff_converted_from_utc_to_tv_zone(self):
        tz = ZoneInfo("America/Mexico_City")
        formatted = format_event(self._upcoming("23:30:00", "2026-10-23"), today_str="2026-10-23", tz=tz)
        self.assertEqual(formatted, "Arsenal vs Chelsea (Today 17:30)")

    def test_kickoff_date_rolls_back_across_midnight(self):
        tz = ZoneInfo("America/Los_Angeles")
        formatted = format_event(self._upcoming("02:00:00", "2026-10-24"), today_str="2026-10-23", tz=tz)
        self.assertEqual(formatted, "Arsenal vs Chelsea (Today 19:00)")

    def test_kickoff_date_rolls_forward_across_midnight(self):
        tz = ZoneInfo("Asia/Tokyo")
        formatted = format_event(self._upcoming("20:00:00", "2026-10-23"), today_str="2026-10-23", tz=tz)
        self.assertEqual(formatted, "Arsenal vs Chelsea (Oct 24, 05:00)")

    def test_finished_label_uses_tv_zone_date(self):
        tz = ZoneInfo("America/Los_Angeles")
        event = self._upcoming("01:00:00", "2026-10-23", intHomeScore="1", intAwayScore="2", strStatus="FT")
        formatted = format_event(event, today_str="2026-10-23", tz=tz)
        self.assertEqual(formatted, "Arsenal 1-2 Chelsea (FT, Oct 22)")

    def test_unknown_kickoff_time_keeps_date(self):
        tz = ZoneInfo("America/Los_Angeles")
        event = {"strEvent": "Dalton Smith vs Alberto Puello", "strTime": "00:00:00", "dateEvent": "2026-10-24"}
        formatted = format_event(event, today_str="2026-10-23", tz=tz)
        self.assertEqual(formatted, "Dalton Smith vs Alberto Puello (Oct 24)")

    def test_default_today_uses_tv_zone(self):
        tz = ZoneInfo("Pacific/Kiritimati")
        today = datetime.now(tz).date().isoformat()
        event = self._upcoming("00:00:00", today)
        self.assertEqual(format_event(event, tz=tz), "Arsenal vs Chelsea (Today)")

    def test_update_theme_with_custom_leagues(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            theme_path = Path(tmpdir)
            cfg_file = theme_path / "config.json"
            cfg_file.write_text(json.dumps({"market_kicker": "MARKETS"}))

            sample_events = [
                {"strHomeTeam": "Arsenal", "strAwayTeam": "Chelsea", "strTime": "16:30:00", "dateEvent": "2026-10-23"},
                {"strHomeTeam": "Real Madrid", "strAwayTeam": "Barcelona", "strTime": "20:00:00", "dateEvent": "2026-10-23"},
                {"strHomeTeam": "América", "strAwayTeam": "Chivas", "strTime": "21:00:00", "dateEvent": "2026-10-23"},
            ]
            with patch("tools.sports_ticker.fetch_all_leagues", return_value=sample_events) as mock_fetch, \
                    patch("tools.sports_ticker.local_tz", return_value=timezone.utc):
                update_theme(str(theme_path), api_key="123", leagues=["4328", "4335", "4350"], push=False)
                mock_fetch.assert_called_once_with(["4328", "4335", "4350"], api_key="123")

            updated = json.loads(cfg_file.read_text())
            self.assertEqual(updated["sports_leagues"], ["4328", "4335", "4350"])
            self.assertEqual(updated["sports_headline"], "Arsenal vs Chelsea (Today 16:30)")
            self.assertEqual(updated["sports_tickers_1"], "Real Madrid vs Barcelona (Today 20:00)     América vs Chivas (Today 21:00)")


if __name__ == "__main__":
    unittest.main()
