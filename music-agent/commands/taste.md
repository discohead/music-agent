---
name: taste
description: Analyze your music library — discover patterns, blind spots, dormant favorites, and taste signals. Archaeology of your listening self.
argument-hint: [focus area]
---

<objective>
Perform deep analysis of the user's Apple Music library. If $ARGUMENTS provides a focus area (genres, labels, eras, most-played, forgotten, recent, skipped), narrow the analysis. Otherwise, provide a comprehensive taste profile.
</objective>

<context>
Knowledge graph stats: !`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py stats 2>/dev/null || echo '{"status": "not initialized"}'`
</context>

<!-- TODO: 500-track export produces ~200KB of JSON which consumes significant
     context window space. Consider starting with 100-200 tracks, or implementing
     a compact/summary export mode in library_export.jxa that pre-aggregates data.

     TODO: The `loved` field is null for all tracks due to JXA limitation. The
     "Dormant favorites" analysis (step 3) cannot use loved status — must rely
     on `rating` field instead. Update the analysis description to reflect this. -->

<process>
1. Export the library (or a relevant subset): `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/scripts/apple-music/library_export.jxa 500`
   (Start with 500 tracks for analysis; increase if user wants comprehensive view)
2. Parse $ARGUMENTS for focus area, or default to comprehensive analysis
3. Analyze the export data across dimensions:
   - **Genre distribution**: What genres dominate? What's underrepresented?
   - **Era clusters**: Which decades/years are most represented?
   - **Label concentrations**: Any label loyalty patterns?
   - **Listening intensity**: Most-played tracks, highest play-count artists
   - **Dormant favorites**: High-rated or loved tracks with zero recent plays
   - **Skip patterns**: High skip-count tracks (why are these still in the library?)
   - **Addition patterns**: When were things added? Any binge periods?
   - **Duration preferences**: Does the user favor long-form or short-form?
   - **Comment field**: Any existing agent annotations or tags?
4. Identify taste signals and store them: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py store-entity '<json>'`
5. Present findings as a narrative — this is a portrait of the user's musical identity
6. Offer actionable directions: "You haven't explored X despite loving Y" or "Your 2019 additions suggest a phase you've abandoned"
</process>

<success_criteria>
- Library analyzed across multiple dimensions
- Quantitative data presented (counts, percentages) alongside qualitative insights
- At least one non-obvious pattern identified
- Taste signals stored in knowledge graph for future use
- Actionable recommendations based on blind spots or dormant interests
- Presented as a readable narrative, not a spreadsheet
</success_criteria>
