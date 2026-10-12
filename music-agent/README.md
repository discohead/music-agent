# 🎵 music-agent

An agentic music companion for Apple Music + Claude Code.

**music-agent** turns your terminal into a music research lab, crate-digging station, and intelligent playlist composer. It connects Claude Code directly to your Apple Music library, external music databases, and a local knowledge graph that gets smarter with every interaction.

## What it does

- **`/now`** — What's playing right now? Get rich metadata, artist research, and context from your knowledge graph.
- **`/dig <subject>`** — Deep research on an artist, label, release, or concept. Cross-references MusicBrainz with your library.
- **`/queue <seed>`** — Build an intelligent queue from any seed: an artist, mood, concept, or abstract idea. Composed with intentionality, not shuffled.
- **`/who <artist>`** — Explore the credit graph. Who produced this? Who mastered it? What else did they work on?
- **`/taste`** — Analyze your library. Discover patterns, blind spots, dormant favorites, and taste signals.
- **`/kb`** — Inspect and query your music knowledge graph directly.

## Personas

Add `--persona <name>` to any command to activate a curatorial perspective:

| Persona | Focus | Search Strategy |
|---------|-------|-----------------|
| **crate-digger** | Obscure finds, deep cuts, small labels | Follow credits, explore rosters, prioritize the overlooked |
| **historian** | Lineage, context, influence chains | Build timelines, trace movements, map scenes |
| **harmonic-dj** | Energy arcs, transitions, flow | Compose journeys, think in tempo/density/mood |
| **anti-bubble** | Filter bubble breaking | Cross genre/geography/era boundaries deliberately |

## Architecture

```
music-agent/
├── commands/           # Slash commands (/now, /dig, /queue, /who, /taste, /kb)
├── agents/             # Subagents (crate-digger, historian, harmonic-dj, anti-bubble)
├── personas/           # Curatorial perspectives with search strategies
├── skills/             # Core orchestration skill
├── hooks/              # Session start context injection
├── scripts/
│   ├── apple-music-jxa-v0/  # Archived v0 JXA scripts (replaced by aux CLI)
│   ├── lookup/         # MusicBrainz Python lookups
│   └── db/             # Knowledge graph SQLite operations
└── db/                 # Schema definition
```

### Data Sources

| Source | Access Method | What It Provides |
|--------|--------------|------------------|
| **Apple Music Library** | aux CLI (MusicKit + REST + AppleScript) | Tracks, playlists, play counts, ratings, loved status, comments, playback control, catalog search, recommendations, charts, queue management |
| **MusicBrainz** | Python API | Artist metadata, discographies, release credits, label info, recording data |
| **Knowledge Graph** | SQLite | Accumulated entities, relations, annotations, sessions, taste signals |

### The Knowledge Graph

Every interaction enriches a local SQLite database at `~/.music-agent/knowledge.db`. It stores:

- **Entities**: Artists, labels, releases, tracks, engineers — from any source
- **Relations**: released_on, mastered_by, member_of, similar_to, influenced_by...
- **Annotations**: Persona-attributed notes, tags, recommendations
- **Sessions**: Chronological listening logs with skip tracking
- **Taste Signals**: Aggregated preference patterns

The comment field on Apple Music tracks doubles as an in-library annotation layer — agent tags like `#deep-cut` and `#crate-dig-find` persist in the library itself.

## Installation

### Prerequisites

- macOS with Apple Music app installed and running
- `aux` CLI v1.1.0+ (the Apple Music bridge — install from the aux project)
- Python 3.7+ with pip
- Claude Code
- `jq` (install via `brew install jq` if not present)

### Install the Plugin

**Option A: From GitHub (recommended)**

```bash
# Add the marketplace and install
/plugin marketplace add <your-org>/music-agent
/plugin install music-agent
```

**Option B: From local directory**

```bash
# Clone the repo
git clone <repo-url>
cd music-agent

# Add as a local dev marketplace
/plugin marketplace add /path/to/music-agent/music-agent
/plugin install music-agent@music-agent-dev
```

**Option C: Manual symlink**

```bash
# Symlink into your Claude Code plugins directory
ln -s /path/to/music-agent/music-agent ~/.claude/plugins/music-agent
```

After installing, **restart Claude Code** for the plugin to load.

### Run Setup

```bash
bash ~/.claude/plugins/cache/<marketplace>/music-agent/<version>/scripts/setup.sh
```

Or, if installed locally:

```bash
bash /path/to/music-agent/music-agent/scripts/setup.sh
```

Setup will:
1. Verify Python 3 is available
2. Install the `musicbrainzngs` Python package
3. Initialize the SQLite knowledge graph at `~/.music-agent/knowledge.db`
4. Set script permissions
5. Test Apple Music connectivity
6. Test MusicBrainz API access

### Verify Installation

After restarting Claude Code, you should see a SessionStart message indicating music-agent is active. Try:

```
/now
```

If Apple Music is playing, you'll get rich track metadata and artist context. If nothing is playing, the plugin will tell you and offer alternatives.

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Plugin not loading | Restart Claude Code after installation |
| Commands not appearing | Check `/plugin list` to verify installation |
| Apple Music errors | Ensure Apple Music.app is open and playing |
| MusicBrainz errors | Check internet connection; API has 1 req/sec rate limit |
| Database errors | Run `python3 scripts/db/db.py init` to reinitialize |
| `musicbrainzngs` missing | Run `pip3 install musicbrainzngs` |

## Examples

```
> /now
Playing: "Multistability" by Mark Fell (2010, Raster-Noton)
Play count: 47 | Added: 2018-03-12 | Loved: ✓
[researches artist, shows context, offers next steps]

> /dig Mark Fell --persona crate-digger
[deep research with credit graph, library cross-reference,
 discoveries organized with "in library" / "not in library" markers]

> /queue "start ambient, build tension for 30 minutes, then dissolve" --count 15 --save "March Session"
[builds intentional queue with energy arc, creates Apple Music playlist]

> /who "Rashad Becker"
[traces mastering credits across experimental electronic music,
 surfaces connections to artists in your library]

> /taste genres
[analyzes genre distribution, identifies blind spots and concentrations]
```

## Philosophy

Streaming recommendation algorithms optimize for platform engagement. music-agent optimizes for **your relationship with music**. It treats your library as a knowledge graph you can converse with — not a passive collection, but an active, queryable, annotated body of knowledge that grows smarter with every interaction.

## License

MIT
