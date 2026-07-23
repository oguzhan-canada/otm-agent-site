#!/usr/bin/env python3
"""Fetch WTI daily close prices and write to data/wti_prices.json.

Fetches from ALL available sources and merges them so the series stays
fresh even when one source lags. Date coverage is the union of every
source (freshest date wins). For value conflicts on the same date, the
most authoritative EIA spot source wins; Yahoo futures are used only to
fill the most-recent days that spot prices haven't been published for yet.

Sources (ascending trust — later overrides earlier on shared dates):
  1. Yahoo Finance CL=F  — WTI front-month futures, real-time, no key
  2. datasets/oil-prices — community EIA spot CSV (may lag)
  3. FRED API DCOILWTICO — EIA spot via API (needs FRED_API_KEY; can lag ~1 week)
  4. FRED public CSV     — EIA spot via fredgraph.csv (no key, ~2-day lag)

Designed to run in GitHub Actions daily or locally.
"""
import json, urllib.request, csv, io, os, sys
from datetime import datetime, timedelta, timezone

FRED_URL = "https://api.stlouisfed.org/fred/series/observations?series_id=DCOILWTICO&file_type=json&sort_order=asc&observation_start={start}"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO&cosd={start}"
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


def fetch_fred_csv(start_date: str) -> dict:
    """Fetch WTI spot from FRED's public CSV endpoint (fredgraph.csv, no key)."""
    url = FRED_CSV_URL.format(start=start_date)
    req = urllib.request.Request(url, headers={"User-Agent": "OTM-Agent/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    prices = {}
    reader = csv.reader(io.StringIO(text))
    next(reader, None)  # header: observation_date,DCOILWTICO
    for row in reader:
        if len(row) < 2:
            continue
        date, val = row[0].strip(), row[1].strip()
        if date >= start_date and val not in ("", "."):
            try:
                prices[date] = round(float(val), 2)
            except ValueError:
                pass
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


# Source registry in ASCENDING trust order. On shared dates, later entries
# override earlier ones, so authoritative EIA spot prices win over the
# community CSV, and both win over Yahoo futures (which only fill the most
# recent days spot hasn't published yet). The union of dates across all
# sources gives the freshest possible coverage.
SOURCES = [
    ("yahoo", fetch_yahoo),           # WTI futures (CL=F) — freshest, fills leading edge
    ("github_csv", fetch_github_csv), # EIA spot, community-maintained (may lag)
    ("fred_api", fetch_fred),         # EIA spot via FRED API (needs key; can lag ~1 week)
    ("fred_csv", fetch_fred_csv),     # EIA spot via FRED public CSV (no key, ~2-day lag)
]


def main():
    # Load existing data if present
    existing = {}
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            existing = json.load(f).get("prices", {})

    # Determine start date: 2 years ago
    start = (datetime.now(timezone.utc) - timedelta(days=730)).strftime("%Y-%m-%d")

    # Fetch from every source independently; a failure in one never blocks
    # the others (previously the first non-empty source "won", so a lagging
    # FRED API silently kept the chart ~1 week stale).
    results = {}
    for name, fetcher in SOURCES:
        try:
            prices = fetcher(start)
            if prices:
                results[name] = prices
                print(f"✓ {name}: {len(prices)} prices (through {max(prices)})")
            else:
                print(f"✗ {name}: no data returned", file=sys.stderr)
        except Exception as e:
            print(f"✗ {name} failed: {e}", file=sys.stderr)

    if not results:
        print("✗ All sources failed — no update", file=sys.stderr)
        sys.exit(1)

    # Merge: existing as base, then each source in ascending trust order so
    # the most authoritative value wins per date while keeping the full union.
    merged = dict(existing)
    for name, _ in SOURCES:
        if name in results:
            merged.update(results[name])

    sorted_dates = sorted(merged.keys())
    latest = sorted_dates[-1] if sorted_dates else "unknown"

    # Which source supplied the latest date (highest trust wins)
    latest_source = "existing"
    for name, _ in reversed(SOURCES):
        if name in results and latest in results[name]:
            latest_source = name
            break

    output = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": ",".join(results.keys()),
        "latest_date": latest,
        "latest_source": latest_source,
        "count": len(merged),
        "prices": {d: merged[d] for d in sorted_dates}
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=1)

    # Freshness report — flag if the newest price is more than 4 days old
    try:
        age = (datetime.now(timezone.utc).date() - datetime.strptime(latest, "%Y-%m-%d").date()).days
        flag = "  ⚠ STALE (>4d)" if age > 4 else ""
        print(f"✓ Wrote {len(merged)} prices (latest: {latest} via {latest_source}, {age}d old){flag}")
    except ValueError:
        print(f"✓ Wrote {len(merged)} prices (latest: {latest}, source: {latest_source})")


if __name__ == "__main__":
    main()
