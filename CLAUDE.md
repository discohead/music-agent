# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

music-agent is a Claude Code plugin that turns the terminal into an agentic music companion for Apple Music. It connects Claude Code to the local Apple Music library (via JXA/osascript), MusicBrainz (via Python), and a local SQLite knowledge graph that accumulates entities, relations, and annotations over time.

This is a **plugin-only architecture** — no servers, no build step. The entire system is text files (markdown commands, personas, agents), shell scripts (JXA for Apple Music, Python for MusicBrainz/SQLite), and a SQLite database at `~/.music-agent/knowledge.db`.

## Repository Structure

The plugin lives in `music-agent/` (subdirectory). The root also contains `music-agent-vision.md` (project vision/design doc).

```
music-agent/                        # The Claude Code plugin
├── .claude-plugin/
│   ├── plugin.json                 # Plugin manifest
│   └── marketplace.json            # Dev marketplace config (points to local source)
├── commands/                       # Slash commands: /now, /dig, /queue, /who, /taste, /kb
├── agents/                         # Subagents: crate-digger, historian, harmonic-dj, anti-bubble
├── personas/                       # Curatorial perspectives (matching agents above)
├── skills/music-agent/SKILL.md     # Auto-trigger skill for music-related conversations
├── hooks/hooks.json                # SessionStart hook → session_context.sh
├── scripts/
│   ├── apple-music/*.jxa           # 7 JXA scripts for Apple Music access
│   ├── lookup/*.py                 # MusicBrainz API wrapper
│   ├── db/db.py                    # Knowledge graph CRUD operations
│   └── session_context.sh          # SessionStart hook script (playback state + KB stats)
└── db/schema.sql                   # SQLite schema definition
```

## Key Scripts

### Apple Music (JXA via osascript)
All return JSON. Run with `osascript -l JavaScript <script>`.
- `now_playing.jxa` — current track with metadata
- `search_library.jxa "<query>" [field]` — search library by name/artist/album
- `play_track.jxa "<persistentID>"` — play by ID
- `playback.jxa <play|pause|next|prev|status>` — transport control
- `playlists.jxa <list|create|add> [args]` — playlist CRUD
- `library_export.jxa [limit]` — export library data
- `annotate.jxa <persistentID> <comment>` — write to track comment field

### MusicBrainz (Python)
```
python3 scripts/lookup/musicbrainz_lookup.py <type> <query>
```
Types: `artist`, `release`, `recording`, `label`, `credits <release-mbid>`, `discography <artist-mbid>`

Requires `musicbrainzngs` (installed by setup). Rate limit: 1 req/sec.

### Knowledge Graph (Python + SQLite)
```
python3 scripts/db/db.py <command> [args]
```
Commands: `init`, `store-entity <json>`, `store-relation <json>`, `annotate <json>`, `query <sql>`, `search <term> [type]`, `log-session <json>`, `cache-get <key>`, `cache-set <key> <json>`, `stats`

DB location: `~/.music-agent/knowledge.db`. Schema in `db/schema.sql`.

### Discogs (Python)
```
python3 scripts/lookup/discogs_lookup.py <type> <query|id>
```
Types: `artist`, `release`, `credits`, `label`, `label-releases`, `artist-releases`

Requires `python3-discogs-client` (installed by setup). Auth: `DISCOGS_TOKEN` env var or `~/.music-agent/config.json`.

### Graph Engine (Python + networkx)
```
python3 scripts/graph/engine.py <command> [args]
```
Commands: `shortest-path`, `ego`, `border`, `walk`, `centrality`, `clusters`, `stats`

Powers the Lenses framework: Drift (walk), Six Degrees (shortest-path), Expedition (border).

### Configuration
```
python3 scripts/config.py <get|set|show> [key] [value]
```
Manages `~/.music-agent/config.json`. Used for API tokens and settings.

## Plugin Installation

```bash
# Load plugin for development/testing (from the repo root)
claude --plugin-dir ./music-agent
```

## Setup

```bash
bash music-agent/scripts/setup.sh
```
Installs `musicbrainzngs`, initializes the SQLite DB, sets permissions, and tests Apple Music + MusicBrainz connections.

**Requirements:** macOS, Apple Music app running, Python 3, `osascript`, `sqlite3`, `jq`.

## Architecture Notes

- **Personas are not tone wrappers** — they define distinct search strategies, scoring biases, and anti-patterns. Each persona in `personas/` has `<search_strategy>`, `<scoring_bias>`, and `<anti_patterns>` sections that change how results are selected and ranked.
- **Subagents** (`agents/`) are autonomous research delegates with constrained workflows. They read their corresponding persona file, conduct multi-step MusicBrainz lookups, cross-reference against the user's library, and store all discoveries in the knowledge graph.
- **Commands** (`commands/`) use `${CLAUDE_PLUGIN_ROOT}` to reference scripts. They invoke JXA via `osascript` and Python scripts via `python3`.
- **The comment field** on Apple Music tracks is used as an in-library annotation layer (tags like `#deep-cut`, `#crate-dig-find`). Written via `annotate.jxa`.
- **All scripts output JSON** — commands and agents parse this output, never present raw JSON to users.
- **The SessionStart hook** runs `scripts/session_context.sh`, which calls `now_playing.jxa` and `db.py stats` to inject current playback state and knowledge graph stats into every new conversation.
- **The auto-trigger skill** (`skills/music-agent/SKILL.md`) activates on any music-related conversation, providing tool references and workflow patterns without requiring a slash command.

## Development Conventions

- Scripts in `scripts/` are the data access layer; commands/agents/personas are the prompt layer. Keep them separate.
- Entity IDs in the knowledge graph use MusicBrainz IDs (MBIDs) when available, generated IDs otherwise.
- Relations use `ON CONFLICT ... DO UPDATE` for idempotent upserts.
- The `lookup_cache` table prevents redundant MusicBrainz API calls.
- JSON metadata fields use SQLite's `json_patch()` for partial updates on entities.

## Testing Individual Scripts

```bash
# Apple Music — requires Music app running
osascript -l JavaScript music-agent/scripts/apple-music/now_playing.jxa
osascript -l JavaScript music-agent/scripts/apple-music/search_library.jxa "Autechre" artist
osascript -l JavaScript music-agent/scripts/apple-music/playback.jxa status

# MusicBrainz — requires network + musicbrainzngs
python3 music-agent/scripts/lookup/musicbrainz_lookup.py artist "Autechre"

# Knowledge graph
python3 music-agent/scripts/db/db.py stats
python3 music-agent/scripts/db/db.py search "Autechre"

# SessionStart hook output (what Claude sees on session init)
bash music-agent/scripts/session_context.sh
```

```bash
# Discogs — requires DISCOGS_TOKEN
python3 music-agent/scripts/lookup/discogs_lookup.py artist "Autechre"

# Graph engine
python3 music-agent/scripts/graph/engine.py stats
python3 music-agent/scripts/graph/engine.py centrality 5
python3 music-agent/scripts/graph/engine.py border auto

# Config
python3 music-agent/scripts/config.py show

# Tests
cd music-agent && python3 -m pytest tests/ -v
```

All scripts output JSON. Pipe through `jq` for readable output.
