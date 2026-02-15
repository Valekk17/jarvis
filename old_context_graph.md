# Context Graph Entities

## Actors
- **Alexey Kosenko** | Role: friend | Aliases: ['Лёха', 'Леха', 'Leha', 'Косенко', 'Kosenko']
- **Andrey Kovalkov** | Role: family | Aliases: ['Андрей', 'брат', 'Ковальков', 'brother']
- **Arisha** | Role: family | Aliases: ['Ариша', 'жена', 'wife', 'Мой Мир']
- **Evgeniya Kovalkova** | Role: family | Aliases: ['мама', 'Евгения', 'Ковалькова', 'mom']
- **JARVIS** | Role: system | Aliases: ['Джарвис', 'jarvis', 'бот', 'bot', 'assistant']
- **Valekk_17** | Role: owner | Aliases: ['я', 'мне', 'мой', 'valekk', 'valekk_17']

## Promises
- [pending] insurance will be free | From: actor-arisha → actor-owner | Deadline: None | Quote: "страховка будет бесплатной"
- [pending] order deodorants | From: actor-owner → actor-arisha | Deadline: None | Quote: "заказать дезодоранты"
- [pending] send report | From: actor-leha-kosenko → actor-owner | Deadline: None | Quote: "обещал скинуть отчет до пятницы"
- [expired] не прийти на ужин | From: actor-owner → actor-arisha | Deadline: None | Quote: "Не приду на ужин"
- [pending] отправить напоминание Комбату | From: actor-owner → actor-arisha | Deadline: None | Quote: "Комбату отправь напоминание"
- [pending] показывать и рассказывать детям как сильно тебя люблю и как ты меня любишь | From: actor-arisha → actor-owner | Deadline: None | Quote: "Вообще всегда буду показывать и рассказывать детям как сильно тебя люблю и как ты меня любишь"
- [expired] прийти | From: actor-owner → actor-arisha | Deadline: None | Quote: "Приду❤️"
- [pending] решить проблему | From: actor-arisha → actor-owner | Deadline: None | Quote: "Если будет проблема — решим"
- [pending] скажет | From: папа → actor-owner | Deadline: None | Quote: "папа сказал скажет"
- [pending] сказать | From: папа → actor-owner | Deadline: None | Quote: "папа сказал скажет"
- [pending] скачать и скинуть фотки | From: actor-owner → actor-arisha | Deadline: None | Quote: "Скачай и скинь"

## Decisions
- Adopt cybOS architecture for JARVIS | Date: 2026-02-14 | Quote: "cybOS и Граф Контекста"
- All internal JARVIS files in English (saves ~30% tokens) | Date: 2026-02-14 | Quote: "сделай все файлы на английском"
- Context graph in markdown files + PostgreSQL | Date: 2026-02-14 | Quote: "Build context graph using markdown files"
- Switch to Claude Opus 4.6 as primary model | Date: 2026-02-14 | Quote: "модель Claude Opus 4.6"
- Use Gemini Embeddings (gemini-embedding-001) | Date: 2026-02-14 | Quote: "Adopted Google Gemini Embeddings"
- Use PostgreSQL in Docker for graph storage | Date: 2026-02-14 | Quote: "Агент решил что PostgreSQL эффективнее"
- Адекватно общаться | Date: 2026-02-15 | Quote: "Адекватно общаться"
- выйти в 18:30 | Date: 2026-02-14 | Quote: "Тогда нужно в 18.30 выходить"
- Главное любить и разговаривать | Date: 2026-02-15 | Quote: "Главное любить и разговаривать"
- На зло не нужно злом отвечать | Date: 2026-02-15 | Quote: "На зло не нужно злом отвечать"
- написать ассистенту | Date: 2026-02-14 | Quote: "Ну вот я написала ассистенту"
- написать в поддержку | Date: 2026-02-14 | Quote: "Написала в поддержку"

