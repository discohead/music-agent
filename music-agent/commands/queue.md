---
name: queue
description: Build an intelligent queue or playlist from a seed — an artist, track, label, concept, mood, or any idea.
argument-hint: <seed idea> [--count <n>] [--persona <name>] [--save <playlist-name>]
---

<objective>
Build a thoughtful, curated queue of tracks from the user's Apple Music library based on $ARGUMENTS. The seed can be anything — an artist name, a track, a label, a mood, a concept ("build tension then release"), an era, or a completely abstract idea. Parse optional flags: --count (default 20), --persona, --save (create a named playlist).
</objective>

<process>
1. Parse $ARGUMENTS for the seed idea and optional flags (--count, --persona, --save)
2. If persona specified, read `${CLAUDE_PLUGIN_ROOT}/personas/<persona>.md` for search strategy guidance
3. Interpret the seed — determine what kind of search strategy it implies:
   - Artist/label name → search library, expand via knowledge graph relations
   - Track name → find it, analyze its properties, find similar
   - Mood/concept → translate to searchable attributes (genre, era, energy)
   - Abstract idea → get creative, use knowledge graph associations
4. Search the user's library: `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/search_library.jxa "<terms>"`
5. Consult the knowledge graph for related entities: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py search "<term>"`
6. If needed, run MusicBrainz lookups to expand the search space
7. Select and order tracks with intentionality — consider:
   - Energy arc (don't just shuffle — compose a journey)
   - Variety within coherence (same universe, different rooms)
   - The user's relationship with each track (mix familiar and rediscovered)
8. If --save flag provided, create playlist: `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/playlists.jxa create "<name>" "<description>"`
   Then add each track: `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/playlists.jxa add "<name>" <databaseID>`
9. Present the queue with brief reasoning for each pick and the overall arc
10. Log the session: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py log-session '<json>'`
</process>

<success_criteria>
- Queue reflects the seed idea with clear intentionality
- Tracks are ordered, not just collected — there's a compositional logic
- Mix of well-played favorites and rediscovered deep cuts from the library
- Each pick has a brief rationale (not just "similar vibes")
- If --save used, playlist created in Apple Music
- Session logged to knowledge graph
- If persona active, curation strategy reflects that perspective
</success_criteria>
