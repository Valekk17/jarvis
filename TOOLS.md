# TOOLS.md — Local Config

## Telegram Chats
- Wife: "Мой Мир❤️" (Arisha, @lazarikk, id:838471791)
- Mother: "Мамуля" (@genekk76, id:763720154)
- Brother: "Андрейка Братик"
- Friend: "Леха Косенко" (@saptded, id:480296644)
- Bot: @jaarvvis_bot (id:8514352345)

## Services
- graph-server: systemd, port 8000, serves /public/ only
- voice_watcher.py: manual (nohup), watches /root/.openclaw/media/inbound/
- Whisper: /opt/whisper-env/, model base (CPU, no FP16)

## Secrets
- Gemini keys: /root/.secrets/gemini_keys.json (5 keys, rotation via key_manager.py)
- Env vars: /root/.secrets/jarvis_env
