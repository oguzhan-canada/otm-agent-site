#!/usr/bin/env python3
"""
OTM Pipeline Watchdog — Self-healing monitor.

Checks the OTM API for data freshness and triggers Cloud Run pipeline
jobs if data is stale. Designed to run locally, in CI, or as a Cloud
Scheduler target.

Usage:
    python scripts/watchdog.py                  # check only
    python scripts/watchdog.py --heal           # check + trigger recovery
    python scripts/watchdog.py --heal --wait    # check + trigger + verify
    python scripts/watchdog.py --json           # machine-readable output
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

API_URLS = [
    "https://otm-api-dev-zdqsboxooa-nn.a.run.app",
    "https://otm-api-dev-481921676964.northamerica-northeast1.run.app",
]
GCP_PROJECT = "oil-tank-monitoring-123"
GCP_REGION = "northamerica-northeast1"
STALE_WARN_DAYS = 3
STALE_CRIT_DAYS = 7
LOG_FILE = Path(__file__).parent.parent / "data" / "watchdog_log.json"

# Pipeline jobs in execution order with wait times (seconds)
PIPELINE_STAGES = [
    ("stage2-ingest-job",          60),
    ("stage3-pipeline-job",        30),
    ("job-otm-daily-runner-dev",   10),
]


def probe_api(timeout: int = 15) -> dict:
    """Check API health across all known URLs."""
    for url in API_URLS:
        try:
            req = Request(f"{url}/data", headers={"User-Agent": "otm-watchdog/1.0"})
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                obs_date = data.get("obs_date")
                tank_count = len(data.get("tank_features", []))
                if not obs_date:
                    return {"status": "no_data", "url": url, "error": "No obs_date in response"}

                age = (datetime.now(timezone.utc) - datetime.strptime(obs_date, "%Y-%m-%d").replace(tzinfo=timezone.utc))
                age_days = age.days

                if age_days >= STALE_CRIT_DAYS:
                    level = "critical"
                elif age_days >= STALE_WARN_DAYS:
                    level = "stale"
                else:
                    level = "ok"

                return {
                    "status": level,
                    "url": url,
                    "obs_date": obs_date,
                    "age_days": age_days,
                    "tank_count": tank_count,
                    "generated_at": data.get("generated_at", ""),
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }
        except (URLError, OSError, json.JSONDecodeError, ValueError) as e:
            continue  # try next URL

    return {
        "status": "api_down",
        "error": f"All {len(API_URLS)} API URLs unreachable",
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def trigger_pipeline(dry_run: bool = False) -> list:
    """Trigger pipeline recovery by executing Cloud Run jobs in order."""
    results = []
    for job_name, wait_secs in PIPELINE_STAGES:
        cmd = [
            "gcloud", "run", "jobs", "execute", job_name,
            f"--project={GCP_PROJECT}",
            f"--region={GCP_REGION}",
            "--async", "--quiet",
        ]
        if dry_run:
            results.append({"job": job_name, "action": "dry_run", "command": " ".join(cmd)})
            continue

        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            success = r.returncode == 0
            results.append({
                "job": job_name,
                "action": "triggered" if success else "failed",
                "exit_code": r.returncode,
                "output": (r.stdout + r.stderr).strip()[:200],
            })
            if success and wait_secs > 0:
                time.sleep(wait_secs)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            results.append({"job": job_name, "action": "error", "error": str(e)})

    return results


def verify_recovery(original_date: str, timeout: int = 15) -> dict:
    """Check if data refreshed after recovery attempt."""
    result = probe_api(timeout)
    new_date = result.get("obs_date", "")
    recovered = new_date != original_date and new_date != ""
    return {
        "recovered": recovered,
        "old_date": original_date,
        "new_date": new_date,
        "new_status": result.get("status", "unknown"),
    }


def append_log(entry: dict):
    """Append watchdog result to rolling log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log = []
    if LOG_FILE.exists():
        try:
            log = json.loads(LOG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            log = []
    log.append(entry)
    # Keep last 90 entries
    log = log[-90:]
    LOG_FILE.write_text(json.dumps(log, indent=2))


def main():
    parser = argparse.ArgumentParser(description="OTM Pipeline Watchdog")
    parser.add_argument("--heal", action="store_true", help="Trigger pipeline recovery if stale")
    parser.add_argument("--wait", action="store_true", help="Wait and verify after healing")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be triggered")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    # Phase 1: Check
    result = probe_api()
    status = result["status"]

    if not args.json:
        icons = {"ok": "✅", "stale": "⚠️", "critical": "🔴", "api_down": "💀", "no_data": "❓"}
        print(f"\n{icons.get(status, '?')}  Pipeline status: {status.upper()}")
        if "obs_date" in result:
            print(f"   Last observation: {result['obs_date']} ({result['age_days']}d ago)")
            print(f"   Tanks: {result.get('tank_count', '?')}")
        if "error" in result:
            print(f"   Error: {result['error']}")

    # Phase 2: Heal (if requested and needed)
    if args.heal and status in ("stale", "critical", "api_down"):
        if not args.json:
            print(f"\n🔄  Triggering pipeline recovery{'  (DRY RUN)' if args.dry_run else ''}...")
        stages = trigger_pipeline(dry_run=args.dry_run)
        result["recovery"] = stages

        if not args.json:
            for s in stages:
                icon = "✓" if s["action"] == "triggered" else "✗" if s["action"] == "failed" else "…"
                print(f"   {icon} {s['job']}: {s['action']}")

        # Phase 3: Verify (if requested)
        if args.wait and not args.dry_run:
            if not args.json:
                print("\n⏳  Waiting 5 minutes for pipeline to complete...")
            time.sleep(300)
            verification = verify_recovery(result.get("obs_date", ""), timeout=15)
            result["verification"] = verification
            if not args.json:
                if verification["recovered"]:
                    print(f"✅  Recovery successful: {verification['old_date']} → {verification['new_date']}")
                else:
                    print(f"⚠️  Data unchanged: still {verification['new_date']}")
    elif args.heal and status == "ok":
        if not args.json:
            print("   No recovery needed — data is fresh.")

    # Log result
    append_log(result)

    if args.json:
        print(json.dumps(result, indent=2))

    # Exit code: 0=ok, 1=stale, 2=critical/down
    if status == "ok":
        sys.exit(0)
    elif status == "stale":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
