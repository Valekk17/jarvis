# ONTOLOGY — Entity Schema (strict)

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
5. Small talk / greetings / emotions → [] (empty array)