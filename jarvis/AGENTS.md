# Security & Agent Rules

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
- If asked "what did X say about Y" — only share if user explicitly allows