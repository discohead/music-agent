# music-agent

**An Agentic Music Companion for Apple Music + Claude Code**

*Project Vision Document — March 17, 2026*

---

## Origin

This project grew out of two conversations that happened back-to-back over 48 hours.

The first, on March 16, started with a research question — does Apple provide a Swift framework for Apple Music APIs? — and escalated into a full engineering effort: design and implement **Aux**, a pure-Swift macOS application and CLI that exposes 100% of Apple's MusicKit framework as structured JSON over stdio for terminal coding agents. That conversation produced an 858-line design document, a 3,341-line YAML API spec defining 88 commands, and then a complete TDD implementation — 24 phases, 466 tests (444 passing, 22 disabled integration tests), 7 live service implementations, a SwiftUI auth GUI, and a working `aux` binary. Aux was built in a single session following strict red-green-refactor discipline.

The second conversation, on March 17, asked the deeper question: now that we have a programmatic bridge to Apple Music, **what would an agentic music companion actually look like?** Not just a CLI — a system with curatorial intelligence, music research capabilities, a persistent knowledge graph, and specialized personas that implement different discovery strategies. That conversation produced **music-agent**, a Claude Code plugin (27 files, ~1800 lines) with slash commands, subagents, persona definitions, JXA scripts, MusicBrainz integration, and a SQLite knowledge graph.

Together, Aux provides the *infrastructure* — the reliable, tested, type-safe bridge to Apple Music — and music-agent provides the *intelligence* — the curatorial layer, personas, knowledge accumulation, and conversational interface.

The idea crystallized through a series of escalating realizations:

1. The APIs exist. MusicKit gives you catalog search, library access, playlist CRUD, playback control, recommendations, and charts. But no single Apple API covers all functionality — MusicKit, the REST API, and Music.app's AppleScript interface each expose unique capabilities.
2. Aux solves this with a three-layer architecture: MusicKit framework for catalog and type-safe library reads, REST API via `MusicDataRequest` for library writes, and an AppleScript bridge for playback, metadata writing, artwork, file import, AirPlay, EQ, and play statistics. One CLI, three backends, unified JSON output.
3. On top of this infrastructure, MusicBrainz provides deep credits, discographies, and label data. Discogs, Bandcamp, and others fill in remaining gaps.
4. A Claude Code plugin is just text files, prompts, and scripts. The agent *is* the interface. No separate UI to build.
5. The comment field on every Apple Music track is an unused metadata layer the agent can write to. Agent knowledge embeds directly into the library itself.
6. A local SQLite knowledge graph accumulates everything the agent discovers. The system gets smarter with every interaction without any explicit training.

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

Every track in Apple Music has a `comment` field that almost nobody uses. The agent can write structured annotations directly into it — tags like `#deep-cut`, `#microsound`, `#crate-dig-find`, or richer JSON metadata. This means agent knowledge gets embedded *into the library itself*, survives across sessions without any external database, syncs across devices via iCloud, and is searchable via both Aux and JXA. It's a free, persistent metadata layer.

### Taste Archaeology

Your own listening history as a reflective tool. "What was I into in 2019 that I've drifted away from?" "What genres do I have zero representation in despite loving adjacent genres?" "Which tracks have I played 200+ times, and what do they have in common?" Streaming services have this data but don't expose it as a tool for self-understanding.

---

## Non-Obvious Features

Beyond the obvious research, curation, and playlist building:

**Energy arc composition.** Not "similar vibes" but constructing a deliberate emotional trajectory across a queue. "Build me 90 minutes that starts ambient, builds tension for 30 minutes, peaks, then dissolves." The playlist itself becomes a composed object with structure.

**Anti-recommendation.** "What's highly rated in genres I like that I would *never* encounter through my current listening patterns?" Collaborative filtering converges; an agent can be instructed to diverge.

**Release monitoring with taste-aware filtering.** Not "new releases in electronic" (thousands per week) but "new releases that share at least two attributes with things I've favorited in the last 6 months, weighted toward small labels I've shown affinity for." A personal A&R agent.

**Session memory.** "What was that playlist I was vibing with last month that started really ambient?" becomes a real query because sessions are logged objects in the knowledge graph.

---

