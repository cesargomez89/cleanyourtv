package com.gathin.tvhome;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

final class MarketTicker {
    static final class Result {
        final String currency;
        final String headline;
        final String row1;
        final String row2;

        Result(String currency, String headline, String row1, String row2) {
            this.currency = currency;
            this.headline = headline;
            this.row1 = row1;
            this.row2 = row2;
        }
    }

    private static final String[][] HEADLINE = {
            {"SPY", "SPY", "$"},
            {"^VIX", "VIX", ""}
    };

    private static final String[][] ROW1 = {
            {"MSFT", "MSFT", "$"},
            {"META", "META", "$"},
            {"INTC", "INTC", "$"}
    };

    private static final String[][] ROW2 = {
            {"TSLA", "TSLA", "$"},
            {"NVDA", "NVDA", "$"},
            {"SPCX", "SPCX", "$"}
    };

    static Result fetch() {
        try {
            double[] usd = fetchQuote("USDMXN=X");
            String currency = usd != null ? formatQuote("USD/MXN", "$", usd[0], usd[1]) : null;
            String headline = formatList(HEADLINE, "   ·   ");
            String row1 = formatList(ROW1, "     ");
            String row2 = formatList(ROW2, "     ");
            return new Result(currency, headline, row1, row2);
        } catch (Exception ignored) {
            return null;
        }
    }

    private static String formatList(String[][] list, String sep) {
        StringBuilder sb = new StringBuilder();
        for (String[] sym : list) {
            double[] q = fetchQuote(sym[0]);
            if (q != null) {
                if (sb.length() > 0) sb.append(sep);
                sb.append(formatQuote(sym[1], sym[2], q[0], q[1]));
            }
        }
        return sb.length() > 0 ? sb.toString() : null;
    }

    private static double[] fetchQuote(String symbol) {
        HttpURLConnection conn = null;
        try {
            URL url = new URL("https://query1.finance.yahoo.com/v8/finance/chart/" + symbol + "?interval=1d&range=1d");
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

            JSONObject root = new JSONObject(sb.toString());
            JSONArray results = root.getJSONObject("chart").optJSONArray("result");
            if (results == null || results.length() == 0) return null;
            JSONObject meta = results.getJSONObject(0).getJSONObject("meta");
            double price = meta.optDouble("regularMarketPrice", 0);
            double prev = meta.optDouble("chartPreviousClose", price);
            double changePct = prev != 0 ? ((price - prev) / prev) * 100.0 : 0.0;
            return new double[]{price, changePct};
        } catch (Exception ignored) {
            return null;
        } finally {
            if (conn != null) conn.disconnect();
        }
    }

    private static String formatQuote(String name, String prefix, double price, double change) {
        String sign = change >= 0 ? "+" : "";
        String priceStr;
        if (price >= 1000) {
            priceStr = String.format(Locale.US, "%,.0f", price);
        } else if (price >= 10) {
            priceStr = String.format(Locale.US, "%.2f", price);
        } else {
            priceStr = String.format(Locale.US, "%.3f", price);
        }
        return String.format(Locale.US, "%s %s%s (%s%.2f%%)", name, prefix, priceStr, sign, change);
    }
}
