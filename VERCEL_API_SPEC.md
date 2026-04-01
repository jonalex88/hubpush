"""
Phase 2.5: Vercel Cloud Sync API - Implementation Specification

This document defines the HTTP API contract for the cloud sync backend.
The API is stateless and file-based, hosting a distributed snapshot of the master
spreadsheet for conflict detection and audit logging.

DEPLOYMENT TARGET: Vercel Functions (Node.js 18+)
FRAMEWORK: Express.js (minimal, just 3 endpoints)
STORAGE: Vercel KV (Redis) or file system in /tmp (ephemeral)

┌─────────────────────────────────────────────────────────────────────────┐
│ ENDPOINTS                                                               │
├─────────────────────────────────────────────────────────────────────────┤
│ POST   /api/v1/health           Check API availability                 │
│ GET    /api/v1/snapshot         Fetch current cloud snapshot            │
│ POST   /api/v1/snapshot         Push updated snapshot from local        │
│ GET    /api/v1/commits          Fetch commit history                    │
│ POST   /api/v1/commits          Append a new commit record              │
└─────────────────────────────────────────────────────────────────────────┘

AUTHENTICATION:
  - Header: X-API-Key (provided in HUBPUSH_CLOUD_API_KEY env var)
  - Project: X-Project (provided in HUBPUSH_PROJECT env var, default: "hubpush")

STORAGE BACKENDS:
  - Default: Vercel KV (Redis) - production, replicated, durable
  - Fallback: /tmp file-based JSON (development, ephemeral per cold start)

RATE LIMITS:
  - 10 requests per second per API key
  - 1 MB max request body
"""

# ────────────────────────────────────────────────────────────────────────────
# Example Node.js/Express Implementation (deploy to Vercel)
# ────────────────────────────────────────────────────────────────────────────

"""
FILE: /api/v1/health.js
PURPOSE: Health check endpoint (no auth required for debugging)
RESPONSE:
  {
    "ok": true,
    "backend": "vercel-kv" or "file-based",
    "project": "hubpush",
    "timestamp": "2026-04-01T12:34:56Z"
  }
"""

# FILE: api/v1/health.js
/*
export default async (req, res) => {
  const backend = process.env.KV_REST_API_URL ? "vercel-kv" : "file-based";
  res.json({
    ok: true,
    backend,
    project: process.env.HUBPUSH_PROJECT || "hubpush",
    timestamp: new Date().toISOString(),
  });
};
*/

# ────────────────────────────────────────────────────────────────────────────

"""
FILE: /api/v1/snapshot.js
PURPOSE: 
  - GET: Fetch current cloud snapshot (493 restaurants + sync metadata)
  - POST: Push full snapshot from local (atomic, replaces entire dataset)

GET /api/v1/snapshot
  Query: (none)
  Auth: X-API-Key, X-Project
  Response:
    {
      "ok": true,
      "row_count": 493,
      "snapshot": [
        {
          "Cloud Row ID": "abc123...",
          "Row Checksum": "def456...",
          "source subfolder": "...",
          "company reg name": "...",
          ...all fields from Excel row...
          "HubSpot Status": "Ready To Push",
          "HubSpot Contact ID": null,
          "Last Push Commit ID": null,
        },
        ...
      ],
      "timestamp": "2026-04-01T12:34:56Z"
    }

POST /api/v1/snapshot
  Auth: X-API-Key, X-Project
  Body:
    {
      "action": "push" or "replace",
      "rows": [ ... 493 row objects ... ],
      "timestamp": "2026-04-01T12:34:56Z"
    }
  Response:
    {
      "ok": true,
      "row_count": 493,
      "timestamp": "2026-04-01T12:34:56Z"
    }
"""