## Architecture

### Aux: The Foundation Layer

Aux is a completed, tested macOS application and CLI that bridges Apple Music to structured JSON over stdio. It exists because no single Apple API covers all of Apple Music's functionality, so Aux unifies three backends behind one interface.

**Three-layer service architecture:**

| Layer | Technology | What It Provides |
|-------|-----------|-----------------|
| **MusicKit framework** | Native Swift | Catalog search, library reads, auth, recommendations, charts (type-safe, automatic tokens) |
| **REST API** | `MusicDataRequest` | Library writes — create playlists, add to library, ratings — because `MusicLibrary.shared.add()` is `@available(macOS, unavailable)` |
| **AppleScript bridge** | `NSAppleScript` → Music.app | Playback control, metadata writing, artwork, file import, track deletion, AirPlay, EQ, play stats (capabilities that exist nowhere else) |

**Build and test status (as of March 16, 2026):**

| Metric | Value |
|--------|-------|
| Implementation phases | 24/24 complete |
| Total tests | 466 (444 passing, 22 disabled integration) |
| Leaf commands | 88 across 9 groups |
| Command groups | auth, search, catalog, library, playback, recommendations, recently-played, ratings, api |
| Live service implementations | 7 (auth, catalog, library, REST, AppleScript, recommendations, recently-played) |
| DTO types | 19 with explicit snake_case CodingKeys |
| Exit codes | 9 (success through unavailable) |

**Key architectural patterns:**

- **Handler/Command split**: Every CLI command has a Handler (in AuxKit, testable with mocks) and a Command (in auxCLI, thin ArgumentParser wrapper). Tests target handlers, not commands.
- **Protocol-based DI**: Seven service protocols with mock implementations. `ServiceContainer` holds all services; `.mock()` returns test doubles.
- **Output envelope**: All output goes through `OutputEnvelope<T>` (success with optional `PaginationMeta`) or `CLIErrorResponse`. JSON to stdout, diagnostics to stderr.
- **VS Code app pattern**: Aux.app is a macOS bundle that handles MusicKit auth via SwiftUI GUI; the `aux` CLI binary is symlinked to `/usr/local/bin/aux` from the app's preferences. GUI for auth, CLI for everything else.

### music-agent: The Intelligence Layer

The Claude Code plugin that provides curatorial intelligence, research capabilities, personas, and the knowledge graph on top of Aux's infrastructure.

**Plugin structure:**

```
music-agent/
├── commands/           # /now, /dig, /queue, /who, /taste, /kb
├── agents/             # crate-digger, historian subagents
├── personas/           # 4 curatorial perspectives with search strategies
├── skills/             # Core orchestration skill
├── hooks/              # Session-start context injection
├── scripts/
│   ├── apple-music/    # JXA scripts (v0) — to be replaced by aux calls (v1)
│   ├── lookup/         # MusicBrainz Python lookups
│   └── db/             # Knowledge graph SQLite operations
└── db/                 # Schema definition
```

### Full Stack

