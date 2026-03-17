---
name: kb
description: Inspect and query the music knowledge graph directly — see accumulated entities, relations, annotations, and session history.
argument-hint: [stats|search <term>|query <sql>|sessions|annotations|threads]
---

<objective>
Provide direct access to the music-agent knowledge graph. If $ARGUMENTS is empty, show stats. Otherwise dispatch to the appropriate operation: stats, search, raw SQL query, session history, annotation review, or research threads.
</objective>

<process>
1. Parse $ARGUMENTS for the operation
2. Dispatch:
   - Empty or "stats": `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py stats`
   - "search <term>": `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py search "<term>"`
   - "query <sql>": `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py query "<sql>"`
   - "sessions": `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py query "SELECT s.*, COUNT(st.id) as track_count FROM sessions s LEFT JOIN session_tracks st ON s.id = st.session_id GROUP BY s.id ORDER BY s.started_at DESC LIMIT 10"`
   - "annotations": `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py query "SELECT a.*, e.name as entity_name FROM annotations a JOIN entities e ON a.entity_id = e.id ORDER BY a.created_at DESC LIMIT 20"`
   - "threads": `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py threads`
3. Present results in a readable format
</process>

<success_criteria>
- Requested data retrieved and presented clearly
- Stats show the health and growth of the knowledge graph
- Search results include related entities and annotations
</success_criteria>
