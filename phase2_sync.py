from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hubpush_core.cloud_client import CloudClient, CloudConfig
from hubpush_core.cloud_emulator import LocalCloudEmulator
from hubpush_core.sync_store import read_json


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def index_rows(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in snapshot.get("rows", []):
        row_id = str(row.get("Cloud Row ID", "")).strip()
        if row_id:
            out[row_id] = row
    return out


def summarize_status(snapshot: dict[str, Any]) -> dict[str, int]:
    counts = Counter()
    for row in snapshot.get("rows", []):
        counts[str(row.get("HubSpot Status", "")).strip() or "(blank)"] += 1
    return dict(counts)


def diff_snapshots(local_snap: dict[str, Any], cloud_snap: dict[str, Any]) -> dict[str, int]:
    local_idx = index_rows(local_snap)
    cloud_idx = index_rows(cloud_snap)

    local_ids = set(local_idx)
    cloud_ids = set(cloud_idx)

    only_local = local_ids - cloud_ids
    only_cloud = cloud_ids - local_ids
    in_both = local_ids & cloud_ids

    checksum_mismatch = 0
    for row_id in in_both:
        if local_idx[row_id].get("Row Checksum") != cloud_idx[row_id].get("Row Checksum"):
            checksum_mismatch += 1

    return {
        "local_rows": len(local_ids),
        "cloud_rows": len(cloud_ids),
        "only_local": len(only_local),
        "only_cloud": len(only_cloud),
        "checksum_mismatch": checksum_mismatch,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2 cloud sync bootstrap")
    parser.add_argument(
        "--local-snapshot",
        default=r"c:\Vibes\Hubpush\data\cloud_master_snapshot.json",
        help="Path to local snapshot JSON produced by phase1_init",
    )
    parser.add_argument(
        "--mode",
        choices=["push", "pull", "check"],
        default="check",
        help="Sync mode: push local->cloud, pull cloud->local, or check drift",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "local", "remote"],
        default="auto",
        help="Cloud backend: local emulator, remote Vercel API, or auto",
    )
    parser.add_argument(
        "--project",
        default="hubpush",
        help="Project key for cloud partitioning",
    )
    args = parser.parse_args()

    local_snapshot_path = Path(args.local_snapshot)
    local_snapshot = read_json(local_snapshot_path, {})
    if not local_snapshot:
        raise FileNotFoundError(f"Local snapshot not found or invalid: {local_snapshot_path}")

    # Backend selection.
    client = None
    if args.backend in {"auto", "remote"}:
        remote = CloudClient(CloudConfig.from_env())
        if remote.enabled:
            client = remote
        elif args.backend == "remote":
            raise RuntimeError("Remote backend requested but HUBPUSH_CLOUD_BASE_URL is not configured")

    if client is None:
        client = LocalCloudEmulator(Path(r"c:\Vibes\Hubpush\data\cloud_emulator"), project=args.project)

    print("Backend:", client.health())

    if args.mode == "push":
        local_snapshot["cloud_synced_at"] = now_iso()
        result = client.push_snapshot(local_snapshot)
        print("Push result:", result)
        print("Status counts:", summarize_status(local_snapshot))
        return

    if args.mode == "pull":
        cloud_snapshot = client.fetch_snapshot()
        if not cloud_snapshot.get("rows"):
            print("Pull result: cloud snapshot empty, local file unchanged")
            return
        cloud_snapshot["pulled_at"] = now_iso()
        local_snapshot_path.write_text(__import__("json").dumps(cloud_snapshot, indent=2, ensure_ascii=True), encoding="utf-8")
        print("Pull result: wrote local snapshot")
        print("Status counts:", summarize_status(cloud_snapshot))
        return

    cloud_snapshot = client.fetch_snapshot()
    if not cloud_snapshot.get("rows"):
        print("Check result: cloud snapshot empty (nothing to compare yet)")
        print("Local status counts:", summarize_status(local_snapshot))
        return

    drift = diff_snapshots(local_snapshot, cloud_snapshot)
    print("Drift check:", drift)
    print("Local status counts:", summarize_status(local_snapshot))
    print("Cloud status counts:", summarize_status(cloud_snapshot))


if __name__ == "__main__":
    main()
