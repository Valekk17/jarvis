# Key Decisions

<!-- Format:
## decision-{uuid}
- actors: [actor_ids]
- content: what was decided
- context: why
- date: YYYY-MM-DD
- source_quote: "exact quote"
- confidence: 0.0-1.0
-->

## decision-001
- actors: [actor-owner]
- content: Build context graph using markdown files, not Neo4j. PostgreSQL later if needed.
- context: Agent determined markdown + SQLite more efficient for current scale
- date: 2025-07-11
- source_quote: "Автор не использовал Neo4j — агент сам решил, что эффективнее реализовать граф внутри PostgreSQL"
- confidence: 0.9

## decision-002
- actors: [actor-owner]
- content: All internal JARVIS files in English to save ~30% tokens
- context: Token economy optimization
- date: 2025-07-11
- source_quote: "сделай все файлы на английском языке, нам же нужно экономить токены"
- confidence: 1.0

## decision-39d68336
- actors: [actor-owner]
- content: использовать PostgreSQL для графа
- date: 2026-02-13
- source_quote: "Решили использовать PostgreSQL для графа."
- confidence: 0.9

## decision-336457be
- actors: [actor-owner]
- content: написать ассистенту
- date: 2026-02-14
- source_quote: "Ну вот я написала ассистенту"
- confidence: 0.9

## decision-a263fa95
- actors: [actor-owner]
- content: написать в поддержку
- date: 2026-02-14
- source_quote: "Написала в поддержку"
- confidence: 0.9

## decision-5cad1413
- actors: [actor-owner]
- content: выйти в 18:30
- date: 2026-02-14
- source_quote: "Тогда нужно в 18.30 выходить"
- confidence: 0.9
