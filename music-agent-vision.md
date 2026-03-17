# music-agent

**An Agentic Music Companion for Apple Music + Claude Code**

*Project Vision Document — March 15, 2026*

---

## Origin

This project began with a simple question: does Apple provide a Swift framework for Apple Music APIs? (Yes — MusicKit, introduced at WWDC 2021.) And does Spotify? (Sort of — an Objective-C iOS SDK that acts as a remote control for the Spotify app, with a REST API for everything else.)

But the real question underneath was bigger: **what if a terminal-based coding agent like Claude Code could become an agentic DJ, curator, collector, archivist, and researcher?** What if there were a Claude Code Apple Music Extension — analogous to VS Code extensions — that turned the terminal into a music research lab, crate-digging station, and intelligent playlist composer?

The idea crystallized through a series of escalating realizations:

1. The APIs exist. MusicKit gives you catalog search, library access, playlist CRUD, and playback control. MusicBrainz gives you deep credits, discographies, and label data. Discogs, Bandcamp, and others fill in the gaps.
2. On macOS, Apple Music is one of the most scriptable apps on the platform. JXA (JavaScript for Automation) can access *everything* — play counts, skip counts, date added, star ratings, loved/disliked state, the comment field, full playback control — data that no API exposes.
3. A Claude Code plugin is just text files, prompts, and scripts. No server, no build step, no API keys for local library access. The agent *is* the interface.
4. The comment field on every Apple Music track is an unused metadata layer that the agent can write to. Agent knowledge embeds directly into the library itself.
5. A local SQLite knowledge graph accumulates everything the agent discovers. The system gets smarter with every interaction without any explicit training.

What emerged is not a music player and not a recommendation engine. It's something that doesn't exist yet: **a music collection as a knowledge graph you can converse with.**

---

## Thesis

Spotify and Apple Music recommendation engines optimize for *platform engagement* — time-on-service, skip rates, passive listening hours. They are not optimizing for the listener's relationship with music. An agentic system optimizes for whatever the listener tells it to optimize for. That's a fundamentally different thing.

You could say "I want to understand the through-line from musique concrète to modern microsound" and get a *curriculum*, not a playlist. You could say "who mastered this record, and what else did they master?" and get a credit graph traversal that surfaces connections no algorithmic feed would ever show you. You could say "look at my library additions from 2019 — what was I into then that I've drifted away from?" and get taste archaeology that treats your own listening history as a queryable dataset for self-understanding.

The paradigm shift is not "AI picks songs for you." It's that your library stops being a flat list of favorites and becomes a structured, queryable, annotated body of knowledge that grows smarter over time. The agent doesn't just find music — it remembers why it recommended something, tracks whether you liked it, refines its model of your taste, and can explain its reasoning.

---

## Core Concepts

### Music Collection as Knowledge Graph

Every entity the agent encounters — artist, album, track, label, engineer, genre — becomes a node in a local knowledge graph. Every relationship — "released on," "mastered by," "member of," "influenced by," "similar to" — becomes an edge. Every interaction enriches the graph. Ask about Mark Fell once, and now the graph contains his discography, his collaborators, his label affiliations, linked to the tracks in your library. Next time you or the agent touches anything adjacent, that context is already local, instant, and searchable.

Listening sessions become data too. "On March 15 you listened to a 2-hour session that started with X and ended with Y, and you skipped these three tracks in the middle." That session arc is itself an object in the graph, queryable later.

Agent annotations are first-class objects, attributed to personas, searchable, revisable. The crate-digger persona flags a release as "deep cut, overlooked, relevant to your interest in microsound." The historian persona adds a note that this track sits at the intersection of two movements. These annotations persist and inform future interactions.

### Personas as Search Strategies

Personas are not tone wrappers. Different curatorial perspectives produce structurally different outputs because they implement different search strategies and scoring functions.

A **crate digger** doesn't just *talk* differently — it *searches* differently. It prioritizes deep cuts, B-sides, overlooked releases on small labels, and credit graph connections that mainstream recommendation would never surface. It scores tracks inversely to popularity.

A **music historian** builds chronological narratives and traces influence chains. It thinks in timelines, movements, and geographic scenes. It scores tracks by historical significance and connective tissue.

A **harmonic DJ** thinks in energy arcs, transitions, BPM flow, and mood trajectories. It treats a playlist as a composed object with deliberate structure — not a collection of good songs, but a journey where each track earns its position through its relationship to what comes before and after.

An **anti-bubble** agent actively fights the filter bubble. It identifies the boundaries of the listener's taste and crosses them deliberately, using a "bridge and leap" pattern that starts from familiar ground and gradually ventures into territory the listener would never encounter through passive algorithmic recommendation.

