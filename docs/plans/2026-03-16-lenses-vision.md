# Lenses: A Framework for New Musical Perspectives

**Date**: 2026-03-16
**Status**: Vision / Design Conversation Capture
**Context**: Brainstorming session on taking music-agent to the next level without MusicKit CLI, leaning into AppleScript/JXA + Python automation.

---

## The Core Insight

The most powerful thing music-agent can become is not a better recommendation engine or a smarter playlist builder. It's a system that offers **lenses** — ways of perceiving your music collection and the broader music universe from angles that literally don't exist in any player, service, or tool.

Visualization is one delivery mechanism, but what matters is the **perspective itself**. A lens reframes your relationship with music. It reveals structure, connection, and meaning that was always there but invisible.

---

## The Lenses

### The Drift

Start with a track. The credit graph chooses the next one. Each track connects to the previous through a shared human — producer, engineer, mastering engineer, label, collaborator. You don't choose where it goes. The *network itself* is the DJ.

This is not shuffle (random). Not algorithmic (optimizing engagement). Not curated (human playlist). It's **topological** — the shape of human collaboration determines the journey. Every transition has a reason: "this track was mastered by the same person who engineered your previous track."

A completely novel traversal mode.

### Six Degrees

"Connect Bjork to Autechre through credits."

Interactive, surprising, reveals hidden structure. The shortest path through the credit graph between any two artists becomes a way to *understand* the topology of music. Sometimes the path goes through a mastering engineer. Sometimes through a label. Sometimes through a side project nobody's heard of.

Becomes a game, a learning tool, and a discovery engine simultaneously.

### The Seasonal Self

