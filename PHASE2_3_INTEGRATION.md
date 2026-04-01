# Phase 2.5 + Phase 3 Integration Guide

## Overview

**Phase 2.5:** Cloud sync backend (Vercel Functions)  
**Phase 3:** Local HubSpot push orchestration (desktop app side)

The architecture maintains **light cloud load** by design:
- Cloud server: only stores/syncs snapshots + commits (stateless, file-based)
- Local app: handles all HubSpot API work directly (contact/company/deal creation)
- No business logic on cloud; cloud is purely a data store

## Architecture Diagram

```
┌─────────────────────────────────────┐         ┌──────────────────────────────┐
│   LOCAL: Desktop Application        │         │  CLOUD: Vercel Functions     │
│   (hs_app.py + hubpush_core)        │         │  (stateless, file-based)     │
│                                     │         │                              │
│  ┌──────────────────────────────┐   │         │  ┌─────────────────────────┐ │
│  │ Phase 2: Sync Layer          │   │◄─────►  │  │ GET /api/v1/snapshot   │ │
│  │ - phase2_sync.py             │   │  JSON   │  │ POST /api/v1/snapshot  │ │
│  │ - cloud_client.py (local)    │   │◄─────►  │  │                         │ │
│  │ - cloud_emulator.py (dev)    │   │  JSON   │  │ GET /api/v1/commits    │ │
│  └──────────────────────────────┘   │         │  │ POST /api/v1/commits   │ │
│                 ▲                    │         │  │                         │ │
│                 │                    │         │  └─────────────────────────┘ │
│  ┌──────────────┴──────────────────┐ │         │         ▲                    │
│  │ Phase 3: HubSpot Service        │ │         │         │                    │
│  │ - hubspot_service.py            │ │         │   Vercel KV (Redis)          │
│  │ - find_contact()                │ │         │   or /tmp file storage       │
│  │ - create_company()              │ │         │                              │
│  │ - push_row() orchestrator       │ │         │                              │
│  │                                 │ │         │                              │
│  │     ┌──────────────────────┐    │ │         │                              │
│  │     │  HubSpot API v3/v4   │    │ │         │                              │
│  │     │  - POST /contacts    │    │ │         │                              │
│  │     │  - POST /companies   │    │ │         │                              │
│  │     │  - POST /deals       │    │ │         │                              │
│  │     │  - PUT /associations │    │ │         │                              │
│  │     │  - POST /files       │    │ │         │                              │
│  │     └──────────────────────┘    │ │         │                              │
│  └─────────────────────────────────┘ │         │                              │
│                                     │         │                              │
│  Data: master snapshot.json         │         │  Data: distributed copy      │
│        commit_history.json          │         │        for quick sync check  │
└─────────────────────────────────────┘         └──────────────────────────────┘
```

## Workflow: Pushing 23 Restaurants to HubSpot

