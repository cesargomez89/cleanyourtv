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


CURRENCY_SYMBOL = ("USDMXN=X", "USD/MXN", "$")

HEADLINE_SYMBOLS = [
    ("SPY", "SPY", "$"),
    ("^VIX", "VIX", ""),
]

ROW1_SYMBOLS = [
    ("MSFT", "MSFT", "$"),
    ("META", "META", "$"),
    ("INTC", "INTC", "$"),
]

ROW2_SYMBOLS = [
    ("TSLA", "TSLA", "$"),
    ("NVDA", "NVDA", "$"),
    ("SPCX", "SPCX", "$"),
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


def fetch_and_format_list(symbol_list, separator="     "):
    parts = []
    for sym, name, pfx in symbol_list:
        price, chg = fetch_quote(sym)
        if price is not None:
            parts.append(format_quote(name, pfx, price, chg))
    return separator.join(parts)


def update_theme(theme_dir, push=False):
    config_path = os.path.join(theme_dir, "config.json")
    if not os.path.exists(config_path):
        sys.exit(f"Error: {config_path} does not exist.")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 1. Currency (replaces greeting above the clock)
    curr_sym, curr_name, curr_pfx = CURRENCY_SYMBOL
    curr_price, curr_chg = fetch_quote(curr_sym)
    currency_str = format_quote(curr_name, curr_pfx, curr_price, curr_chg) if curr_price is not None else ""

    # 2. Market headline (SPY and VIX)
    headline_str = fetch_and_format_list(HEADLINE_SYMBOLS, separator="   ·   ")

    # 3. Two rows of equities
    row1_str = fetch_and_format_list(ROW1_SYMBOLS, separator="     ")
    row2_str = fetch_and_format_list(ROW2_SYMBOLS, separator="     ")

    config["market_currency"] = currency_str
    config["market_kicker"] = "MARKETS"
    config["market_headline"] = headline_str
    config["market_tickers_1"] = row1_str
    config["market_tickers_2"] = row2_str
    config["market_tickers"] = f"{row1_str}\n{row2_str}" if row2_str else row1_str

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Updated {config_path}:")
    print(f"  Currency:  {currency_str}")
    print(f"  Headline:  {headline_str}")
    print(f"  Row 1:     {row1_str}")
    print(f"  Row 2:     {row2_str}")

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