With living awareness (background monitoring of what you're playing), your listening becomes a time series. Not Spotify Wrapped — deeper, continuous, reflective.

"You've been drifting toward longer ambient forms this month. Your most-traversed credit node is Rashad Becker. You haven't touched your jazz corner in 6 weeks. Your listening entropy decreased — you're in a narrowing phase."

Taste as a living, evolving signal, not a static profile.

### The Expedition

The credit graph has edges that lead *out of* your collection. Every artist, engineer, and label you know connects to work you don't have. The Expedition identifies the **border of your musical territory** — the most promising edges leading into unknown space.

"Your collection's credit graph connects to 847 releases you don't own. Here are the 5 most interesting border crossings, ranked by how many of your known-and-loved credits converge on them."

The border of your territory *is* your discovery frontier.

---

## The Underlying Framework

Every lens above is a composition of the same primitives. The question isn't "how do we build four features" — it's "what foundational layers make ALL of them (and future lenses we haven't imagined) possible?"

### Layer 1: Dense Knowledge Graph (Data Enrichment)

The current KB has entities and relations from MusicBrainz. To power these lenses, the graph needs to be **much denser**.

**Discogs integration** (`python3-discogs-client`):
- Richer credit data (MusicBrainz has producers/engineers; Discogs has mastering houses, sleeve designers, A&R, remix credits, featured artists)
- Format and pressing data (vinyl vs CD vs digital — cultural signal)
- Label hierarchies (sublabels, parent labels, distribution chains)
- Marketplace data (rarity signal — a proxy for cultural scarcity)

**Cross-source entity resolution**:
- Same artist in Apple Music library + MusicBrainz + Discogs = one entity, multiple source IDs
- The `sources` JSON field on entities already supports this; needs active linking logic

**Relationship density targets**:
- Every release should have: artist(s), label, producer(s), engineer(s), mastering
- Every artist should have: label affiliations, collaborator network, discography
- Every label should have: roster, parent/sublabel hierarchy, geographic base

The denser the graph, the more interesting every lens becomes. Six Degrees gets shorter paths. The Drift has more options at each step. The Expedition sees further past the border.

### Layer 2: Temporal Stream (Living Awareness)

A background process that continuously logs what's playing to the KB.

**Implementation**: `launchd` plist (macOS-native, no cron needed) that runs a lightweight Python script every 30 seconds:
1. Call `now_playing.jxa` — get current track + player state
2. If track changed since last poll, log the transition
3. If same track still playing, note continued listening (vs skip)
4. Write to `session_tracks` table with timestamp

**What this enables**:
- **Time-of-day patterns**: What do you listen to in the morning vs evening?
- **Listening velocity**: How many tracks per hour? (High = browsing/skipping. Low = deep listening.)
- **Dwell time**: How long on each track? Proxy for engagement without explicit rating.
- **Session boundaries**: Gaps in listening = session breaks. Auto-segment into sessions.
- **Weekly/monthly/seasonal rhythms**: Aggregated temporal patterns.
- **Recency-weighted taste signals**: What you listened to this week matters more than last year.

**Data this generates over time**:
- After 1 week: daily rhythm visible
- After 1 month: weekly patterns, genre drift detectable
- After 3 months: seasonal self becomes meaningful
- After 1 year: full temporal portrait, year-over-year comparison

This is the layer that makes the Seasonal Self lens possible, and enriches every other lens with temporal context ("you last encountered this credit node 3 months ago").

### Layer 3: Graph Engine (Traversal Primitives)

This is the critical middle layer. A Python module (using `networkx`) that loads the KB into an in-memory graph and exposes traversal operations. Every lens is a composition of these primitives.

**Core operations**:

| Primitive | What it does | Powers which lens |
|-----------|-------------|-------------------|
| `shortest_path(a, b)` | Find shortest credit path between two entities | Six Degrees |
| `random_walk(start, edge_types, steps)` | Weighted random walk following specified edge types | The Drift |
| `border_nodes(collection_ids)` | Entities connected to your collection but not in it | The Expedition |
| `centrality(subgraph)` | Most-connected nodes in a subgraph | Seasonal Self, all lenses |
| `clusters(min_size)` | Detect communities/scenes in the graph | Cartography, Expedition |
| `ego_graph(entity, depth)` | N-hop neighborhood around an entity | All research commands |
| `bridge_nodes()` | Entities connecting otherwise-separate clusters | Six Degrees, Expedition |
| `temporal_weight(entity, window)` | Recency-weighted importance of an entity | Seasonal Self, Drift |

**Implementation approach**:
- `scripts/graph/engine.py` — loads entities + relations from SQLite into `networkx.Graph`
- Exposes CLI: `python3 engine.py <operation> [args]` (same pattern as `db.py`)
- Results are JSON (same pattern as everything else)
- Graph rebuilt on each invocation (SQLite is small; this is fast) or cached with invalidation

**Why networkx**:
- Pure Python, no compilation, no server
- Handles graphs up to ~100K nodes trivially (our KB will be 1K-10K entities)
- Built-in shortest path, centrality, community detection, random walks
- Fits plugin architecture perfectly (just another Python script)

### Layer 4: Lenses (Composable Perspectives)

Each lens is a **command** (or mode within a command) that composes graph primitives + temporal queries + optional persona perspective.

A lens is NOT a feature. It's a **perspective function**:

```
Lens(seed, context, persona?) → Experience
```

Where:
- **seed** = starting point (track, artist, concept, mood, time period)
- **context** = temporal state (what you've been listening to, time of day, season)
- **persona** = optional search strategy bias (crate-digger follows obscure edges, historian follows chronological ones, harmonic-dj follows energy-compatible ones)

This means:
- The Drift + crate-digger persona = follows the most obscure credit connections
- The Drift + historian persona = follows chronological influence chains
- Six Degrees + harmonic-dj = finds paths where each step is energy-compatible
- The Expedition + anti-bubble = finds border crossings in genres you've never touched

**Lenses are composable with personas.** 4 lenses x 4 personas = 16 distinct experiences from the same framework.

---

## What Doesn't Exist Anywhere Else

To be explicit about what's novel here:

1. **Credit-graph traversal as a listening mode** (The Drift) — No player, service, or tool lets the network of human collaboration determine what you hear next. Spotify's "related artists" is a black box. This is transparent, traceable, and surprising.

2. **Topological discovery** (Six Degrees) — No tool lets you explore the *shape* of music's collaborative network interactively. The closest is Wikipedia rabbit holes, but those aren't queryable, traversable, or connected to your library.

3. **Temporal taste as a living signal** (Seasonal Self) — Spotify Wrapped is annual, shallow, and engagement-optimized. This is continuous, deep, and self-knowledge-oriented. "How am I changing?" is a question no music service answers.

4. **Border-aware discovery** (The Expedition) — Every recommendation engine suggests things "like what you already like." The Expedition explicitly maps the *edge* of your known territory and shows you what's just past it, with the credit connections that make it reachable. Discovery as cartography.

5. **Perspective composability** (Lenses x Personas) — No system offers the same musical question answered from structurally different viewpoints. "Build me a drift" from a crate-digger vs a historian produces fundamentally different journeys through the same graph.

---

## Implementation Progression

### Phase 1: The Credit Universe

**Goal**: Make the knowledge graph dense enough to power graph traversal.

- Integrate Discogs via `python3-discogs-client`
  - New script: `scripts/lookup/discogs_lookup.py` (same CLI pattern as musicbrainz_lookup.py)
  - Entity resolution: link Discogs IDs to existing MusicBrainz entities
  - New relation types: `remixed_by`, `mastered_at` (studio), `designed_by` (sleeve), `a_and_r`
  - Label hierarchy: `sublabel_of` relation
- Enrich existing KB entities with Discogs credits on demand
- Add `scripts/graph/engine.py` with core traversal primitives
- Validate: run `shortest_path` and `border_nodes` on real data, confirm interesting results

### Phase 2: Living Awareness

**Goal**: The system continuously knows your listening state.

- Create `scripts/monitor/listener.py` — lightweight polling script
- Create `com.music-agent.listener.plist` — launchd config for 30-second polling
- Install/uninstall via setup script or new `/monitor` command
- Extend `db.py` with temporal query helpers (listening in time window, session boundaries)
- Add temporal weighting to graph engine
- Validate: run for 1 week, confirm daily rhythm data is meaningful

### Phase 3: The Lenses

**Goal**: Ship the four lenses as commands/modes.

- `/drift [seed] [--persona]` — credit-graph-driven traversal, builds and plays queue
- `/connect <artist-a> <artist-b>` — Six Degrees, find and display credit path
- `/self [--window <days>]` — Seasonal Self, temporal taste portrait
- `/frontier [--persona]` — The Expedition, border-node discovery
- Each lens composes graph engine primitives + temporal queries + persona bias
- Each lens stores its results in KB (the lenses themselves generate knowledge)

### Phase 4: Cartographic Rendering (Optional, Additive)

**Goal**: When a visual would amplify the perspective, generate one.

- Python script using `networkx` layouts + SVG/HTML generation
- `/map [entity] [--depth N]` — render ego graph as interactive HTML
- Opens in browser via `open` command
- Not required for any lens to work — purely additive

---

## The Spirit

This system doesn't compete with Spotify or Apple Music's recommendation engines. It operates on a fundamentally different axis.

Streaming services answer: **"What should I play next to keep you listening?"**

This system answers: **"What is the shape of your musical world, and what's just past the edge of it?"**

The lenses are tools for self-knowledge and exploration. They treat a music collection not as a consumption queue but as a **territory of accumulated taste** — navigable, queryable, and always revealing new structure.

The best music technology deepens your relationship with music, not your engagement with a platform.

---

## Technical Foundation Summary

| Layer | Implementation | Key Dependency | Fits Plugin Arch? |
|-------|---------------|----------------|-------------------|
| Dense KB | `discogs_lookup.py` + entity resolution | `python3-discogs-client` | Yes (Python script) |
| Temporal Stream | `listener.py` + `launchd` plist | None (osascript + sqlite3) | Yes (shell + Python) |
| Graph Engine | `engine.py` using `networkx` | `networkx` | Yes (Python script) |
| Lenses | New commands composing above | All above | Yes (markdown commands) |
| Cartography | SVG/HTML generation | `networkx` layouts | Yes (Python script) |

Zero servers. Zero build steps. Zero new architecture. Just more scripts, denser data, and smarter traversal.

---

*This document captures the spirit and critical details of a brainstorming session on 2026-03-16. The four lenses (Drift, Six Degrees, Seasonal Self, Expedition) emerged from asking: "What perspectives on music are literally impossible with existing tools?" The answer is: perspectives that require a dense credit graph, temporal awareness, and composable traversal — none of which streaming services expose to users.*