These are substantively different from Claude.ai Styles. They're closer to specialized subagents with domain-specific heuristics.

### Credit Graph Traversal

This is the killer feature nobody has built well. The music industry runs on invisible collaborator networks — producers, engineers, mastering engineers, label curators — that listeners almost never see. An agent that can traverse these networks surfaces connections that no recommendation algorithm would make.

"Show me everything the engineer who mixed this track has worked on" → cross-reference against the Apple Music catalog → filter to things you haven't heard → rank by relevance to your taste. For experimental electronic music — Fell, Ikeda, Alva Noto — the producer/engineer/mastering credit graph is incredibly dense and interconnected. Rashad Becker mastered half of modern experimental electronic music. An agent that knows that is powerful.

### The Comment Field as Annotation Layer

Every track in Apple Music has a `comment` field that almost nobody uses. The agent can write structured annotations directly into it — tags like `#deep-cut`, `#microsound`, `#crate-dig-find`, or richer JSON metadata. This means agent knowledge gets embedded *into the library itself*, survives across sessions without any external database, syncs across devices via iCloud, and is searchable via JXA. It's a free, persistent metadata layer.

### Taste Archaeology

Your own listening history as a reflective tool. "What was I into in 2019 that I've drifted away from?" "What genres do I have zero representation in despite loving adjacent genres?" "Which tracks have I played 200+ times, and what do they have in common?" Streaming services have this data but don't expose it as a tool for self-understanding.

---

## Non-Obvious Features

Beyond the obvious research, curation, and playlist building:

**Energy arc composition.** Not "similar vibes" but constructing a deliberate emotional trajectory across a queue. "Build me 90 minutes that starts ambient, builds tension for 30 minutes, peaks, then dissolves." The playlist itself becomes a composed object with structure.

**Anti-recommendation.** "What's highly rated in genres I like that I would *never* encounter through my current listening patterns?" Collaborative filtering converges; an agent can be instructed to diverge.

**Release monitoring with taste-aware filtering.** Not "new releases in electronic" (thousands per week) but "new releases that share at least two attributes with things I've favorited in the last 6 months, weighted toward small labels I've shown affinity for." A personal A&R agent.

**Taste archaeology.** Querying your own history for self-understanding. Identifying dormant interests, binge periods, abandoned explorations.

**Session memory.** "What was that playlist I was vibing with last month that started really ambient?" becomes a real query because sessions are logged objects in the knowledge graph.

---

## Architecture

### Design Decision: Plugin-First, Not MCP-First

The v0 deliberately omits the complexity of MCP servers in favor of the simplest possible architecture: a Claude Code plugin composed entirely of text files, prompts, and scripts. This gets shockingly far because:

- JXA gives deeper access to Apple Music than MusicKit in many ways (play counts, skip counts, date added, star ratings, comments, full playback control, no auth tokens, no network calls)
- Python scripts wrap MusicBrainz cleanly with zero infrastructure
- SQLite needs no server and Claude Code can query it directly via bash
- The plugin system provides commands, skills, subagents, hooks, and personas with no custom UI to build
- Claude Code *is* the CLI — the agent interface is already built

MCP servers are the natural v1 evolution when the tools need to be consumed by clients other than Claude Code, or when real-time streaming updates become important.

### Stack

