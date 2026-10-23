import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.sports_ticker import (
    assemble_ticker_board,
    format_event,
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

    def test_format_finished_with_past_date(self):
        event = {
            "strHomeTeam": "Tottenham Hotspur",
            "strAwayTeam": "Coventry City",
            "intHomeScore": "3",
            "intAwayScore": "1",
            "strStatus": "FT",
            "dateEvent": "2026-10-19",
        }
        formatted = format_event(event, today_str="2026-10-22")
        self.assertEqual(formatted, "Tottenham Hotspur 3-1 Coventry City (FT, Oct 19)")

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


if __name__ == "__main__":
    unittest.main()
