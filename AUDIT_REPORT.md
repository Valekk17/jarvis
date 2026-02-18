# 🔍 JARVIS Infrastructure Audit Report

**Date:** 2026-02-18  
**Server:** vm261949.hosted-by-robovps.com  
**Auditor:** Subagent (Claude Opus 4.6)

---

## Executive Summary

The workspace contains a **personal AI assistant system ("JARVIS")** built around:
1. **Telegram message monitoring** → Gemini LLM extraction → Markdown knowledge graph
2. **Voice note processing** (Whisper transcription → entity extraction)
3. **D3.js graph visualization** served via HTTP
4. A **Squish Memory** TypeScript app (third-party memory plugin for Claude Code)

### Critical Findings
- 🔴 **API keys exposed in plaintext** (`keys.json` — 5 Google AI API keys)
- 🔴 **Database credentials hardcoded** across 4+ files (`jarvis_password`)
- 🔴 **PostgreSQL not running** (Docker not active), but 4 scripts depend on it
- 🔴 **Broken imports**: `import_telegram.py` imports non-existent `extract_graph` module; `jarvis_system.py` imports non-existent `embedding_util`
- 🟡 **Dead code**: Multiple one-off cleanup scripts that served their purpose
- 🟡 **`graph-server.service`** serves entire workspace on port 8000 with **no auth, no TLS** — exposes all files including `keys.json`
- 🟡 **voice_watcher.py** is running but depends on Whisper (not confirmed installed)

### Health Score: 4/10
The system has good architectural ideas but poor operational hygiene. Half the infrastructure (PostgreSQL, Neo4j deps) is non-functional. Security is critically weak.

---

## File-by-File Analysis

### Python Files (20 files, 2,708 lines total)

