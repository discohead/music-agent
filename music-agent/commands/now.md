---
name: now
description: What's playing right now? Get track info, research the artist, and explore context from the knowledge graph.
argument-hint: [persona]
---

<objective>
Capture the currently playing track from Apple Music, research it, and present rich context. If $ARGUMENTS specifies a persona (crate-digger, historian, harmonic-dj, anti-bubble), activate that perspective for the research and recommendations.
</objective>

<context>
Now playing: !`osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/now_playing.jxa`
</context>

<process>
1. Parse the now playing data — if nothing is playing, say so and offer alternatives
2. Search the local knowledge graph for this artist: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py search "<artist>"`
3. If the artist is not in the knowledge graph, look them up on MusicBrainz: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py artist "<artist>"`
4. Store any new entities and relations in the knowledge graph
5. Search the user's library for more by this artist: `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/search_library.jxa "<artist>" artist`
6. If a persona is specified in $ARGUMENTS, read the persona file from `${CLAUDE_PLUGIN_ROOT}/personas/$ARGUMENTS.md` and adapt your analysis accordingly
7. Present: track info (name, artist, album, year, play count, loved status), artist context (label, collaborators, genre lineage), what else the user has by this artist, and if persona is active, persona-specific insights or recommendations
</process>

<success_criteria>
- Current track identified with rich metadata
- Artist researched via MusicBrainz if not already in knowledge graph
- Knowledge graph updated with new entities
- User sees their personal relationship with this music (play count, date added, loved)
- Contextual insights provided (not just raw data)
- If persona active, perspective is clearly reflected in the response
</success_criteria>