```
1. Local App Loads Master Spreadsheet
   └─ 493 restaurants, status = "Ready To Push"
   └─ Master snapshot already in data/cloud_master_snapshot.json (Phase 1)

2. User Clicks "Commit to HubSpot" Button
   └─ App calls phase2_sync.py --mode pull --backend remote
      (if available) to check for remote updates
   └─ Get current cloud snapshot to detect conflicts
   └─ If cloud has newer status, warn user (e.g., another user pushed same row)

3. For Each "Ready To Push" Row → hubspot_service.push_row()
   └─ Example row:
      {
        "source subfolder": "Wimpy/0001",
        "company reg name": "Wimpy South Africa (Pty) Ltd",
        "company registration number": "2001234567",
        ...
      }

   └─ Step A: Classify documents (mandate vs bank proof)
      └─ Scan subfolder: 1.FBEO/1.FBEO/Wimpy/0001/
      └─ Find mandate*.pdf, bank confirmation.pdf

   └─ Step B: Find or Create Contact
      └─ POST /crm/v3/objects/contacts/search {"email": "..."}
      └─ If exists: reuse ID (no duplicates)
      └─ If not exists: POST /crm/v3/objects/contacts → create, get ID

   └─ Step C: Find or Create Company
      └─ POST /crm/v3/objects/companies/search {"registration": "..."}
      └─ If exists: reuse ID
      └─ If not exists: POST /crm/v3/objects/companies → create, get ID

   └─ Step D: Upload Documents
      └─ POST /files/v3/files [mandate.pdf]   → get mandate_url
      └─ POST /files/v3/files [bank_proof.pdf] → get bank_url

   └─ Step E: Create Deal with Files + Properties
      └─ POST /crm/v3/objects/deals {
           "dealname": "Wimpy - Sandton",
           "pipeline": "default",
           "dealstage": "appointmentscheduled",
           "debit_order_mandate": mandate_url,
           "bank_letter": bank_url,
           "brand__famous_brands_": "Wimpy",
           ...
         } → get deal_id

   └─ Step F: Associate Contact → Company
      └─ PUT /crm/v4/objects/contacts/{contact_id}/associations/companies/{company_id}

   └─ Step G: Associate Deal → Company
      └─ PUT /crm/v4/objects/deals/{deal_id}/associations/companies/{company_id}

   Return: HubSpotResult(ok=True, contact_id=..., company_id=..., deal_id=...)

4. Update Excel Spreadsheet
   └─ For each pushed row:
      └─ HubSpot Contact ID ← returned_contact_id
      └─ HubSpot Company ID ← returned_company_id
      └─ HubSpot Deal ID ← returned_deal_id
      └─ HubSpot Status ← "Pushed"
      └─ Last Push Timestamp ← now
      └─ Last Push Commit ID ← commit_id

5. Create Commit Record
   └─ Append to data/commit_history.events.jsonl:
      {
        "timestamp": "2026-04-01T12:34:56Z",
        "user": "admin",
        "action": "push",
        "restaurant_count": 23,
        "hubspot_ids_created": {"contacts": 5, "companies": 3, "deals": 23},
        "hubspot_ids_reused": {"contacts": 18, "companies": 20, "deals": 0},
        "result": "ok",
        "message": "Pushed 23 restaurants",
      }

6. Cloud Sync (Phase 2) - Optional
   └─ phase2_sync.py --mode push --backend remote
   └─ Send updated snapshot + new commit to Vercel
   └─ Other users can now see updated status

7. Output Report (Phase Output 3)
   └─ Generate summary CSV/Excel:
      - Restaurant Name, Contact ID, Company ID, Deal ID, Push Timestamp
      - 23 rows pushed successfully
```

## File Dependencies

```
hubpush_core/
├── __init__.py
├── data_model.py
│   ├─ build_cloud_row_id()          ← Generate deterministic row ID
│   ├─ compute_row_checksum()        ← Detect mutations
│   ├─ default_hubspot_status()      ← Infer "Ready To Push" from validation
│   └─ SYNC_COLUMNS[]                ← Column schema
├── sync_store.py
│   ├─ write_json()
│   ├─ read_json()
│   └─ append_jsonl()
├── cloud_client.py                   ← (Phase 2) HTTP client for Vercel
│   └─ CloudClient: push_snapshot(), fetch_commits(), etc.
├── cloud_emulator.py                 ← (Phase 2) Local file-based emulator
│   └─ LocalCloudEmulator: same interface as CloudClient
└─ hubspot_service.py                 ← (Phase 3) HubSpot orchestration
    ├─ HubSpotConfig                  ← API credentials + settings
    ├─ HubSpotService                 ← Main service class
    │   ├─ push_row()                 ← Full orchestration (9 steps)
    │   ├─ find_contact_by_email()
    │   ├─ create_company()
    │   ├─ upload_file()
    │   └─ ... 20+ helper methods
    └─ HubSpotResult                  ← Named tuple for structured results

phase2_sync.py                         ← (Phase 2) CLI for snapshot sync
└─ --mode {check|push|pull}
└─ --backend {local|remote|auto}

phase3_hubspot_examples.py             ← (Phase 3) Usage examples + dry-run demo
└─ example_batch_push()
└─ example_from_excel()
└─ ... 5 more examples

hs_app.py                              ← Main desktop app (Tkinter)
├─ Calls phase2_sync.py on pull
├─ Calls hubspot_service.push_row() on "Commit to HubSpot" button
└─ Updates Excel + generates commit record
```

## Configuration

### HubSpot API Token