```
┌─────────────────────────────────────────────────┐
│         Claude Code Plugin: music-agent          │
├──────────────────┬──────────────────────────────┤
│   Commands       │   Personas & Subagents       │
│   /now           │   crate-digger               │
│   /dig           │   historian                  │
│   /queue         │   harmonic-dj                │
│   /who           │   anti-bubble                │
│   /taste         │                              │
│   /kb            │   Hooks                      │
│                  │   session-start context       │
├──────────────────┴──────────────────────────────┤
│              Scripts & Tools                      │
│  ┌──────────────┬──────────────┬──────────────┐ │
│  │ aux CLI      │  Python      │  SQLite      │ │
│  │ (88 commands)│  musicbrainz │  knowledge   │ │
│  │ 3-layer arch │  _lookup     │  graph       │ │
│  │ MusicKit +   │              │  db.py       │ │
│  │ REST API +   │              │              │ │
│  │ AppleScript  │              │              │ │
│  └──────────────┴──────────────┴──────────────┘ │
│  ┌──────────────────────────────────────────────┐│
│  │  JXA scripts (v0 fallback / supplemental)    ││
│  └──────────────────────────────────────────────┘│
├─────────────────────────────────────────────────┤
│              Data Layer                          │
│  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  Apple Music      │  │  ~/.music-agent/     │ │
│  │  MusicKit + REST  │  │  knowledge.db        │ │
│  │  + Music.app      │  │  (SQLite)            │ │
│  │  via Aux          │  │                      │ │
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

## Current State

### Aux (complete)

The foundation is built and tested. 88 commands across 9 groups, 466 tests, 7 live service implementations, SwiftUI auth GUI, CLI installer. Strict TDD — every line of production code was preceded by a failing test. The `aux` binary runs, outputs structured JSON, and covers the full surface area of MusicKit, the Apple Music REST API, and Music.app's AppleScript interface.

### music-agent plugin (v0 — functional prototype)

The Claude Code plugin is built and packaged (27 files, ~1800 lines). The v0 uses JXA scripts for Apple Music access — a pragmatic choice that validates the experience without requiring Aux installation. JXA covers ~70% of what Aux can do (local library access, playback, playlists, metadata, annotations) but lacks cloud catalog search, subscription management, recommendations, charts, and authenticated REST API calls.

**What's functional in v0:**
- Full Apple Music library access via 7 JXA scripts
- MusicBrainz lookup for artists, releases, recordings, labels, credits, and discographies
- Knowledge graph with full CRUD, session logging, caching, and search
- 6 slash commands covering the core workflows (/now, /dig, /queue, /who, /taste, /kb)
- 4 fully defined personas with distinct search strategies, scoring biases, and anti-patterns
- 2 subagents (crate-digger, historian) for delegated research
- Session-start hook for context injection
- Setup script for one-command installation

### Evolution Path

**v0 (built):** Claude Code plugin + JXA scripts + Python + SQLite. Validates the experience. Works today on any Mac with Apple Music and Python 3.

**v1 (ready to integrate):** Replace JXA scripts with `aux` CLI calls. The plugin's commands, personas, and knowledge graph stay the same — only the script layer changes from `osascript` to `aux`. This unlocks the full power of MusicKit: cloud catalog search across Apple Music's entire library, personalized recommendations, charts, recently played, ratings management, and authenticated REST API operations. The three-layer architecture of Aux means every capability of Apple Music becomes available to the agent.

**v2 (planned):** MCP server wrapping Aux + MusicBrainz + Discogs + Bandcamp + the knowledge graph. Intent-level tools like `deep_lookup` that do fan-out, deduplication, and entity resolution across all data sources. Personas served via MCP prompts and resources to any compatible client. Any AI — not just Claude Code — can consume the music intelligence layer.

**v3 (vision):** LanceDB vector embeddings for hybrid semantic + structured search. Every entity gets both a vector embedding and structured metadata. Queries like "semantically similar to this track BUT constrained to releases on independent labels after 2020 that I haven't heard" become natural. Release monitoring as a persistent background agent. Taste profile evolution tracking over time.

---

## Spirit

This project exists at the intersection of three convictions:

1. **The best music technology is the kind that deepens your relationship with music, not the kind that optimizes your engagement with a platform.** Recommendation algorithms have made discovery frictionless and shallow. The interesting problem is making discovery *meaningful* — contextual, intentional, surprising in ways you can learn from.

2. **A personal music library is a form of self-knowledge.** It's a record of who you've been, what you've cared about, what you've abandoned, and what you keep coming back to. Treating it as a queryable, annotated knowledge graph — rather than a flat list of favorites — makes that self-knowledge accessible.

3. **Agentic tools are most powerful when they augment taste rather than replace it.** The agent shouldn't decide what you like. It should give you better tools for understanding what you like, finding more of it, finding the *opposite* of it, and building intentional listening experiences that no algorithmic feed would ever construct.

The goal is an experience where you open your terminal, say "what's playing?", and the agent knows not just the track name but the label, the mastering engineer, what else that engineer worked on, what you have in your library from that lineage, what you're missing, and what the crate-digger in the back room would pull off the shelf for you next.

---

*Aux v1.1.0 — 88 commands, 466 tests, built March 16, 2026.*
*music-agent v0.1.0 — 27 files, ~1800 lines, built March 17, 2026.*
*Both built in single conversations.*
