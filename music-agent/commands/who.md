---
name: who
description: Explore the credit graph — who made this record? Who else did they work with? Follow the invisible collaborator networks.
argument-hint: <artist|release|track>
---

<objective>
Trace the credit graph for $ARGUMENTS. The music industry runs on invisible collaborator networks — producers, engineers, mastering engineers, label curators — that listeners rarely see. This command surfaces those connections and follows them to discover new music.
</objective>

<!-- TODO: Step 2 hardcodes `artist` as the lookup type, but argument-hint says
     <artist|release|track>. If the user passes a release or track name, this will
     search for an artist with that name. Should disambiguate the subject type first
     (try artist, then release, then recording) or ask the user. -->

<process>
1. Identify the subject from $ARGUMENTS
2. Search MusicBrainz for the subject: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py artist "<n>"`
3. Get their MBID, then look up releases: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py discography "<mbid>"`
4. For key releases, get full credits: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/musicbrainz_lookup.py credits "<release-mbid>"`
5. Build the credit map: producers, engineers, mastering engineers, featured artists, remix artists, label connections
6. For interesting credits, follow the chain — "Who else did this engineer work on?"
7. Cross-reference discoveries with the user's library: `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/search_library.jxa "<n>"`
8. Store all entities and relations in the knowledge graph
9. Present the credit map as a narrative — tell the story of these connections
10. Highlight the most interesting threads for further exploration
</process>

<success_criteria>
- Credit graph explored at least 2 levels deep from the seed
- Key collaborators identified (producer, engineer, mastering, label)
- Cross-referenced with user's library (what they have vs don't have from these connections)
- Relations stored in knowledge graph for future queries
- Presented as a readable narrative, not just a data dump
- At least one surprising or non-obvious connection surfaced
</success_criteria>
