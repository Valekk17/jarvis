# Long-Term Memory

## System
- Initialized: 2025-07-11 | Model: Claude Opus 4.6 | Graph: ONTOLOGY.md v1
- Google Cloud Code Assist (hokuxoqexu51@gmail.com): BANNED 2026-02-19 (403 ToS). Using direct Anthropic key.
- 5 Gemini API keys in /root/.secrets/gemini_keys.json (separate from Cloud Code Assist)

## Key Facts
- Valek: military serviceman, Serpukhov
- Arisha (wife): pregnant, ~14w3d as of 2026-02-18, due ~Aug 16, 2026
- Family: Mother Evgeniya, Brother Andrey | Friend: Alexey Kosenko (Moscow)
- Ring size: 16.5

## Key Decisions
- Markdown-based context graph (PostgreSQL abandoned)
- All internal files in English (~30% token savings)
- Russian + English terminology in responses
- No duplicate messages (message tool OR final, never both)

## Lessons
- localtunnel URLs expire — always verify
- voice_watcher.py needs nohup/systemd monitoring
- Include sender attribution when feeding chat to LLM
- Bot API cannot send Telegram scheduled messages — use Cron
- keys.json was publicly exposed via http.server — fixed 2026-02-18 (moved to /root/.secrets/)
- System audit 2026-02-18: health 4/10 → 8/10. Archived 22 dead files, secured credentials.
