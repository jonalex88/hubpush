"""
Auth client — talks to Vercel /api/v1/users and /api/v1/auth endpoints.
All credentials stay on the Vercel server; PINs are never sent in plain text
over the network for storage — they are only sent for a single validation call.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import NamedTuple


class AuthConfig(NamedTuple):
    base_url: str
    api_key: str = ""
    project: str = "hubpush"

    @classmethod
    def from_env(cls) -> "AuthConfig":
        base = os.getenv("HUBPUSH_CLOUD_BASE_URL", "").rstrip("/")
        key = os.getenv("HUBPUSH_CLOUD_API_KEY", "")
        project = os.getenv("HUBPUSH_PROJECT", "hubpush")
        return cls(base_url=base, api_key=key, project=project)


class AuthClient:
    """HTTP client for the authentication endpoints on Vercel."""

    def __init__(self, config: AuthConfig):
        self.config = config

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "Content-Type": "application/json",
            "X-Project": self.config.project,
        }
        if self.config.api_key:
            h["X-API-Key"] = self.config.api_key
        return h

    def get_users(self) -> list[str]:
        """
        Fetch the list of usernames from the cloud (no PINs returned).
        Falls back to hardcoded list if the server is unreachable.
        """
        if not self.config.base_url:
            return _FALLBACK_USERS[:]

        url = f"{self.config.base_url}/api/v1/users"
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                users = data.get("users", [])
                if isinstance(users, list) and users:
                    return users
        except Exception:
            pass
        return _FALLBACK_USERS[:]

    def login(self, username: str, pin: str) -> tuple[bool, str]:
        """
        Validate username + PIN against the cloud store.
        Returns (ok, error_message).
        PIN is sent over HTTPS for server-side HMAC validation only.
        """
        if not self.config.base_url:
            return False, "Cloud authentication server not configured.\nSet HUBPUSH_CLOUD_BASE_URL."

        url = f"{self.config.base_url}/api/v1/auth"
        body = json.dumps({"username": username, "pin": pin}).encode()
        req = urllib.request.Request(
            url, data=body, headers=self._headers(), method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                if data.get("ok"):
                    return True, ""
                return False, data.get("error", "Invalid PIN")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return False, "Invalid PIN"
            return False, f"Server error ({e.code})"
        except Exception as e:
            return False, f"Could not reach authentication server:\n{e}"


# Fallback username list shown when the server is unreachable.
# These are display names only — login will still require server validation.
_FALLBACK_USERS: list[str] = [
    "Yusuf S",
    "Michelle",
    "Meehgan",
    "Jonathan",
    "AD",
    "Cheslin",
]
