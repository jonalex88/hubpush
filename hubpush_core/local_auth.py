from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple


class LocalAuthResult(NamedTuple):
    ok: bool
    error: str = ""


class LocalAuthStore:
    """Simple local username/PIN store backed by a JSON file."""

    def __init__(self, file_path: Path | str):
        self.file_path = Path(file_path)

    def _read_users(self) -> list[dict[str, str]]:
        if not self.file_path.exists():
            return []
        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def get_users(self) -> list[str]:
        return [str(item.get("username", "")).strip() for item in self._read_users() if str(item.get("username", "")).strip()]

    def login(self, username: str, pin: str) -> LocalAuthResult:
        username = username.strip()
        pin = pin.strip()
        if not username or not pin:
            return LocalAuthResult(False, "Username and PIN are required.")

        for item in self._read_users():
            stored_user = str(item.get("username", "")).strip()
            stored_pin = str(item.get("pin", "")).strip()
            if stored_user.lower() == username.lower():
                if stored_pin == pin:
                    return LocalAuthResult(True, "")
                return LocalAuthResult(False, "Invalid PIN")
        return LocalAuthResult(False, "Unknown user")
