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
