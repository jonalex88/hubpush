"""
Upload files and patch them to the existing deal from the test run.
"""
import json
import mimetypes
import os
import urllib.request
import urllib.error
from pathlib import Path

TOKEN = os.getenv("HUBSPOT_API_TOKEN", "")
BASE = "https://api.hubapi.com"
ROOT = Path(r"c:\Vibes\Hubpush\1.FBEO\1.FBEO")
SUBFOLDER = "FBEO-106"
DEAL_ID = "496821464278"

AUTH_HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

MANDATE_KEYS = ("mandate", "debit", "order")
BANK_KEYS = ("bank", "account", "confirmation", "proof", "statement")
SUPPORTED_DOC_EXTS = {".pdf", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def upload_file(file_path: Path, folder_path: str = "/hubpush") -> str | None:
    print(f"   Uploading: {file_path.name}")
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    file_bytes = file_path.read_bytes()

    boundary = "HubPushBoundary7MA4YWxkTrZu0gW"
    CRLF = b"\r\n"

    def part_text(name: str, value: str) -> bytes:
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}"
        ).encode() + CRLF

    options = json.dumps({
        "access": "PUBLIC_INDEXABLE",
        "overwrite": False,
        "duplicateValidationStrategy": "NONE",
        "duplicateValidationScope": "ENTIRE_PORTAL",
    })

    body = (
        part_text("folderPath", folder_path)
        + part_text("options", options)
        + (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode()
        + file_bytes
        + CRLF
        + f"--{boundary}--\r\n".encode()
    )

    upload_headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }

    req = urllib.request.Request(
        f"{BASE}/files/v3/files",
        data=body,
        headers=upload_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            file_url = result.get("url") or result.get("id")
            print(f"       ✓ Uploaded: {file_url}")
            return str(file_url) if file_url else None
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"       ✗ HTTP {e.code}: {err[:300]}")
        return None


def patch_deal(property_name: str, property_value: str) -> bool:
    print(f"   Patching deal property: {property_name}")
    req = urllib.request.Request(
        f"{BASE}/crm/v3/objects/deals/{DEAL_ID}",
        data=json.dumps({"properties": {property_name: property_value}}).encode(),
        headers=AUTH_HEADERS,
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read())
            print(f"       ✓ Patched")
            return True
    except urllib.error.HTTPError as e:
        print(f"       ✗ HTTP {e.code}: {e.read().decode()[:300]}")
        return False


def classify_folder_docs(folder: Path) -> tuple[Path | None, Path | None]:
    docs = sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_DOC_EXTS],
        key=lambda p: p.name.lower(),
    )
    mandate = next((d for d in docs if any(k in d.name.lower() for k in MANDATE_KEYS)), None)
    bank = next((d for d in docs if any(k in d.name.lower() for k in BANK_KEYS)), None)
    if not mandate:
        non_bank = [d for d in docs if not any(k in d.name.lower() for k in BANK_KEYS)]
        mandate = next((d for d in non_bank if d.suffix.lower() == ".pdf"), None)
        if not mandate:
            mandate = next((d for d in docs if d.suffix.lower() == ".pdf" and d != bank), None)
    if not bank:
        bank = next((d for d in docs if d != mandate), None)
    return mandate, bank


print("\n" + "=" * 60)
if not TOKEN:
    print("ERROR: HUBSPOT_API_TOKEN is not set.")
    raise SystemExit(1)

print(f"  Uploading files for FBEO-106 -> Deal {DEAL_ID}")
print("=" * 60)

folder_path = ROOT / SUBFOLDER
mandate_file, bank_file = classify_folder_docs(folder_path)

print(f"\n✓ Resolved files:")
print(f"  Mandate:    {mandate_file.name if mandate_file else 'NOT FOUND'}")
print(f"  Bank proof: {bank_file.name if bank_file else 'NOT FOUND'}")

mandate_url = None
bank_url = None

if mandate_file:
    print(f"\n[1/2] Uploading mandate...")
    mandate_url = upload_file(mandate_file)

if bank_file:
    print(f"\n[2/2] Uploading bank proof...")
    bank_url = upload_file(bank_file)

if mandate_url:
    print(f"\n[3/2] Patching deal with file URLs...")
    patch_deal("debit_order_mandate", mandate_url)

if bank_url:
    patch_deal("bank_letter", bank_url)

print("\n" + "=" * 60)
print(f"  DONE - View deal: https://app.hubspot.com/contacts/145268660/deal/{DEAL_ID}")
print("=" * 60)