| File | Lines | Purpose | Status | Issues |
|---|---|---|---|---|
| `key_manager.py` | 43 | Rotates Gemini API keys from `keys.json` | ✅ Active, used by many scripts | Keys in plaintext file |
| `collector_cron.py` | 440 | **Core**: Reads Telegram chats, extracts entities via Gemini, updates graph, sends auto-replies, morning greetings, dashboard | ⚠️ Functional but not scheduled (no cron) | Hardcoded API token (line 16), hardcoded chat IDs, sends automated "love" messages, contains an OpenClaw API token |
| `gemini_cli.py` | 268 | CLI tool: ask/translate/extract/audio/summarize via Gemini | ✅ Well-structured | `MODELS` list mutated in-place (shared state bug) |
| `voice_watcher.py` | 138 | Watches `/root/.openclaw/media/inbound` for audio, transcribes with Whisper, extracts entities | ⚠️ Running (PID 2361698) | Depends on `whisper` CLI (may not be installed); writes to graph without dedup |
| `sync_tasks.py` | 110 | Two-way sync: Obsidian task files ↔ context_graph.md | ✅ OK | Called by collector_cron |
| `generate_canvas.py` | 281 | Parses context_graph.md → D3.js HTML visualization | ✅ OK | Hardcoded family relationships; outputs to stdout |
| `jarvis_system.py` | 250 | Unified CLI: collect/search/status/export/rebuild-md/decay | 🔴 Partially broken | `cmd_search` imports non-existent `embedding_util`; all DB commands fail (no PostgreSQL) |
| `jarvis_extractor.py` | 161 | Extracts entities from text → saves to jarvis/memory/*.md | ⚠️ Functional | Uses deprecated `google.generativeai` only (no new API fallback) |
| `export_d3.py` | 24 | Exports PostgreSQL graph_nodes/edges to JSON | 🔴 Broken | PostgreSQL not running |
| `import_telegram.py` | 107 | Imports Telegram history into PostgreSQL graph | 🔴 Broken | Imports non-existent `extract_graph` module |
| `fix_graph.py` | 106 | Deduplicates context_graph.md entries | ✅ OK | One-off utility |
| `refine_graph.py` | 98 | Sends entire graph to Gemini for reformatting | ⚠️ Risky | Sends all personal data to LLM; may corrupt graph |
| `smart_refactor.py` | 182 | Classifies tasks via Gemini into Day/Month/Global | ⚠️ Functional | LLM rephrasing can break graph-task linkage |
| `memory_decay.py` | 132 | Archives old graph items (>60 days) | ✅ OK | Scoring logic is partially Squish-inspired but simplified |
| `cleanup_routine.py` | 60 | Removes completed/noise items from graph | ✅ OK | One-off utility |
| `cleanup_metrics.py` | 32 | Removes metrics except pregnancy/ring data | ✅ OK | One-off utility |
| `remove_decisions.py` | 30 | Deletes all decisions from graph | ✅ OK | One-off utility |
| `restore_principles.py` | 42 | Copies principles from Principles.md back to graph | ✅ OK | One-off utility |
| `generate_system_b.py` | 181 | D3 visualization for a "System B" JSON graph | ⚠️ References non-existent `_archive/system_b/knowledge_graph.json` |
| `analyze_love.py` | 23 | Searches raw.txt for love messages | ✅ One-off script | |

### Key Config/Data Files

| File | Purpose | Issues |
|---|---|---|
| `keys.json` | 5 Google AI API keys in plaintext | 🔴 **CRITICAL**: Served on port 8000 to the internet |
| `docker-compose.yml` | PostgreSQL 16 + pgvector | Container not running |
| `SOUL.md` | Agent personality definition | OK |
| `jarvis/SOUL.md` | JARVIS personality (more detailed) | OK |
| `jarvis/ONTOLOGY.md` | Entity schema (Actor, Promise, Decision, Metric, Plan) | Well-structured |
| `jarvis/USER.md` | User profile | Not read (private) |
| `jarvis/MEMORY.md` | Long-term curated memory | Not read (private) |
| `chat_history.json`, `chat.json`, `chats.json` | Telegram chat data dumps | Potentially stale/orphaned |
| `graph_data.json` | D3 export data | Stale (requires PostgreSQL) |
| `graph.html`, `index.html` | D3 visualizations | Served publicly on :8000 |
| `raw.txt` | Raw chat export | One-off data file |
| `analysis.jsonl` | Analysis output | Orphaned |
| `tunnel.pid`, `server.pid`, `ngrok.log` | Process artifacts | Stale PIDs |
| `archive_legacy.tar.gz` | Old code archive | Can be cleaned up |
| `old_graph.html`, `graph_legacy.html`, `graph_system_b.html`, `old_context_graph.md` | Legacy files | Orphaned, should archive |

### Squish App (TypeScript)

A full **Squish Memory** installation — a Claude Code plugin for persistent agent memory using SQLite/PostgreSQL. ~100+ TypeScript source files, node_modules, build output. **Not directly related to JARVIS Python infrastructure** but coexists in workspace.

### JARVIS Memory Vault (`jarvis/memory/`)

| File | Purpose |
|---|---|
| `context_graph.md` | **Primary knowledge graph** (Markdown-based) |
| `collector_state.json` | Collector last-run state, seen hashes, message IDs |
| `Facts.md` | Curated facts |
| `Principles.md` | Life principles |
| `Tasks/Day.md`, `Month.md`, `Global.md` | Classified task lists |
| `.obsidian/` | Obsidian vault config (synced via git) |

---

## Dead Code Found

1. **`export_d3.py`** — Requires PostgreSQL (not running). Dead.
2. **`import_telegram.py`** — Imports `extract_graph` which doesn't exist. Completely broken.
3. **`jarvis_system.py` → `cmd_search()`** — Imports `embedding_util` which doesn't exist. `cmd_status()`, `cmd_rebuild_md()`, `cmd_decay()` all require PostgreSQL.
4. **`generate_system_b.py`** — References `_archive/system_b/knowledge_graph.json` which doesn't exist.
5. **One-off cleanup scripts** (`cleanup_metrics.py`, `cleanup_routine.py`, `remove_decisions.py`, `restore_principles.py`, `analyze_love.py`) — Served their purpose. Should be archived.
6. **`jarvis_extractor.py`** — Superseded by `collector_cron.py` + `gemini_cli.py`. Not called anywhere.
7. **`gemini_cli.py` → `cmd_audio()`** — Audio transcription via Gemini, but `voice_watcher.py` uses Whisper instead. Potentially useful standalone but unused in pipeline.

---

## Unused Dependencies

### Installed but not imported by any active script:
- `neo4j` — Neo4j driver. Zero references in any .py file.
- `langchain_core`, `langchain_text_splitters` — LangChain. Zero references.
- `langsmith` — Zero references.
- `openai` — Zero references (system uses Gemini).
- `pgvector` — Only usable with PostgreSQL (not running).
- `numpy` — No direct use.
- `telethon` — Telegram client. Not imported (system uses `tg` CLI instead).
- `websockets` — Zero references.
- `xxhash`, `zstandard` — Zero references.
- `requests`, `requests_toolbelt` — Zero references (system uses `subprocess` + `curl`).

### Actually used:
- `google-genai` / `google-generativeai` — Gemini API
- `psycopg2-binary` — PostgreSQL (but DB is down)
- `pydantic`, `pydantic-core` — Likely transitive deps
- `httpx`, `httpcore` — Likely transitive deps of google-genai

**Recommendation:** ~60% of installed packages are unused. venv could be rebuilt with just `google-genai psycopg2-binary`.

---

## Security Issues

### 🔴 CRITICAL

1. **API Keys Exposed on Public HTTP Server**
   - `keys.json` contains 5 Google AI API keys in plaintext
   - `graph-server.service` runs `python3 -m http.server 8000` in workspace root
   - **Anyone can `curl http://SERVER_IP:8000/keys.json`** and steal the keys
   - **FIX:** Move keys to env vars or `/root/.secrets/`, restrict http.server to serve only `graph.html`

2. **OpenClaw API Token Hardcoded**
   - `collector_cron.py` line 16: `API_TOKEN = "6b9b90cc1d18c70e6741594c6c07e15526fb740fb213b3c8"`
   - **FIX:** Move to environment variable

3. **PostgreSQL Credentials Hardcoded**
   - `jarvis_password` appears in: `export_d3.py`, `import_telegram.py`, `jarvis_system.py`, `docker-compose.yml`
   - **FIX:** Use env vars

### 🟡 MEDIUM

4. **HTTP Server Has No Auth/TLS** — All workspace files (memory, chat history, personal data) accessible
5. **Automated Telegram Messages** — `collector_cron.py` sends love messages and morning greetings automatically. If state corrupts, it could spam contacts
6. **`refine_graph.py` Sends All Personal Data to Gemini** — Entire knowledge graph (personal facts, family info) sent to Google's API

### 🟢 LOW

7. **MD5 used for content hashing** — Not security-critical (dedup only), but SHA256 would be better practice
8. **No input validation** on subprocess calls to `tg` CLI

---

## Optimization Recommendations

### Architecture

1. **Kill PostgreSQL dependency** — The system evolved away from it. All active code uses `context_graph.md`. Remove `export_d3.py`, `import_telegram.py`, `jarvis_system.py` DB commands, and `docker-compose.yml`.

2. **Consolidate scripts** — The 20 Python files could be reduced to 4:
   - `collector.py` (collector_cron.py)
   - `gemini.py` (gemini_cli.py)
   - `graph.py` (generate_canvas.py + fix_graph.py + memory_decay.py + sync_tasks.py)
   - `voice.py` (voice_watcher.py)

3. **Add cron scheduling** — `collector_cron.py` has "cron" in the name but isn't scheduled. Add: `*/30 * * * * cd /root/.openclaw/workspace && .venv/bin/python collector_cron.py >> /var/log/jarvis-collector.log 2>&1`

4. **Fix HTTP server** — Replace `python3 -m http.server` with nginx serving only `graph.html` and `graph_data.json`

### Code Quality

5. **Extract config** — Create `config.py` with all paths, credentials (from env), chat names
6. **Add error handling** — `collector_cron.py` has bare `except: pass` in multiple places
7. **Logging** — Replace `print()` with proper `logging` module
8. **Type hints** — None exist in any file
9. **Tests** — Zero tests for Python code

### Performance

10. **Batch Gemini calls** — `collector_cron.py` calls Gemini per-chat. Could batch all new messages into one call.
11. **Graph file grows unbounded** — No max-size check. With `memory_decay.py` not scheduled, it will grow indefinitely.

---

## Complete Bot Capabilities

Based on all code analysis, JARVIS can:

### Active Capabilities (working now)
- 📱 **Monitor Telegram chats** (wife, brother, friend, mother) for new messages
- 🧠 **Extract entities** (promises, decisions, metrics, plans) from conversations using Gemini AI
- 📊 **Build a knowledge graph** in Markdown format with deduplication
- 💕 **Auto-reply "I love you"** to wife when she sends love keywords (1h cooldown)
- 💕 **Proactively send love messages** to wife if >4h silence (9AM-10PM)
- ☀️ **Send morning greetings** to mother (7-9 AM, once per day)
- 🔔 **Deadline reminders** — checks graph for tasks due today, sends notifications
- 📊 **Live dashboard** — edits a pinned Telegram message with today's tasks + pregnancy tracker
- 🎤 **Voice note processing** — watches for audio files, transcribes with Whisper, extracts entities
- 🌐 **D3.js graph visualization** — interactive force-directed graph served on port 8000
- 🔄 **Obsidian sync** — two-way task sync between graph and Obsidian vault
- ☁️ **Git sync** — auto-pushes memory changes to GitHub
- 🤖 **Gemini CLI** — ask questions, translate, extract entities, summarize, transcribe audio
- 🔑 **API key rotation** — automatic rotation across 5 Google AI keys on quota exhaustion

### Dormant Capabilities (code exists but broken/unused)
- 🔍 Semantic search via pgvector embeddings (requires PostgreSQL)
- 📈 Graph export to JSON for D3 (requires PostgreSQL)
- 📦 Temporal decay / auto-archive of old entities
- 🏗️ Full entity extraction to structured md files (jarvis_extractor.py)
- 📋 Smart task classification via LLM (Day/Month/Global)

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     JARVIS Infrastructure                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │  Telegram    │────▶│ collector_   │────▶│ Gemini API   │ │
│  │  (tg CLI)   │     │ cron.py      │     │ (5 keys)     │ │
│  │             │◀────│              │     │              │ │
│  │  Chats:     │     │ Features:    │     └──────────────┘ │
│  │  - Wife     │     │ - Extract    │            │          │
│  │  - Brother  │     │ - Auto-reply │            ▼          │
│  │  - Friend   │     │ - Greetings  │     ┌──────────────┐ │
│  │  - Mother   │     │ - Dashboard  │     │ context_     │ │
│  └─────────────┘     │ - Deadlines  │────▶│ graph.md     │ │
│                      └──────────────┘     │ (Knowledge   │ │
│                             │             │  Graph)       │ │
│                             ▼             └──────┬───────┘ │
│                      ┌──────────────┐            │          │
│                      │ sync_tasks   │◀───────────┘          │
│                      │ .py          │            │          │
│                      └──────┬───────┘            ▼          │
│                             ▼             ┌──────────────┐ │
│                      ┌──────────────┐     │ generate_    │ │
│                      │ Obsidian     │     │ canvas.py    │ │
│                      │ Tasks/*.md   │     └──────┬───────┘ │
│                      └──────────────┘            ▼          │
│                                           ┌──────────────┐ │
│  ┌─────────────┐                          │ graph.html   │ │
│  │ voice_      │──── Whisper ────▶        │ (D3.js)      │ │
│  │ watcher.py  │     transcribe   ───────▶│ :8000        │ │
│  │ (running)   │                          └──────────────┘ │
│  └─────────────┘                                            │
│                                                              │
│  ┌─────────────┐     ┌──────────────┐                      │
│  │ gemini_     │     │ key_manager  │                      │
│  │ cli.py      │────▶│ .py          │                      │
│  │ (CLI tool)  │     │ (5 keys      │                      │
│  └─────────────┘     │  rotation)   │                      │
│                      └──────────────┘                      │
│                                                              │
│  ┌─────────────────────────────────────────┐               │
│  │ DORMANT / BROKEN                        │               │
│  │ - PostgreSQL (docker not running)       │               │
│  │ - export_d3.py, import_telegram.py      │               │
│  │ - jarvis_system.py (DB commands)        │               │
│  │ - jarvis_extractor.py (superseded)      │               │
│  └─────────────────────────────────────────┘               │
│                                                              │
│  ┌─────────────────────────────────────────┐               │
│  │ SQUISH APP (separate TypeScript system) │               │
│  │ Claude Code memory plugin               │               │
│  │ Not integrated with JARVIS Python code  │               │
│  └─────────────────────────────────────────┘               │
│                                                              │
│  SERVICES:                                                   │
│  • graph-server.service (systemd, :8000, ACTIVE)            │
│  • voice_watcher.py (manual, RUNNING pid 2361698)           │
│  • No cron jobs configured                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Priority Action Items

1. **🔴 IMMEDIATE:** Fix `keys.json` exposure — restrict HTTP server or move keys
2. **🔴 IMMEDIATE:** Move all credentials to environment variables
3. **🟡 THIS WEEK:** Delete broken scripts or archive them
4. **🟡 THIS WEEK:** Schedule collector_cron.py via cron
5. **🟡 THIS WEEK:** Clean up unused pip packages
6. **🟢 LATER:** Consolidate scripts, add logging, add tests
7. **🟢 LATER:** Decide: keep PostgreSQL path or fully commit to Markdown-only graph

---

*Report generated 2026-02-18T23:16 MSK*
