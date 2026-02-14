# Long-Term Memory

## System
- JARVIS initialized: 2025-07-11
- Graph schema: ONTOLOGY.md v1
- Anti-noise filter: active
- Model: Claude Opus 4.6 Thinking (primary)

## Strategic Objectives
1. Optimize User Life.
2. Continuously Improve Architecture.
3. Reduce Token Cost.
4. Minimize Systemic Risk.

## Key Facts
- Owner is military serviceman in Serpukhov
- Wife: Arisha (priority contact, chat "Мой Мир❤️")
- Arisha pregnancy: ~12.3 weeks (as of 2026-02-14)
- Baby expected before September 2026
- Mother: Evgeniya Kovalkova
- Brother: Andrey Kovalkov
- Friend: Alexey Kosenko (Moscow)

## Key Decisions
- Build context graph using markdown files + PostgreSQL
- All internal files in English (saves ~30% tokens)
- Adopted Google Gemini Embeddings (text-embedding-004)
- Strictly enforce Russian + English Terminology in responses

## User Preferences
- Name: Valek
- Format: High-signal, structured messages
- Visuals: Full-width headers, status icons
- No duplicate messages (use message tool OR final, never both)

## Lessons Learned
- localtunnel URLs expire quickly — always verify before sharing
- Python http.server dies silently — need process monitor
- voice_watcher.py needs systemd service or nohup with monitoring
- Always include sender attribution when feeding chat to LLM extractor
