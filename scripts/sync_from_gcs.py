#!/usr/bin/env python3
"""
sync_from_gcs.py — Pull benchmark results from GCS to local data/ directory.

Used by the GitHub Actions sync-results.yml workflow.
Also runnable locally:
    python scripts/sync_from_gcs.py --bucket otm-public-results --output-dir data/

Expects GCP credentials via GOOGLE_APPLICATION_CREDENTIALS or
google-github-actions/auth.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone


BENCHMARK_IDS = [
    "otm_persona_align",
    "otm_skill_retention",
    "otm_mem_utility",
    "otm_oos_replay",
]


def sync_from_gcs(
    bucket_name: str,
    output_dir: str,
    benchmark: str = "all",
) -> list[str]:
    """
    Download latest benchmark results from GCS bucket to output_dir.

    Each benchmark writes to:
        gs://{bucket}/{benchmark_id}/latest.json
        gs://{bucket}/{benchmark_id}/runs/YYYY-MM-DD.json

    We download latest.json for each benchmark and save as
    {output_dir}/{benchmark_id}.json.
    """
    try:
        from google.cloud import storage
    except ImportError:
        print("ERROR: google-cloud-storage not installed")
        print("  pip install google-cloud-storage")
        sys.exit(1)

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    if benchmark == "all":
        benchmarks = BENCHMARK_IDS
    else:
        benchmarks = [benchmark.lower().replace("-", "_")]

    os.makedirs(output_dir, exist_ok=True)
    updated = []

    for bid in benchmarks:
        blob_path = f"{bid}/latest.json"
        blob = bucket.blob(blob_path)

        if not blob.exists():
            print(f"  SKIP: {blob_path} not found in gs://{bucket_name}")
            continue

        local_path = os.path.join(output_dir, f"{bid}.json")

        # Check if local file already matches (by comparing run_id)
        if os.path.exists(local_path):
            with open(local_path) as f:
                local_data = json.load(f)
            remote_data = json.loads(blob.download_as_text())
            if local_data.get("run_id") == remote_data.get("run_id"):
                print(f"  SKIP: {bid} — already up to date (run_id: {remote_data['run_id']})")
                continue
            # Save the remote data
            with open(local_path, "w") as f:
                json.dump(remote_data, f, indent=2)
        else:
            blob.download_to_filename(local_path)

        print(f"  SYNC: {bid} → {local_path}")
        updated.append(bid)

    return updated


def main():
    parser = argparse.ArgumentParser(description="Sync benchmark results from GCS")
    parser.add_argument("--bucket", required=True, help="GCS bucket name")
    parser.add_argument("--output-dir", default="data/", help="Local output directory")
    parser.add_argument("--benchmark", default="all", help="Specific benchmark or 'all'")
    args = parser.parse_args()

    print(f"Syncing from gs://{args.bucket} → {args.output_dir}")
    updated = sync_from_gcs(args.bucket, args.output_dir, args.benchmark)

    if updated:
        print(f"\nUpdated {len(updated)} benchmark(s): {', '.join(updated)}")
    else:
        print("\nNo updates needed.")


if __name__ == "__main__":
    main()
