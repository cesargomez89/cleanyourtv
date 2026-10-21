#!/usr/bin/env python3
"""Fetch live currency and stock quotes and inject them into a CleanYourTV theme.

Usage:
    python3 tools/market_ticker.py themes/ghibli-dark
    python3 tools/market_ticker.py themes/ghibli-dark --push
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request


DEFAULT_SYMBOLS = [
    ("USDMXN=X", "USD/MXN", "$"),
    ("^GSPC", "S&P 500", ""),
    ("NVDA", "NVDA", "$"),
    ("AAPL", "AAPL", "$"),
    ("TSLA", "TSLA", "$"),
]


def fetch_quote(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 CleanYourTV/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            meta = data["chart"]["result"][0]["meta"]
            price = meta.get("regularMarketPrice", 0.0)
            prev = meta.get("chartPreviousClose", price)
            change_pct = ((price - prev) / prev) * 100.0 if prev else 0.0
            return price, change_pct
    except Exception as e:
        print(f"Warning: failed to fetch {symbol}: {e}", file=sys.stderr)
        return None, 0.0


def format_quote(name, prefix, price, change):
    sign = "+" if change >= 0 else ""
    if price >= 1000:
        price_str = f"{price:,.0f}"
    elif price >= 10:
        price_str = f"{price:.2f}"
    else:
        price_str = f"{price:.3f}"
    return f"{name} {prefix}{price_str} ({sign}{change:.2f}%)"


def update_theme(theme_dir, push=False):
    config_path = os.path.join(theme_dir, "config.json")
    if not os.path.exists(config_path):
        sys.exit(f"Error: {config_path} does not exist.")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    quotes = []
    for sym, name, pfx in DEFAULT_SYMBOLS:
        price, chg = fetch_quote(sym)
        if price is not None:
            quotes.append((name, pfx, price, chg))

    if not quotes:
        sys.exit("Error: Could not retrieve any quotes.")

    # Format Headline: USD/MXN and S&P 500
    usd_q = next((q for q in quotes if q[0] == "USD/MXN"), None)
    sp_q = next((q for q in quotes if q[0] == "S&P 500"), None)

    headline_parts = []
    if usd_q:
        headline_parts.append(format_quote(usd_q[0], usd_q[1], usd_q[2], usd_q[3]))
    if sp_q:
        headline_parts.append(format_quote(sp_q[0], sp_q[1], sp_q[2], sp_q[3]))
    headline = "  ·  ".join(headline_parts)

    # Format Tickers: popular equities
    stock_parts = [format_quote(q[0], q[1], q[2], q[3]) for q in quotes if q[0] not in ("USD/MXN", "S&P 500")]
    stock_line = "     ".join(stock_parts)

    config["market_kicker"] = "MARKETS"
    config["market_headline"] = headline
    config["market_tickers"] = stock_line

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated {config_path}:")
    print(f"  Headline: {headline}")
    print(f"  Tickers:  {stock_line}")

    if push:
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        theme_sh = os.path.join(repo_root, "tools", "theme.sh")
        print(f"Pushing {theme_dir} to TV...")
        subprocess.run(["bash", theme_sh, theme_dir], check=True)


def main():
    parser = argparse.ArgumentParser(description="Fetch market quotes and update CleanYourTV theme.")
    parser.add_argument("theme", help="Path to theme directory (e.g. themes/ghibli-dark)")
    parser.add_argument("--push", action="store_true", help="Push theme to TV after updating")
    args = parser.parse_args()

    update_theme(args.theme, push=args.push)


if __name__ == "__main__":
    main()