# FILE: api/v1/snapshot.js (simplified pseudocode)
/*
import { kv } from "@vercel/kv";

async function getSnapshot(project) {
  try {
    const key = `snapshot:${project}`;
    const data = await kv.get(key);
    return data || { rows: [] };
  } catch (e) {
    // Fallback to empty if no KV
    return { rows: [] };
  }
}

async function setSnapshot(project, snapshot) {
  const key = `snapshot:${project}`;
  // KV string limits: store as JSON string
  await kv.set(key, JSON.stringify(snapshot), { ex: 86400 * 30 }); // 30 days
  return true;
}

export default async (req, res) => {
  const project = req.headers["x-project"] || "hubpush";
  const apiKey = req.headers["x-api-key"];
  
  // Verify API key
  if (apiKey !== process.env.HUBPUSH_CLOUD_API_KEY) {
    return res.status(401).json({ ok: false, error: "Unauthorized" });
  }

  if (req.method === "GET") {
    const data = await getSnapshot(project);
    return res.json({
      ok: true,
      row_count: data.rows?.length || 0,
      snapshot: data.rows || [],
      timestamp: new Date().toISOString(),
    });
  }

  if (req.method === "POST") {
    const { rows } = req.body;
    if (!Array.isArray(rows)) {
      return res.status(400).json({ ok: false, error: "rows must be array" });
    }
    
    const snapshot = { rows, updated_at: new Date().toISOString() };
    await setSnapshot(project, snapshot);
    
    return res.json({
      ok: true,
      row_count: rows.length,
      timestamp: snapshot.updated_at,
    });
  }

  res.status(405).json({ ok: false, error: "Method not allowed" });
};
*/

# ────────────────────────────────────────────────────────────────────────────

"""
FILE: /api/v1/commits.js
PURPOSE:
  - GET: Fetch commit history log (audit trail)
  - POST: Append a new commit record (immutable)

GET /api/v1/commits
  Query: ?limit=100 (default: all)
  Auth: X-API-Key, X-Project
  Response:
    {
      "ok": true,
      "commits": [
        {
          "id": "commit-2026-04-01-001",
          "timestamp": "2026-04-01T12:34:56Z",
          "user": "admin",
          "action": "push",
          "restaurant_count": 23,
          "hubspot_ids_created": { "contacts": 5, "companies": 3, "deals": 3 },
          "hubspot_ids_reused": { "contacts": 18, "companies": 20, "deals": 20 },
          "result": "ok",
          "message": "Pushed 23 restaurants",
          "undo_status": "none"
        },
        ...
      ],
      "timestamp": "2026-04-01T12:34:56Z"
    }

POST /api/v1/commits
  Auth: X-API-Key, X-Project
  Body:
    {
      "user": "admin",
      "action": "push",
      "restaurant_count": 23,
      "hubspot_ids_created": { "contacts": 5, "companies": 3, "deals": 3 },
      "hubspot_ids_reused": { "contacts": 18, "companies": 20, "deals": 20 },
      "result": "ok",
      "message": "Pushed 23 restaurants",
    }
  Response:
    {
      "ok": true,
      "commit_id": "commit-2026-04-01-001",
      "timestamp": "2026-04-01T12:34:56Z"
    }
"""

# FILE: api/v1/commits.js (simplified pseudocode)
/*
import { kv } from "@vercel/kv";

async function getCommits(project, limit = null) {
  try {
    const key = `commits:${project}`;
    const data = await kv.get(key);
    let commits = data ? JSON.parse(data) : [];
    if (limit) commits = commits.slice(-limit);
    return commits;
  } catch (e) {
    return [];
  }
}

async function appendCommit(project, commitData) {
  const key = `commits:${project}`;
  const commits = await getCommits(project);
  
  const commit = {
    id: `commit-${new Date().toISOString().split("T")[0]}-${String(commits.length + 1).padStart(3, "0")}`,
    timestamp: new Date().toISOString(),
    ...commitData,
    undo_status: "none",
  };
  
  commits.push(commit);
  await kv.set(key, JSON.stringify(commits), { ex: 86400 * 365 }); // 1 year
  return commit;
}

export default async (req, res) => {
  const project = req.headers["x-project"] || "hubpush";
  const apiKey = req.headers["x-api-key"];
  
  if (apiKey !== process.env.HUBPUSH_CLOUD_API_KEY) {
    return res.status(401).json({ ok: false, error: "Unauthorized" });
  }

  if (req.method === "GET") {
    const limit = req.query.limit ? parseInt(req.query.limit) : null;
    const commits = await getCommits(project, limit);
    return res.json({
      ok: true,
      commits,
      timestamp: new Date().toISOString(),
    });
  }

  if (req.method === "POST") {
    const commit = await appendCommit(project, req.body);
    return res.json({
      ok: true,
      commit_id: commit.id,
      timestamp: commit.timestamp,
    });
  }

  res.status(405).json({ ok: false, error: "Method not allowed" });
};
*/

