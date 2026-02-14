# Plans

<!-- Format:
## plan-{uuid}
- actor: actor_id
- content: what is planned
- target_date: date or null
- status: active | done | abandoned
- source_quote: "exact quote"
- confidence: 0.0-1.0
-->

## plan-postgres
- actor: actor-owner
- content: PostgreSQL in Docker for graph + visualization
- target_date: null
- status: done
- source_quote: "PostgreSQL граф — хранение сущностей"
- confidence: 0.9

## plan-obsidian
- actor: actor-owner
- content: Integrate Obsidian vault for voice → transcription → notes
- target_date: null
- status: active
- source_quote: "Obsidian — Голос → транскрипция → заметка → vault"
- confidence: 0.8

## plan-baby
- actor: actor-arisha
- content: Baby due before September 2026
- target_date: 2026-09-01
- status: active
- source_quote: "ребенок родится до сентября"
- confidence: 0.9

## plan-semantic
- actor: actor-owner
- content: Implement semantic search over dialogs
- target_date: null
- status: done
- source_quote: "Семантический поиск по диалогам"
- confidence: 0.9

## plan-multi-chat
- actor: actor-owner
- content: Process all key Telegram chats (not just Arisha)
- target_date: null
- status: active
- source_quote: "Обработка других чатов"
- confidence: 0.9

## plan-mcp
- actor: actor-owner
- content: Build MCP Server for automatic graph queries before responses
- target_date: null
- status: active
- source_quote: "MCP Server чтобы автоматически запрашивал граф перед ответом"
- confidence: 0.9

## plan-auto-collect
- actor: actor-owner
- content: Cron-based auto-collector — Telegram → Gemini 2.5 Pro extraction every 2h
- target_date: null
- status: active
- source_quote: "Auto-collector cron для Telegram ingestion"
- confidence: 0.9

## plan-voice-svc
- actor: actor-owner
- content: voice_watcher.py as systemd service (auto-restart)
- target_date: null
- status: active
- source_quote: "voice_watcher как systemd service"
- confidence: 0.9

## plan-gemini-extract
- actor: actor-owner
- content: Use Gemini 2.5 Pro (free) for all entity extraction, not Claude
- target_date: null
- status: active
- source_quote: "Gemini free tier для extraction, Claude только для ответов"
- confidence: 0.9

## plan-collage
- actor: actor-owner
- content: Make photo collage and send to everyone
- target_date: null
- status: active
- source_quote: "сделать коллаж из фотографий и отправить"
- confidence: 0.8

## plan-appeal
- actor: actor-owner
- content: Submit appeal
- target_date: null
- status: active
- source_quote: "подать апелляцию"
- confidence: 0.8

## plan-0a2c3846
- actor: actor-owner
- content: Add a JSON configuration file
- target_date: null
- status: active
- source_quote: "Добавь себе файл настройки JSON, возможность выбора модели Cloud Opus 4.6."
- confidence: 0.9

## plan-89a2331a
- actor: actor-owner
- content: Add the ability to choose the Cloud Opus 4.6 model
- target_date: null
- status: active
- source_quote: "Добавь себе файл настройки JSON, возможность выбора модели Cloud Opus 4.6."
- confidence: 0.9

## plan-e8e460f5
- actor: actor-owner
- content: Install a skill for importing dialogues with Telegram
- target_date: null
- status: active
- source_quote: "нужно установить в кил импорт диалогов с телеграмом"
- confidence: 0.9

## plan-ba758fc1
- actor: actor-owner
- content: Build connections with the help of the dialogue import skill
- target_date: null
- status: active
- source_quote: "в помощь этого скила уже строить связи"
- confidence: 0.9

## plan-2a9d0798
- actor: actor-owner
- content: Install a skill that will convert connections into vector ones and build a correct graph
- target_date: null
- status: active
- source_quote: "Может быть еще установить кил, который будет сразу превращать эти связи в векторные и строить правильный граф."
- confidence: 0.9

## plan-dbc4fa1c
- actor: actor-owner
- content: Создать второго полностью отдельного агента, которому Valekk предоставит новый ключ (опеключ от телеграмбота), и который будет называться 'Жара' для ответов на случайные вопросы.
- target_date: null
- status: active
- source_quote: "Создай второго полностью отдельного агента, которым я дам новый ключ, опеключ от телеграмбота. Он будет звать жарой скажу для ответов на случайные вопросы."
- confidence: 0.9
