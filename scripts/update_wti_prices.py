#!/usr/bin/env python3
"""Fetch WTI daily close prices and write to data/wti_prices.json.

Sources tried in order:
  1. FRED API (DCOILWTICO series) — free, no key required
  2. datasets/oil-prices GitHub CSV — community-maintained

Designed to run in GitHub Actions daily or locally.
"""
import json, urllib.request, csv, io, os, sys
from datetime import datetime, timedelta, timezone

FRED_URL = "https://api.stlouisfed.org/fred/series/observations?series_id=DCOILWTICO&file_type=json&sort_order=asc&observation_start={start}"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
GITHUB_CSV = "https://raw.githubusercontent.com/datasets/oil-prices/main/data/wti-daily.csv"
OUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "wti_prices.json")


def fetch_fred(start_date: str) -> dict:
    """Fetch from FRED. Requires FRED_API_KEY env var."""
    if not FRED_API_KEY:
        raise RuntimeError("FRED_API_KEY not set")
    url = FRED_URL.format(start=start_date) + f"&api_key={FRED_API_KEY}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read())
    prices = {}
    for obs in data.get("observations", []):
        if obs["value"] != ".":
            prices[obs["date"]] = round(float(obs["value"]), 2)
    return prices


def fetch_github_csv(start_date: str) -> dict:
    """Fetch from community GitHub CSV."""
    req = urllib.request.Request(GITHUB_CSV, headers={"User-Agent": "OTM-Agent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    prices = {}
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        date = row["Date"]
        if date >= start_date and row["Price"]:
            try:
                prices[date] = round(float(row["Price"]), 2)
            except ValueError:
                pass
    return prices


def fetch_yahoo(start_date: str) -> dict:
    """Fetch from Yahoo Finance (CL=F WTI futures), no API key needed."""
    start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
    end_ts = int(datetime.now().timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/CL=F"
        f"?period1={start_ts}&period2={end_ts}&interval=1d"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "OTM-Agent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    closes = result["indicators"]["quote"][0]["close"]
    prices = {}
    for ts, close in zip(timestamps, closes):
        if close is not None:
            d = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            if d >= start_date:
                prices[d] = round(close, 2)
    return prices


def main():
    # Load existing data if present
    existing = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            existing = json.load(f).get("prices", {})

    # Determine start date: 2 years ago or earliest missing
    two_years_ago = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    start = two_years_ago

    # Try FRED first, then Yahoo, then GitHub CSV
    new_prices = {}
    source = "none"
    for name, fetcher in [("fred", fetch_fred), ("yahoo", fetch_yahoo), ("github_csv", fetch_github_csv)]:
        try:
            new_prices = fetcher(start)
            if new_prices:
                source = name
                print(f"✓ Fetched {len(new_prices)} prices from {name}")
                break
        except Exception as e:
            print(f"✗ {name} failed: {e}", file=sys.stderr)

    if not new_prices:
        print("✗ All sources failed — no update", file=sys.stderr)
        sys.exit(1)

    # Merge: existing + new (new wins on conflict)
    merged = {**existing, **new_prices}
    sorted_dates = sorted(merged.keys())
    latest = sorted_dates[-1] if sorted_dates else "unknown"

    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": source,
        "latest_date": latest,
        "count": len(merged),
        "prices": {d: merged[d] for d in sorted_dates}
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=1)

    print(f"✓ Wrote {len(merged)} prices to {OUT_PATH} (latest: {latest}, source: {source})")


if __name__ == "__main__":
    main()
