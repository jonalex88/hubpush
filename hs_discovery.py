"""
Read-only HubSpot discovery script.
Fetches: deal pipelines/stages, deal properties, contact properties, company properties.
"""
import json
import os
import urllib.request
import urllib.error

TOKEN = os.getenv("HUBSPOT_API_TOKEN", "")
BASE = "https://api.hubapi.com"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def get(path: str, params: str = "") -> dict:
    url = f"{BASE}{path}"
    if params:
        url += f"?{params}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  HTTP {e.code} on {path}: {body[:400]}")
        return {}


# ── 1. Deal pipelines ────────────────────────────────────────────────────────
if not TOKEN:
    print("ERROR: HUBSPOT_API_TOKEN is not set.")
    raise SystemExit(1)

print("\n=== DEAL PIPELINES ===")
pipelines_resp = get("/crm/v3/pipelines/deals")
for pl in pipelines_resp.get("results", []):
    print(f"  Pipeline: id={pl['id']}  label={pl['label']}")
    for st in pl.get("stages", []):
        print(f"    Stage: id={st['id']}  label={st['label']}")

# ── 2. Deal properties ───────────────────────────────────────────────────────
print("\n=== DEAL PROPERTIES (name | label) ===")
deal_props = get("/crm/v3/properties/deals")
for p in deal_props.get("results", []):
    print(f"  {p['name']}  |  {p['label']}")

# ── 3. Contact properties ────────────────────────────────────────────────────
print("\n=== CONTACT PROPERTIES (name | label) ===")
contact_props = get("/crm/v3/properties/contacts")
for p in contact_props.get("results", []):
    print(f"  {p['name']}  |  {p['label']}")

# ── 4. Company properties ────────────────────────────────────────────────────
print("\n=== COMPANY PROPERTIES (name | label) ===")
company_props = get("/crm/v3/properties/companies")
for p in company_props.get("results", []):
    print(f"  {p['name']}  |  {p['label']}")
