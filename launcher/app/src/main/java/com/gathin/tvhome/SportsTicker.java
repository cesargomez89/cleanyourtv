package com.gathin.tvhome;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Locale;

final class SportsTicker {
    private static final String DEFAULT_API_KEY = "123";
    private static final List<String> DEFAULT_LEAGUES = Arrays.asList("4328", "4335", "4350", "4443", "4445", "4480");
    private static final String[] MONTH_NAMES = {"", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"};

    private SportsTicker() {
    }

    static String getTodayIso() {
        return java.time.LocalDate.now(ZoneId.systemDefault()).toString();
    }

    /** TheSportsDB reports dateEvent and strTime in UTC; returns {date, time} in zone, unchanged when the time is unknown. */
    static String[] localizeKickoff(String dateStr, String timeStr, ZoneId zone) {
        String[] unchanged = {dateStr, timeStr};
        if (dateStr == null || dateStr.isEmpty() || timeStr == null || timeStr.length() < 5
                || timeStr.charAt(2) != ':' || "00:00".equals(timeStr.substring(0, 5))) {
            return unchanged;
        }
        try {
            ZonedDateTime local = LocalDateTime.parse(dateStr + "T" + timeStr.substring(0, 5))
                    .atZone(ZoneOffset.UTC).withZoneSameInstant(zone);
            return new String[]{local.toLocalDate().toString(), local.toLocalTime().toString()};
        } catch (Exception ignored) {
            return unchanged;
        }
    }

    static String formatDateLabel(String dateStr, String todayStr) {
        if (dateStr == null || dateStr.isEmpty()) return "";
        dateStr = dateStr.trim();
        if (todayStr != null && dateStr.equals(todayStr)) {
            return "Today";
        }
        try {
            String[] parts = dateStr.split("-");
            if (parts.length == 3) {
                int m = Integer.parseInt(parts[1]);
                int d = Integer.parseInt(parts[2]);
                if (m >= 1 && m <= 12 && d >= 1 && d <= 31) {
                    return MONTH_NAMES[m] + " " + d;
                }
            }
        } catch (Exception ignored) {
        }
        return dateStr;
    }

    static boolean isEventRecent(String dateStr, String todayStr, int maxPastDays) {
        if (dateStr == null || dateStr.trim().isEmpty() || "null".equalsIgnoreCase(dateStr.trim())) {
            return true;
        }
        try {
            java.time.LocalDate evDate = java.time.LocalDate.parse(dateStr.trim());
            java.time.LocalDate today = (todayStr != null && !todayStr.trim().isEmpty())
                    ? java.time.LocalDate.parse(todayStr.trim())
                    : java.time.LocalDate.now();
            long daysBetween = java.time.temporal.ChronoUnit.DAYS.between(today, evDate);
            return daysBetween >= -maxPastDays;
        } catch (Throwable ignored) {
            try {
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd", Locale.US);
                Date ev = sdf.parse(dateStr.trim());
                Date t = (todayStr != null && !todayStr.trim().isEmpty()) ? sdf.parse(todayStr.trim()) : new Date();
                if (ev != null && t != null) {
                    long diffMs = ev.getTime() - t.getTime();
                    long diffDays = diffMs / (1000L * 60 * 60 * 24);
                    return diffDays >= -maxPastDays;
                }
            } catch (Exception e) {
                return true;
            }
            return true;
        }
    }

    static String[] fetch(String apiKey, List<String> leagues) {
        String key = (apiKey != null && !apiKey.trim().isEmpty()) ? apiKey.trim() : DEFAULT_API_KEY;
        List<String> leaguesToFetch = (leagues != null && !leagues.isEmpty()) ? leagues : DEFAULT_LEAGUES;

        List<String> allEvents = new ArrayList<>();
        for (String leagueId : leaguesToFetch) {
            String past = fetchEndpoint("eventspastleague.php?id=" + leagueId, key);
            if (past != null) allEvents.addAll(parseEvents(past));
            try { Thread.sleep(250); } catch (InterruptedException ignored) {}
            String next = fetchEndpoint("eventsnextleague.php?id=" + leagueId, key);
            if (next != null) allEvents.addAll(parseEvents(next));
            try { Thread.sleep(250); } catch (InterruptedException ignored) {}
        }
        return assemble(allEvents, "     ");
    }

    private static String fetchEndpoint(String path, String apiKey) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL("https://www.thesportsdb.com/api/v1/json/" + apiKey + "/" + path);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestProperty("User-Agent", "Mozilla/5.0 CleanYourTV/1.0");
            conn.setConnectTimeout(4000);
            conn.setReadTimeout(4000);
            if (conn.getResponseCode() != 200) return null;

            BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) sb.append(line);
            reader.close();
            return sb.toString();
        } catch (Exception ignored) {
            return null;
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    static List<String> parseEvents(String jsonStr) {
        List<String> list = new ArrayList<>();
        if (jsonStr == null || jsonStr.isEmpty()) return list;
        try {
            JSONObject root = new JSONObject(jsonStr);
            JSONArray events = root.optJSONArray("events");
            if (events == null) return list;
            for (int i = 0; i < events.length(); i++) {
                JSONObject ev = events.optJSONObject(i);
                if (ev != null) {
                    String formatted = formatEvent(ev);
                    if (formatted != null && !formatted.isEmpty()) {
                        list.add(formatted);
                    }
                }
            }
        } catch (Exception ignored) {
        }
        return list;
    }

    static String formatEvent(JSONObject ev) {
        String home = ev.isNull("strHomeTeam") ? "" : ev.optString("strHomeTeam", "").trim();
        String away = ev.isNull("strAwayTeam") ? "" : ev.optString("strAwayTeam", "").trim();
        String eventName = ev.isNull("strEvent") ? "" : ev.optString("strEvent", "").trim();
        String homeScore = ev.isNull("intHomeScore") ? null : ev.optString("intHomeScore", "").trim();
        String awayScore = ev.isNull("intAwayScore") ? null : ev.optString("intAwayScore", "").trim();
        String status = ev.isNull("strStatus") ? "" : ev.optString("strStatus", "").trim();
        String timeStr = ev.isNull("strTime") ? "" : ev.optString("strTime", "").trim();
        String dateStr = ev.isNull("dateEvent") ? (ev.isNull("strDate") ? "" : ev.optString("strDate", "").trim()) : ev.optString("dateEvent", "").trim();
        if ("null".equalsIgnoreCase(home)) home = "";
        if ("null".equalsIgnoreCase(away)) away = "";
        if ("null".equalsIgnoreCase(eventName)) eventName = "";
        if ("null".equalsIgnoreCase(status)) status = "";
        if ("null".equalsIgnoreCase(timeStr)) timeStr = "";
        if ("null".equalsIgnoreCase(dateStr)) dateStr = "";
        ZoneId zone = ZoneId.systemDefault();
        return formatMatch(home, away, eventName, homeScore, awayScore, status, timeStr, dateStr, getTodayIso(), zone);
    }

    static String formatMatch(String home, String away, String eventName, String homeScore, String awayScore, String status, String timeStr) {
        return formatMatch(home, away, eventName, homeScore, awayScore, status, timeStr, null, null);
    }

    static String formatMatch(String home, String away, String eventName, String homeScore, String awayScore,
                               String status, String timeStr, String dateStr, String todayStr) {
        return formatMatch(home, away, eventName, homeScore, awayScore, status, timeStr, dateStr, todayStr, ZoneOffset.UTC);
    }

    static String formatMatch(String home, String away, String eventName, String homeScore, String awayScore,
                               String status, String timeStr, String dateStr, String todayStr, ZoneId zone) {
        String[] local = localizeKickoff(dateStr, timeStr, zone);
        dateStr = local[0];
        timeStr = local[1];
        if (!isEventRecent(dateStr, todayStr, 1)) {
            return null;
        }
        if (home != null && "null".equalsIgnoreCase(home.trim())) home = "";
        if (away != null && "null".equalsIgnoreCase(away.trim())) away = "";
        if (eventName != null && "null".equalsIgnoreCase(eventName.trim())) eventName = "";
        if (status != null && "null".equalsIgnoreCase(status.trim())) status = "";
        if (timeStr != null && "null".equalsIgnoreCase(timeStr.trim())) timeStr = "";

        if (timeStr != null && timeStr.length() >= 5 && timeStr.charAt(2) == ':') {
            timeStr = timeStr.substring(0, 5);
            if ("00:00".equals(timeStr)) {
                timeStr = "";
            }
        }

        String dateLabel = formatDateLabel(dateStr, todayStr);
        boolean hasScores = homeScore != null && awayScore != null && !homeScore.isEmpty() && !awayScore.isEmpty();
        String upperStatus = status != null ? status.toUpperCase(Locale.US) : "";
        boolean isFinished = hasScores || "FT".equals(upperStatus) || "AOT".equals(upperStatus) || "AET".equals(upperStatus)
                || "PEN".equals(upperStatus) || "FINAL".equals(upperStatus);

        if (home != null && away != null && !home.isEmpty() && !away.isEmpty()) {
            if (hasScores) {
                String stat = (status != null && !status.isEmpty() && !"NS".equals(upperStatus)) ? status : "FT";
                if (!dateLabel.isEmpty() && !"Today".equals(dateLabel)) {
                    return home + " " + homeScore + "-" + awayScore + " " + away + " (" + stat + ", " + dateLabel + ")";
                }
                return home + " " + homeScore + "-" + awayScore + " " + away + " (" + stat + ")";
            }
            String sched = buildScheduleSuffix(dateLabel, timeStr);
            if (!sched.isEmpty()) {
                return home + " vs " + away + " (" + sched + ")";
            }
            return home + " vs " + away;
        }

        if (eventName != null && !eventName.isEmpty()) {
            if (isFinished) {
                String stat = (status != null && !status.isEmpty() && !"NS".equals(upperStatus)) ? status : "FT";
                if (!dateLabel.isEmpty() && !"Today".equals(dateLabel)) {
                    return eventName + " (" + stat + ", " + dateLabel + ")";
                }
                return eventName + " (" + stat + ")";
            }
            String sched = buildScheduleSuffix(dateLabel, timeStr);
            if (!sched.isEmpty()) {
                return eventName + " (" + sched + ")";
            }
            return eventName;
        }

        return null;
    }

    private static String buildScheduleSuffix(String dateLabel, String timeStr) {
        if (!dateLabel.isEmpty() && timeStr != null && !timeStr.isEmpty()) {
            return "Today".equals(dateLabel) ? ("Today " + timeStr) : (dateLabel + ", " + timeStr);
        }
        if (!dateLabel.isEmpty()) return dateLabel;
        if (timeStr != null && !timeStr.isEmpty()) return timeStr;
        return "";
    }

    static String[] assemble(List<String> events, String sep) {
        if (events == null || events.isEmpty()) return null;
        String headline = events.get(0);
        String row1 = joinRange(events, 1, 4, sep);
        String row2 = joinRange(events, 4, 7, sep);
        return new String[]{headline, row1, row2};
    }

    private static String joinRange(List<String> list, int start, int end, String sep) {
        if (start >= list.size()) return "";
        int bound = Math.min(end, list.size());
        StringBuilder sb = new StringBuilder();
        for (int i = start; i < bound; i++) {
            if (sb.length() > 0) sb.append(sep);
            sb.append(list.get(i));
        }
        return sb.toString();
    }
}