1. Create a private app in HubSpot portal:
   - Settings → Integrations → Private Apps
   - Scopes: contacts, companies, deals, files, crm
   - Copy token

2. Set environment variable:
   ```powershell
   $env:HUBSPOTPAT = "pat-eu1-..."  # for testing
   ```
   Or hardcode in HubSpotConfig(token="...")

### Cloud Sync (Phase 2.5)

Once Vercel deployed:

1. Copy cloud.env.example to cloud.env
2. Set:
   ```
   HUBPUSH_CLOUD_BASE_URL=https://your-vercel-project.vercel.app
   HUBPUSH_CLOUD_API_KEY=<api-key-from-vercel-dashboard>
   HUBPUSH_PROJECT=hubpush
   ```

3. Test:
   ```powershell
   .\.venv\Scripts\python.exe phase2_sync.py --mode check --backend remote
   ```

## Testing Phase 3 (HubSpot Service)

### Test 1: Dry-Run Mode (No API Calls)

```powershell
.\.venv\Scripts\python.exe phase3_hubspot_examples.py
```

Runs example_dry_run() which simulates push without touching HubSpot.
Output:
```
Contact ID: DRY_RUN_CONTACT_ID
Company ID: DRY_RUN_COMPANY_ID
Deal ID: DRY_RUN_DEAL_ID
```

### Test 2: Live Push (Single Row)

```powershell
# Create minimal test script
$env:HUBSPOTPAT = "pat-eu1-..."

# In Python:
from pathlib import Path
from hubpush_core.hubspot_service import HubSpotConfig, HubSpotService

config = HubSpotConfig(token=$env:HUBSPOTPAT)
hs = HubSpotService(config)

row = {... from spreadsheet ...}
result = hs.push_row(row, Path(r"c:\Vibes\Hubpush\1.FBEO\1.FBEO"))

if result.ok:
    print(f"Success! Contact={result.contact_id}, Company={result.company_id}, Deal={result.deal_id}")
    # View in HubSpot: https://app.hubspot.com/contacts/145268660/deal/{result.deal_id}
```

### Test 3: Batch Push (First 5 Ready Rows)

Modify phase3_hubspot_examples.py or create batch_test.py:

```python
# Load first 5 "Ready To Push" rows
# Call hs.push_row() in a loop
# Collect results
# Print summary
```

## Next: Wiring to hs_app.py UI

Once Phase 3 is tested and working:

1. In hs_app.py, implement "Commit to HubSpot" button handler:
   ```python
   def on_commit_click():
       # Load "Ready To Push" rows from spreadsheet
       # For each row: call hubspot_service.push_row()
       # Update Excel with returned IDs + status
       # Create commit record
       # Sync to cloud (phase2_sync.py)
       # Show summary to user
   ```

2. Status updates during push:
   ```python
   # Right pane shows:
   # "Pushing 1/23..." with progress bar
   # Contact ID: ___
   # Company ID: ___
   # Deal ID: ___
   # Link to HubSpot deal
   ```

3. Undo support (Phase 6):
   ```python
   def on_undo_click(commit_id):
       # Load which deals/companies/contacts were created by this commit
       # DELETE them in HubSpot (archive)
       # Mark commit as "Undone" in commit history
       # Reset Excel rows to "Not Ready" status
   ```

## Dry-Run Testing

The HubSpotService supports dry-run mode at both service and row level:

```python
# Service-level dry-run (all operations simulate)
hs = HubSpotService(HubSpotConfig(..., dry_run=True))

# Per-row override
result = hs.push_row(row, file_root, dry_run=True)  # Even with service dry_run=False
```

Dry-run mode:
- Logs all intended API calls
- Returns mock IDs (DRY_RUN_CONTACT_ID, etc.)
- Validates file paths and data without making HTTP requests
- Useful for safe testing before going live

---

**Ready to proceed?** Once you:

1. ✅ Deploy to Vercel (Phase 2.5) - test Vercel endpoints
2. ✅ Test hubspot_service.py dry-run (Phase 3) - confirm document classification
3. ✅ Provide HubSpot API token - run live test on 1-2 rows

Then we can wire "Commit to HubSpot" button in hs_app.py (Phase 5) and build the complete end-to-end workflow.
