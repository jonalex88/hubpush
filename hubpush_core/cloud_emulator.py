from __future__ import annotations

from pathlib import Path
from typing import Any

from hubpush_core.sync_store import read_json, write_json


class LocalCloudEmulator:
    """File-based cloud emulator used before Vercel is deployed.

    Keeps API-compatible methods with CloudClient for easy switch-over.
    """

    def __init__(self, root: Path, project: str = "hubpush"):
        self.root = root
        self.project = project
        self.root.mkdir(parents=True, exist_ok=True)

    @property
    def _snapshot_path(self) -> Path:
        return self.root / f"{self.project}.snapshot.json"

    @property
    def _commits_path(self) -> Path:
        return self.root / f"{self.project}.commits.json"

    def health(self) -> dict[str, Any]:
        return {"ok": True, "backend": "local-emulator", "project": self.project}

    def fetch_snapshot(self) -> dict[str, Any]:
        return read_json(self._snapshot_path, {"schema_version": 1, "rows": [], "row_count": 0})

    def push_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        write_json(self._snapshot_path, snapshot)
        return {"ok": True, "row_count": snapshot.get("row_count", 0)}

    def fetch_commits(self) -> dict[str, Any]:
        return read_json(self._commits_path, {"schema_version": 1, "commits": []})

    def append_commit(self, commit_entry: dict[str, Any]) -> dict[str, Any]:
        payload = self.fetch_commits()
        commits = payload.setdefault("commits", [])
        commits.append(commit_entry)
        write_json(self._commits_path, payload)
        return {"ok": True, "count": len(commits)}
