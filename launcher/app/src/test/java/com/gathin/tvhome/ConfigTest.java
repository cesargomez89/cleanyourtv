package com.gathin.tvhome;

import org.junit.Test;

import java.util.Arrays;
import java.util.Collections;

import static org.junit.Assert.assertEquals;

public class ConfigTest {

    @Test
    public void testSportsFieldsOnConfig() {
        Config cfg = new Config(
                Collections.emptyList(), false, Collections.emptyList(), "", "",
                Collections.emptyMap(), Collections.emptyMap(), Collections.emptyMap(),
                "", "", "", 5, 1, false, false, false, "", false, false, true, true, false,
                "", false, false, false, 0, 0, new int[0], false, false, null,
                Collections.emptyList(), 0, 0, false, Festival.NONE, new int[0],
                Collections.emptyList(), Collections.emptyList(), false,
                "", "", "", "", "", "",
                "FIGHT NIGHT", "Dalton Smith vs Alberto Puello (21:00)", "Row 1", "Row 2",
                "custom_key", Arrays.asList("Soccer", "Fighting"),
                Arrays.asList("4328", "4335", "4350", "4443", "4445", "4480")
        );

        assertEquals("FIGHT NIGHT", cfg.sportsKicker);
        assertEquals("Dalton Smith vs Alberto Puello (21:00)", cfg.sportsHeadline);
        assertEquals("Row 1", cfg.sportsTickers1);
        assertEquals("Row 2", cfg.sportsTickers2);
        assertEquals("custom_key", cfg.sportsApiKey);
        assertEquals(Arrays.asList("Soccer", "Fighting"), cfg.sportsList);
        assertEquals(Arrays.asList("4328", "4335", "4350", "4443", "4445", "4480"), cfg.sportsLeagues);
    }

    @Test
    public void testSportsDefaultLeaguesFallback() {
        Config cfg = new Config(
                Collections.emptyList(), false, Collections.emptyList(), "", "",
                Collections.emptyMap(), Collections.emptyMap(), Collections.emptyMap(),
                "", "", "", 5, 1, false, false, false, "", false, false, true, true, false,
                "", false, false, false, 0, 0, new int[0], false, false, null,
                Collections.emptyList(), 0, 0, false, Festival.NONE, new int[0],
                Collections.emptyList(), Collections.emptyList(), false,
                "", "", "", "", "", "",
                "SPORTS", "", "", "",
                "", Collections.emptyList(),
                Collections.emptyList()
        );

        assertEquals(Arrays.asList("4328", "4335", "4350", "4443", "4445", "4480"), cfg.sportsLeagues);
    }
}
