# Audit Fixes — 2026-02-18

## Completed

### 1. ✅ Secured API keys
- Moved `keys.json` → `/root/.secrets/gemini_keys.json` (chmod 600)
- Updated `key_manager.py` to read from new path
- Deleted `keys.json` from workspace (no longer served on :8000)

### 2. ✅ Secured HTTP server
- Created `/root/.openclaw/workspace/public/` with only `graph.html`, `graph_data.json`, `index.html`
- Updated `graph-server.service` to serve from `public/` only
- Added `EnvironmentFile=/root/.secrets/jarvis_env`
- Restarted service — confirmed running

### 3. ✅ Moved hardcoded credentials to env vars
- `collector_cron.py`: replaced hardcoded `API_TOKEN` with `os.environ.get("OPENCLAW_API_TOKEN", "")`
- Created `/root/.secrets/jarvis_env` with `OPENCLAW_API_TOKEN` and `PG_DSN`

### 4. ✅ Archived dead code (22 files)
Moved to `_archive/`:
- Scripts: `export_d3.py`, `import_telegram.py`, `generate_system_b.py`, `analyze_love.py`, `cleanup_metrics.py`, `cleanup_routine.py`, `remove_decisions.py`, `restore_principles.py`, `jarvis_system.py`
- Data: `raw.txt`, `analysis.jsonl`, `tunnel.pid`, `server.pid`, `ngrok.log`, `old_graph.html`, `graph_legacy.html`, `graph_system_b.html`, `old_context_graph.md`, `chat_history.json`, `chat.json`, `chats.json`
- Config: `docker-compose.yml`

### 5. ✅ Cleaned unused pip packages
Removed: neo4j, langchain-core, langchain-text-splitters, langsmith, openai, telethon, xxhash, zstandard, numpy, requests-toolbelt
Re-installed `websockets` and `requests` (required by google-genai).
Verified: `from google import genai` works.

### 6. ✅ Fixed jarvis_system.py
Moved entire file to `_archive/` — most commands required PostgreSQL (not running).

### 7. ✅ Removed docker-compose.yml
Moved to `_archive/`.

### 8. ✅ Git commits
- Pre-change snapshot commit
- Final commit: "audit: fix critical security issues, archive dead code, clean dependencies"
