package com.gathin.tvhome;

import org.junit.Test;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;

public class SportsTickerTest {

    @Test
    public void testFormatFinishedSoccerEvent() {
        String formatted = SportsTicker.formatMatch("Arsenal", "Chelsea", "Arsenal vs Chelsea", "2", "0", "FT", "15:00:00");
        assertEquals("Arsenal 2-0 Chelsea (FT)", formatted);
    }

    @Test
    public void testFormatUpcomingSoccerEvent() {
        String formatted = SportsTicker.formatMatch("Liverpool", "Brighton", "Liverpool vs Brighton", null, null, "NS", "17:30:00");
        assertEquals("Liverpool vs Brighton (17:30)", formatted);
    }

    @Test
    public void testFormatCombatEventWithNullTeams() {
        String formatted = SportsTicker.formatMatch(null, null, "Dalton Smith vs Alberto Puello", null, null, null, "21:00:00");
        assertEquals("Dalton Smith vs Alberto Puello (21:00)", formatted);
    }

    @Test
    public void testFormatCombatEventWithLiteralNullStringTeams() {
        String formatted = SportsTicker.formatMatch("null", "null", "Dynamite #368", null, null, null, null);
        assertEquals("Dynamite #368", formatted);
    }

    @Test
    public void testFormatUpcomingSoccerEventWithDate() {
        String formatted = SportsTicker.formatMatch("Ipswich Town", "Nottingham Forest", null, null, null, "NS", "19:00:00", "2026-10-23", "2026-10-22");
        assertEquals("Ipswich Town vs Nottingham Forest (Oct 23, 19:00)", formatted);
    }

    @Test
    public void testFormatFinishedSoccerEventWithYesterdayDate() {
        String formatted = SportsTicker.formatMatch("Club Brugge", "Lens", null, "3", "0", "FT", "19:00:00", "2026-10-21", "2026-10-22");
        assertEquals("Club Brugge 3-0 Lens (FT, Oct 21)", formatted);
    }

    @Test
    public void testFormatDropsEventsOlderThanOneDay() {
        String formatted = SportsTicker.formatMatch("Tottenham Hotspur", "Coventry City", null, "3", "1", "FT", "19:00:00", "2026-10-19", "2026-10-22");
        assertNull(formatted);
    }

    @Test
    public void testIsEventRecent() {
        org.junit.Assert.assertTrue(SportsTicker.isEventRecent("2026-10-22", "2026-10-22", 1));
        org.junit.Assert.assertTrue(SportsTicker.isEventRecent("2026-10-21", "2026-10-22", 1));
        org.junit.Assert.assertFalse(SportsTicker.isEventRecent("2026-10-20", "2026-10-22", 1));
        org.junit.Assert.assertFalse(SportsTicker.isEventRecent("2026-10-19", "2026-10-22", 1));
        org.junit.Assert.assertTrue(SportsTicker.isEventRecent("2026-10-23", "2026-10-22", 1));
        org.junit.Assert.assertTrue(SportsTicker.isEventRecent("", "2026-10-22", 1));
        org.junit.Assert.assertTrue(SportsTicker.isEventRecent(null, "2026-10-22", 1));
    }

    @Test
    public void testFormatUpcomingTodayEvent() {
        String formatted = SportsTicker.formatMatch("Arsenal", "Chelsea", null, null, null, "NS", "16:30:00", "2026-10-22", "2026-10-22");
        assertEquals("Arsenal vs Chelsea (Today 16:30)", formatted);
    }

    @Test
    public void testFormatCombatEventWithDateNoTime() {
        String formatted = SportsTicker.formatMatch(null, null, "Dalton Smith vs Alberto Puello", null, null, null, "00:00:00", "2026-10-24", "2026-10-22");
        assertEquals("Dalton Smith vs Alberto Puello (Oct 24)", formatted);
    }

    @Test
    public void testFormatCombatFinishedEventWithYesterdayDate() {
        String formatted = SportsTicker.formatMatch(null, null, "UFC Fight Night 291", null, null, "FT", "21:00:00", "2026-10-21", "2026-10-22");
        assertEquals("UFC Fight Night 291 (FT, Oct 21)", formatted);
    }

    @Test
    public void testAssembleTickerRows() {
        List<String> events = Arrays.asList(
                "Match 1 (FT)",
                "Match 2 (17:30)",
                "Match 3 (21:00)",
                "Match 4 (FT)",
                "Match 5 (20:00)"
        );
        String[] rows = SportsTicker.assemble(events, "     ");
        assertNotNull(rows);
        assertEquals(3, rows.length);
        assertEquals("Match 1 (FT)", rows[0]);
        assertEquals("Match 2 (17:30)     Match 3 (21:00)     Match 4 (FT)", rows[1]);
        assertEquals("Match 5 (20:00)", rows[2]);
    }

    @Test
    public void testEmptyEventsReturnsNull() {
        assertNull(SportsTicker.assemble(Collections.emptyList(), "     "));
        assertNull(SportsTicker.assemble(null, "     "));
    }
}
