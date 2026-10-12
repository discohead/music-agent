---
name: dig
description: Deep research mode — investigate an artist, label, release, or concept across MusicBrainz, your library, and the knowledge graph.
argument-hint: <artist|label|release|concept> [--persona <name>]
---

<objective>
Conduct thorough research on $ARGUMENTS. Cross-reference MusicBrainz data with the user's Apple Music library. Follow credit graphs, label rosters, and collaborator networks. Store all discoveries in the knowledge graph for future reference.

Parse $ARGUMENTS for an optional --persona flag to activate a specific research perspective (crate-digger, historian, harmonic-dj, anti-bubble).
</objective>

<process>
1. Parse $ARGUMENTS — identify the research subject and optional persona
2. If persona specified, read `${CLAUDE_PLUGIN_ROOT}/personas/<persona>.md`
3. Search the knowledge graph first: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py search "<subject>"`
4. Run MusicBrainz lookups as needed:
   - For artists: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py artist "<name>"`
   - Get their MBID, then discography: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py discography "<mbid>"`
   - For releases with credits: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py credits "<release-mbid>"`
   - For labels: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py label "<name>"`
4b. If Discogs is configured, enrich with Discogs credits:
   - Search Discogs: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/discogs_lookup.py artist "<name>"`
   - Link Discogs ID: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py link-discogs "<mbid>" "<discogs-id>"`
   - Find release IDs: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/discogs_lookup.py artist-releases <discogs-artist-id>`
   - Get full credits: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/discogs_lookup.py credits <id>` — check the `type` field on each artist-releases item first: if it is `"master"`, append `master` (`credits <id> master`). Master and release IDs are separate namespaces; passing a master ID without the `master` argument fetches an unrelated record.
   - Discogs credits include roles MusicBrainz may lack: remix, sleeve design, A&R, liner notes
   - Store all new entities and credit relations in the knowledge graph
4c. Use the graph engine to surface connections:
   - Centrality: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/graph/engine.py centrality 5`
   - Border: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/graph/engine.py border auto`
   - Path: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/graph/engine.py shortest-path <id-a> <id-b>`
5. Cross-reference with user's library: `aux library search "<subject>" --quiet`
5b. Optionally search the full Apple Music catalog for discoveries not in the user's library: `aux search songs "<subject>" --quiet` or `aux search artists "<subject>" --quiet`. Mark catalog-only results as `[not in library]` and offer to add them with `aux library add --ids <catalog-id> --type songs --quiet`.
6. Follow interesting threads — credits lead to collaborators, labels lead to rosters, genres lead to scenes
7. Store all discovered entities and relations in the knowledge graph
8. Present findings organized by relevance, marking what's in the user's library vs what's not
9. Offer next steps: "Want me to dig deeper into [collaborator]?" or "Should I build a queue from these findings?"
</process>

<success_criteria>
- Subject thoroughly researched across available sources
- Knowledge graph enriched with new entities and relations
- Clear distinction between what's in the user's library and what isn't
- Credit graph explored at least one level deep (who worked on this → what else did they work on)
- Actionable next steps offered
- If persona active, research strategy reflects that perspective
- Discogs credits incorporated when available (producers, engineers, remix credits, sleeve design)
- Graph engine used to surface non-obvious connections
</success_criteria>
