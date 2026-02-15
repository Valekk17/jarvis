#!/bin/bash
cd /root/.openclaw/workspace

# Use default key (first one) for ingestion or rotate inside?
# ingest.py uses single env var. I should update it to use KeyManager too.
# But for now, let's just pick a random key for ingest or use rotation inside ingest.
# I will assume ingest.py works.
# Or I should pass one of the keys from keys.json?

# Better: update ingest.py to use KeyManager as well.
# But user only asked for "gemini cli to extract entities".
# Ingest is embeddings.
# Let's assume ingest works for now or update it later.
# For extraction, it uses KeyManager.

.venv/bin/python ingest.py
.venv/bin/python extract_graph.py
.venv/bin/python sync_obsidian.py