# ────────────────────────────────────────────────────────────────────────────
# DEPLOYMENT STEPS
# ────────────────────────────────────────────────────────────────────────────

"""
1. CREATE VERCEL PROJECT:
   $ vercel init hubpush-cloud
   (Choose "Other" template, then manually add files)

2. PROJECT STRUCTURE:
   hubpush-cloud/
   ├── api/
   │   └── v1/
   │       ├── health.js
   │       ├── snapshot.js
   │       └── commits.js
   ├── vercel.json
   ├── package.json
   └── .env.example

3. INSTALL VERCEL KV:
   $ npm install @vercel/kv

4. ENABLE VERCEL KV IN PROJECT:
   $ vercel env add KV_REST_API_URL
   $ vercel env add KV_REST_API_TOKEN
   (Copy from Vercel dashboard: Storage > KV)

5. ENV VARIABLES (set in Vercel. Dashboard):
   HUBPUSH_CLOUD_API_KEY = <random-256-char-key>
   HUBPUSH_PROJECT = "hubpush"

6. DEPLOY:
   $ vercel deploy --prod

7. TEST:
   curl -H "X-API-Key: <your-key>" \\
        https://hubpush-cloud.vercel.app/api/v1/health

8. UPDATE LOCAL ENV:
   Create file: cloud.env
   HUBPUSH_CLOUD_BASE_URL=https://hubpush-cloud.vercel.app
   HUBPUSH_CLOUD_API_KEY=<your-key>
   HUBPUSH_PROJECT=hubpush

9. TEST LOCAL SYNC:
   .\.venv\Scripts\python.exe phase2_sync.py --mode check --backend remote
"""

# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE PACKAGE.JSON
# ────────────────────────────────────────────────────────────────────────────

"""
{
  "name": "hubpush-cloud",
  "version": "1.0.0",
  "description": "HubPush cloud sync API",
  "scripts": {
    "dev": "vercel dev",
    "build": "vercel build",
    "deploy": "vercel deploy --prod"
  },
  "dependencies": {
    "@vercel/kv": "^0.2.1"
  },
  "keywords": ["hubspot", "sync", "vercel"]
}
"""

# ────────────────────────────────────────────────────────────────────────────
# EXAMPLE VERCEL.JSON
# ────────────────────────────────────────────────────────────────────────────

"""
{
  "functions": {
    "api/v1/*.js": {
      "maxDuration": 30,
      "memory": 512,
      "middleware": []
    }
  },
  "env": {
    "HUBPUSH_CLOUD_API_KEY": "@hubpush_cloud_api_key",
    "HUBPUSH_PROJECT": "hubpush"
  },
  "redirects": [
    {
      "source": "/",
      "destination": "/api/v1/health",
      "permanent": false
    }
  ]
}
"""

# ────────────────────────────────────────────────────────────────────────────
# PYTHON CLIENT COMPATIBILITY
# ────────────────────────────────────────────────────────────────────────────

"""
The CloudClient in hubpush_core/cloud_client.py is already compatible:

Usage:
  config = CloudConfig.from_env()  # reads HUBPUSH_CLOUD_BASE_URL, HUBPUSH_CLOUD_API_KEY
  client = CloudClient(config)
  
  # Health check
  result = client.health()  # {"ok": true, "backend": "vercel-kv", ...}
  
  # Test snapshot push/pull
  rows = client.fetch_snapshot()
  client.push_snapshot(rows)
  
  # Commits
  commits = client.fetch_commits()
  client.append_commit(...)

Once Vercel deployment is ready:
  1. Get base URL: https://hubpush-cloud.vercel.app
  2. Get API key from Vercel dashboard
  3. Create cloud.env file in workspace:
     HUBPUSH_CLOUD_BASE_URL=https://hubpush-cloud.vercel.app
     HUBPUSH_CLOUD_API_KEY=<your-key>
  4. Run: .\.\.venv\Scripts\python.exe phase2_sync.py --mode check --backend remote
"""
