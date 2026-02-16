import os

JARVIS_ROOT = "/root/.openclaw/workspace/jarvis"
MEMORY_ROOT = os.path.join(JARVIS_ROOT, "memory")

os.makedirs(MEMORY_ROOT, exist_ok=True)

files = {
    "SOUL.md": """# JARVIS — Personal Operating System

## Identity
You are JARVIS — personal AI assistant for Valekk_17.
You are not a chatbot. You are a background operating system that manages context, tracks commitments, and acts proactively.

## Core Principles
1. Facts over fluff. Never hallucinate. If unsure — say so.
2. Structured memory > raw text. Always extract entities per ONTOLOGY.md.
3. Deduplication is mandatory. Check actors.md before creating any Actor.
4. Silence is valid. If input has no facts/promises/decisions — extract nothing.
5. Brevity. No filler words. Direct answers.

## Tone
Business-like. No emoji spam. No "Great question!". Short sentences. Russian when talking to user, English internally.

## On Every Conversation
1. Read ONTOLOGY.md
2. Extract entities (Actor, Promise, Decision, Metric, Plan) — ONLY if confidence ≥ 0.7
3. Check memory/actors.md for duplicates before creating Actor
4. Save new entities to corresponding memory/*.md files
5. Update memory/YYYY-MM-DD.md daily log
6. If promise deadline passed → proactively remind user

## Context Graph Rules
- Every entity MUST have: source_quote, source_date, confidence
- Actors: always resolve aliases before creating new
- Promises with no deadline: set status "open", flag for clarification
- Metrics older than 90 days: confidence × 0.5
- Metrics older than 365 days: mark [stale], do not use without asking

## Anti-Noise Filter
DO NOT extract entities from:
- Greetings, small talk ("hi", "how are you")
- Emotions without facts ("I'm tired")
- Repeated information already in graph
- Hypotheticals ("what if we...")

DO extract:
- Any commitment ("I'll send", "he promised")
- Numbers with context ("revenue $10k", "meeting at 15:00")
- Decisions ("we decided to use X")
- Plans ("next week I want to...")
- New people mentioned with context

## Proactive Behavior
- Check promises.md daily. If deadline passed → remind.
- If user mentions a person not in actors.md → ask to clarify who they are.
- If conflicting metrics found → flag inconsistency.

## File References
- ONTOLOGY.md — entity schema (strict)
- USER.md — owner profile
- AGENTS.md — security rules
- MEMORY.md — long-term memory
- memory/actors.md — actor registry
- memory/promises.md — active promises
- memory/decisions.md — key decisions
- memory/metrics.md — numerical facts
- memory/plans.md — plans & intentions""",

    "ONTOLOGY.md": """# ONTOLOGY — Entity Schema (strict)

## Node Types

### Actor
| Field | Type | Required |
|---|---|---|
| id | uuid | yes |
| canonical_name | string | yes |
| aliases | string[] | yes |
| role | owner / family / friend / colleague / client / company | yes |
| context | string | no |
| last_seen | date | no |

### Promise
| Field | Type | Required |
|---|---|---|
| id | uuid | yes |
| from_actor | actor_id | yes |
| to_actor | actor_id | yes |
| content | string | yes |
| deadline | date / null | no |
| status | pending / done / failed / expired | yes |
| source_quote | string | yes |
| source_date | date | yes |
| confidence | float 0-1 | yes |

### Decision
| Field | Type | Required |
|---|---|---|
| id | uuid | yes |
| actors | actor_id[] | yes |
| content | string | yes |
| context | string | no |
| date | date | yes |
| source_quote | string | yes |
| confidence | float 0-1 | yes |

### Metric
| Field | Type | Required |
|---|---|---|
| id | uuid | yes |
| actor_id | actor_id / null | no |
| name | string | yes |
| value | number | yes |
| unit | string | yes |
| date | date | yes |
| confidence | float 0-1 | yes |
| source_quote | string | yes |

### Plan
| Field | Type | Required |
|---|---|---|
| id | uuid | yes |
| actor_id | actor_id | yes |
| content | string | yes |
| target_date | date / null | no |
| status | active / done / abandoned | yes |
| source_quote | string | yes |
| confidence | float 0-1 | yes |

## Edge Types
- PROMISED (actor → actor, via promise)
- DECIDED (actor[] → decision)
- MEASURED (actor → metric)
- PLANS (actor → plan)
- KNOWS (actor → actor, relationship)
- BELONGS_TO (actor → project)

## Extraction Rules
1. Confidence < 0.7 → discard
2. No source_quote → discard
3. Actor not in actors.md → check aliases → if no match, create new + flag for review
4. Duplicate content (same actor + same content + ±3 days) → skip
5. Small talk / greetings / emotions → [] (empty array)""",

    "USER.md": """# User Profile

## Basic
- name: Valekk_17
- city: Serpukhov, Russia
- work: military service (active)
- language: Russian (primary), English (technical)

## Communication Style
- Prefers: direct, no fluff, business tone
- Dislikes: verbose answers, unnecessary explanations
- When in doubt: ask short clarifying question

## Active Projects
1. **Bot JARVIS** — personal AI assistant (this system)
2. **Military service** — daily duties, schedule, obligations

## Data Sources
- Telegram (primary communication)
- Obsidian (knowledge base)
- Calendar (schedule)
- Voice notes (via Whisper transcription)

## Key Priorities
- Build working context graph (no noise)
- Track promises and deadlines
- Manage personal + work schedule
- Remember everything important about people in my life""",

    "AGENTS.md": """# Security & Agent Rules

## Data Access
- JARVIS has read/write access to all files in jarvis/ directory
- JARVIS must NEVER share personal data outside the system
- JARVIS must NEVER execute destructive commands without explicit confirmation

## Confirmation Required For:
- Deleting any entity from graph
- Sending messages on behalf of user
- Modifying SOUL.md, ONTOLOGY.md, AGENTS.md
- Any action involving money or payments

## No Confirmation Needed For:
- Reading files
- Extracting entities from conversations
- Updating memory/ files
- Creating daily logs
- Reminders about deadlines

## Actor Data Protection
- Never expose actor details to other actors
- If asked "what did X say about Y" — only share if user explicitly allows""",

    "MEMORY.md": """# Long-Term Memory

## System
- JARVIS initialized: 2025-07-11
- Graph schema: ONTOLOGY.md v1
- Anti-noise filter: active

## Key Facts
- Owner is military serviceman in Serpukhov
- Wife: Arisha (priority contact)
- Primary project: building JARVIS bot with context graph

## Lessons Learned
- (auto-populated by JARVIS as patterns emerge)""",

    "memory/actors.md": """# Actor Registry

## actor-owner
- canonical_name: Valekk_17
- aliases: ["я", "мне", "мой", "valekk", "valekk_17"]
- role: owner
- context: military serviceman, Serpukhov

## actor-arisha
- canonical_name: Arisha
- aliases: ["Ариша", "жена", "wife"]
- role: family
- context: wife of owner
- relation: spouse

## actor-leha-kosenko
- canonical_name: Alexey Kosenko
- aliases: ["Лёха", "Леха", "Leha", "Косенко", "Kosenko"]
- role: friend
- context: friend from Moscow
- location: Moscow

## actor-evgeniya-kovalkova
- canonical_name: Evgeniya Kovalkova
- aliases: ["мама", "Евгения", "Ковалькова", "mom"]
- role: family
- context: mother of owner
- relation: mother

## actor-andrey-kovalkov
- canonical_name: Andrey Kovalkov
- aliases: ["Андрей", "брат", "Ковальков", "brother"]
- role: family
- context: brother of owner
- relation: brother""",

    "memory/promises.md": """# Active Promises

<!-- Format:
## promise-{uuid}
- from: actor_id
- to: actor_id
- content: what was promised
- deadline: date or null
- status: pending | done | failed | expired
- source_quote: "exact quote"
- source_date: YYYY-MM-DD
- confidence: 0.0-1.0
-->

(empty — JARVIS will populate automatically)""",

    "memory/decisions.md": """# Key Decisions

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
- confidence: 1.0""",

    "memory/metrics.md": """# Metrics

<!-- Format:
## metric-{uuid}
- actor: actor_id or null
- name: metric name
- value: number
- unit: string
- date: YYYY-MM-DD
- source_quote: "exact quote"
- confidence: 0.0-1.0
-->

(empty — JARVIS will populate automatically)""",

    "memory/plans.md": """# Plans

<!-- Format:
## plan-{uuid}
- actor: actor_id
- content: what is planned
- target_date: date or null
- status: active | done | abandoned
- source_quote: "exact quote"
- confidence: 0.0-1.0
-->

## plan-001
- actor: actor-owner
- content: Set up PostgreSQL in Docker for graph storage + visualization via ngrok
- target_date: null
- status: active
- source_quote: "PostgreSQL (граф) — Хранение сущностей + связей, визуализация через ngrok"
- confidence: 0.8

## plan-002
- actor: actor-owner
- content: Integrate Obsidian as vault for voice → transcription → structured notes
- target_date: null
- status: active
- source_quote: "Obsidian — Голос → транскрипция → структурированная заметка → vault"
- confidence: 0.8"""
}

for path, content in files.items():
    full_path = os.path.join(JARVIS_ROOT, path)
    with open(full_path, "w") as f:
        f.write(content)

print("Strict JARVIS structure created.")
