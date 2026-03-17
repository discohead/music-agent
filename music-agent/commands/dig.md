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
5. Cross-reference with user's library: `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/search_library.jxa "<subject>"`
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
</success_criteria>