## Metrics
- **income_mentioned**: 3000.0 RUB | Quote: "доход 3000 руб"
- **income_threshold_mrot**: 8.0 МРОТ | Quote: "порог 8 МРОТ"
- **insurance_cashback_pct**: 20.0 % | Quote: "20% кэшбэка на страховку"
- **insurance_monthly_deduction**: 500.0 RUB | Quote: "списание по полису 500 руб"
- **insurance_total_sum**: 150000.0 RUB | Quote: "Страховая сумма 150000₽"
- **Pregnancy**: 12.3 weeks | Quote: "Беременность 12.3"
- **pregnancy_weeks**: 12.3 weeks | Quote: "Arisha pregnancy ~12.3 weeks"
- **возраст сына Valekk'а**: 4.0 года | Quote: "у него жена ребенок 4 года сын"
- **максимальное списание за страховку**: 500.0 ₽ | Quote: "максимум — 500 ₽"
- **минимальное списание за страховку**: 20.0 ₽ | Quote: "Минимум — 20 ₽"
- **порог кэшбэка для списания страховки**: 100.0 ₽ | Quote: "при кэшбэке от 100 ₽"
- **процент списания за страховку от кэшбэка**: 20.0 % | Quote: "За страховку списываем 20% от кэшбэка"
- **списание по полису страхования**: 500.0 руб | Quote: "500руб это списание по полису страхования"
- **страховая сумма**: 150000.0 ₽ | Quote: "Страховая сумма — до 150 000 ₽"

## Plans
- [active] Baby due before September 2026 | Target: 2026-09-01 | Quote: "ребенок родится до сентября"
- [active] Build MCP Server for automatic graph queries before responses | Target: None | Quote: "обернуть граф как MCP Server"
- [active] Cron-based auto-collector: Telegram → Gemini extraction every 2h | Target: None | Quote: "Auto-collector cron для Telegram ingestion"
- [active] fill something out | Target: None | Quote: "Заполню"
- [active] go home | Target: None | Quote: "Завтра домой"
- [active] Implement semantic search over dialogs | Target: None | Quote: "Семантический поиск по диалогам"
- [active] Integrate Obsidian vault for voice → transcription → notes | Target: None | Quote: "Obsidian — Голос → транскрипция → заметка"
- [active] Make photo collage and send to everyone | Target: None | Quote: "сделать коллаж из фотографий"
- [active] Pick up part of marmalade from Ozon | Target: None | Quote: "Часть мармелада пришла на озон"
- [active] PostgreSQL in Docker for graph + visualization | Target: None | Quote: "PostgreSQL граф — хранение сущностей"
- [active] Process all key Telegram chats (not just Arisha) | Target: None | Quote: "Обработка других чатов (пока только Ариша)"
- [active] Submit appeal | Target: None | Quote: "подать апелляцию"
- [active] Use Gemini 2.5 Pro (free) for all entity extraction, not Claude | Target: None | Quote: "Gemini free tier для extraction, Claude только для ответов"
- [active] voice_watcher.py as systemd service (auto-restart) | Target: None | Quote: "voice_watcher как systemd service"
- [active] Write to insurance support | Target: None | Quote: "написать в поддержку"
- [active] бабушке гале позвонить | Target: None | Quote: "Надо бабушке гале позвонить"
- [active] Забрать мармелад с Ozon | Target: 2026-02-15 | Quote: "Часть мармелада пришла на озон"
- [active] заказать дезодоранты с озона | Target: None | Quote: "надо заказать дезодоранты с озона"
- [active] избавиться от мата | Target: None | Quote: "надо кстати избавляться по-хорошему"
- [active] не сидеть в тиктоке | Target: None | Quote: "Главное знаешь, вот самим тоже не сидеть в тиктоке 😃"
- [active] повести в столовку | Target: None | Quote: "Я же в столовку поведу"
- [active] позвонить бабушке гале | Target: None | Quote: "Надо бабушке гале позвонить"
- [active] позвонить бабушке Гале | Target: None | Quote: "Надо бабушке гале позвонить"
- [active] Позвонить бабушке Гале | Target: None | Quote: "Надо бабушке гале позвонить"
- [active] пойти вечером за тестом в монеточку | Target: None | Quote: "Так, вечером за тестом в монеточку"
- [active] покидать всем коллаж фотокарточки | Target: None | Quote: "Надо им всем коллаж фотокарточки покидать наверное"
- [active] приехать к сыну | Target: None | Quote: "сына скоро приеду"
- [active] сделать дела | Target: None | Quote: "Надо сделать дела то"
- [active] составить табличку | Target: None | Quote: "Надо вообще составить наверное табличку"
- [active] стараться (в воспитании ребенка) | Target: None | Quote: "Но блин, реально нам нужно будет стараться"
- [active] читать всякие умные книжки (ребенку) | Target: None | Quote: "Будете всякие умные книжки читать"