```
┌─────────────────────────────────────────────────┐
│              Claude Code Plugin                  │
├──────────────────┬──────────────────────────────┤
│   Commands       │   Personas                   │
│   /now           │   crate-digger               │
│   /dig           │   historian                  │
│   /queue         │   harmonic-dj                │
│   /who           │   anti-bubble                │
│   /taste         │                              │
│   /kb            │   Subagents                  │
│                  │   crate-digger agent          │
│   Skills         │   historian agent             │
│   music-agent    │                              │
│                  │   Hooks                      │
│                  │   session-start context       │
├──────────────────┴──────────────────────────────┤
│              Scripts Layer                        │
│  ┌────────────┬──────────────┬────────────────┐ │
│  │ JXA/osascript │  Python     │    SQLite     │ │
│  │ now_playing   │  musicbrainz│    db.py      │ │
│  │ search_library│  _lookup    │    schema.sql │ │
│  │ playback      │             │               │ │
│  │ playlists     │             │               │ │
│  │ library_export│             │               │ │
│  │ annotate      │             │               │ │
│  │ play_track    │             │               │ │
│  └────────────┴──────────────┴────────────────┘ │
├─────────────────────────────────────────────────┤
│              Data Layer                          │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  Apple Music App  │  │  ~/.music-agent/     │ │
│  │  (local library)  │  │  knowledge.db        │ │
│  │  via JXA/osascript│  │  (SQLite)            │ │
│  └──────────────────┘  └──────────────────────┘ │
│  ┌──────────────────────────────────────────────┐│
│  │  MusicBrainz API (external, rate-limited)    ││
│  └──────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

### Knowledge Graph Schema

The SQLite database at `~/.music-agent/knowledge.db` contains:

- **entities** — Artists, labels, releases, tracks, engineers. Each has a type, structured metadata, source attribution, and optional Apple Music library ID for cross-referencing.
- **relations** — Graph edges: released_on, mastered_by, member_of, similar_to, influenced_by, collaborated_with. Each has confidence scoring and persona attribution.
- **annotations** — Agent notes attributed to specific personas. Tags, recommendations, contextual observations. First-class objects, searchable and revisable.
- **sessions** — Chronological listening logs with individual track plays, skip tracking, and context about what the user was doing or asked for.
- **session_tracks** — Individual plays within sessions with skip tracking and position data.
- **lookup_cache** — Avoids redundant external API calls with optional TTL.
- **taste_signals** — Aggregated preferences: genre affinity, label affinity, era preference, duration preference. Evidence-backed with references to source data.
- **research_threads** — Multi-step research journeys with steps and findings, for resuming investigations.

---

## Current State (v0)

The plugin is built and packaged. 27 files, ~1800 lines. Everything needed for a working v0:

**Functional:**
- Full Apple Music library access via 7 JXA scripts (now playing, search, playback, playlists, export, annotations, play-by-ID)
- MusicBrainz lookup for artists, releases, recordings, labels, credits, and discographies
- Knowledge graph with full CRUD, session logging, caching, and search
- 6 slash commands covering the core workflows
- 4 fully defined personas with distinct search strategies, scoring biases, and anti-patterns
- 2 subagents (crate-digger, historian) for delegated research
- Session-start hook for context injection
- Setup script for one-command installation

**Not yet built (future iterations):**
- Discogs integration (marketplace data, format info, richer credit data)
- Bandcamp integration (independent label graph, tag-based discovery)
- LanceDB vector embeddings for hybrid semantic + structured search
- Additional subagents for harmonic-dj and anti-bubble personas
- Local Apple Music Library XML/SQLite reader for historical data beyond what JXA exposes
- MCP server wrapping for consumption by clients beyond Claude Code
- Release monitoring / personal A&R agent
- Taste profile evolution tracking over time

---

## The Vision, Longer Term

The unified MCP server is the natural evolution. Instead of exposing raw API surfaces, it composes them into intent-level tools. The agent doesn't call `musicbrainz_search` then `apple_music_catalog_search` then `discogs_release` — it calls `deep_lookup` with an artist name and gets back a unified, richly cross-referenced result. The MCP server does fan-out, deduplication, and entity resolution internally. Personas could be served via MCP prompts and resources to any compatible client.

LanceDB (or similar) adds vector search over embeddings alongside structured metadata filtering. Music similarity is multi-dimensional and context-dependent — "similar to Alva Noto" means completely different things depending on whether you mean timbral similarity, label affinity, conceptual approach, era, or collaborative network proximity. Hybrid search handles this naturally.

The local Apple Music Library XML and the newer `Music Library.musiclibrary` SQLite database on modern macOS contain data that no API exposes — complete play history, smart playlist rule definitions, local-to-cloud mapping. An agent that can read this data knows how you've *lived with* your music, not just what's in your collection.

Combined with the persona system, you essentially get a team of specialist music advisors with different expertise who share access to your collection and listening context. That doesn't exist anywhere.

---

## Spirit

This project exists at the intersection of three convictions:

1. **The best music technology is the kind that deepens your relationship with music, not the kind that optimizes your engagement with a platform.** Recommendation algorithms have made discovery frictionless and shallow. The interesting problem is making discovery *meaningful* — contextual, intentional, surprising in ways you can learn from.

2. **A personal music library is a form of self-knowledge.** It's a record of who you've been, what you've cared about, what you've abandoned, and what you keep coming back to. Treating it as a queryable, annotated knowledge graph — rather than a flat list of favorites — makes that self-knowledge accessible.

3. **Agentic tools are most powerful when they augment taste rather than replace it.** The agent shouldn't decide what you like. It should give you better tools for understanding what you like, finding more of it, finding the *opposite* of it, and building intentional listening experiences that no algorithmic feed would ever construct.

The goal is an experience where you open your terminal, say "what's playing?", and the agent knows not just the track name but the label, the mastering engineer, what else that engineer worked on, what you have in your library from that lineage, what you're missing, and what the crate-digger in the back room would pull off the shelf for you next.

---

*music-agent v0.1.0 — built in a single conversation, March 15, 2026.*
