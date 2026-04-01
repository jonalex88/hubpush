from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class CloudConfig:
    base_url: str = ""
    api_key: str = ""
    project: str = "hubpush"
    timeout_seconds: int = 25

    @staticmethod
    def from_env() -> "CloudConfig":
        return CloudConfig(
            base_url=os.getenv("HUBPUSH_CLOUD_BASE_URL", "").strip(),
            api_key=os.getenv("HUBPUSH_CLOUD_API_KEY", "").strip(),
            project=os.getenv("HUBPUSH_PROJECT", "hubpush").strip() or "hubpush",
        )


class CloudClient:
    """HTTP client for Vercel-hosted HubPush sync API.

    API contract expected:
      GET    /api/v1/snapshot?project=<name>
      POST   /api/v1/snapshot
      GET    /api/v1/commits?project=<name>
      POST   /api/v1/commits
      GET    /api/v1/health
    """

    def __init__(self, config: CloudConfig):
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(self.config.base_url)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["x-api-key"] = self.config.api_key
        return headers

    def _url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}{path}"

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("Cloud client disabled: HUBPUSH_CLOUD_BASE_URL not configured")

        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")

        req = urllib.request.Request(
            self._url(path),
            data=body,
            method=method,
            headers=self._headers(),
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                if not raw.strip():
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Cloud HTTP {exc.code} {path}: {err_body[:400]}") from exc

    def health(self) -> dict[str, Any]:
        return self._request_json("GET", "/api/v1/health")

    def fetch_snapshot(self) -> dict[str, Any]:
        project = self.config.project
        return self._request_json("GET", f"/api/v1/snapshot?project={project}")

    def push_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        payload = {"project": self.config.project, "snapshot": snapshot}
        return self._request_json("POST", "/api/v1/snapshot", payload)

    def fetch_commits(self) -> dict[str, Any]:
        project = self.config.project
        return self._request_json("GET", f"/api/v1/commits?project={project}")

    def append_commit(self, commit_entry: dict[str, Any]) -> dict[str, Any]:
        payload = {"project": self.config.project, "commit": commit_entry}
        return self._request_json("POST", "/api/v1/commits", payload)
