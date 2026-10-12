# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

music-agent is a Claude Code plugin that turns the terminal into an agentic music companion for Apple Music. It connects Claude Code to the local Apple Music library via the `aux` CLI (a Swift bridge to MusicKit, REST API, and AppleScript), MusicBrainz and Discogs (via Python), and a local SQLite knowledge graph that accumulates entities, relations, and annotations over time.

This is a **plugin-only architecture** — no servers, no build step. The entire system is text files (markdown commands, personas, agents), shell/Python scripts, and a SQLite database at `~/.music-agent/knowledge.db`.

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
│   ├── apple-music-jxa-v0/         # Archived v0 JXA scripts (replaced by aux CLI)
│   ├── lookup/*.py                 # MusicBrainz + Discogs API wrappers
│   ├── db/db.py                    # Knowledge graph CRUD operations
│   ├── graph/engine.py             # NetworkX graph traversal engine
│   ├── config.py                   # Configuration management
│   └── session_context.sh          # SessionStart hook script (playback state + KB stats)
└── db/schema.sql                   # SQLite schema definition
```

## Key Scripts

### Apple Music (aux CLI)
The `aux` CLI (installed at `/usr/local/bin/aux`) bridges Apple Music via MusicKit, REST API, and AppleScript. All output is JSON wrapped in `{"data": ...}`. Always pass `--quiet` to suppress non-JSON output.

**Playback:**
- `aux playback now-playing --quiet` — current track (title, artist_name, album_title, database_id, state, position_seconds, duration_seconds, year, genre)
- `aux playback play|pause|stop|next|previous --quiet` — transport control
- `aux playback play --track-id <database_id> --quiet` — play specific track
- `aux playback play-next --track-id <database_id> --quiet` — queue as next
- `aux playback add-to-queue --track-id <database_id> --quiet` — append to queue
- `aux playback status --quiet` — player state (state, shuffle_mode, repeat_mode, volume)

**Library:**
- `aux library search "<query>" --quiet` — search local library
- `aux library songs --limit <n> [--artist "<x>"] --quiet` — list/filter library songs
- `aux library get-tags <database_id> --quiet` — track metadata (comment, rating, genre)
- `aux library set-tags <database_id> --fields "comment=text" --quiet` — write metadata
- `aux library batch-set-tags --track-ids <ids> --fields "comment=text" --quiet` — batch annotate
- `aux library get-play-stats <database_id> --quiet` — play count, skip count, rating
- `aux library create-playlist "<name>" --quiet` — create playlist (returns ID)
- `aux library add-to-playlist <playlist-id> --track-ids <ids> --quiet` — add tracks
- `aux library list-playlists --quiet` — list playlists

**Catalog & Discovery (new in v1):**
- `aux search songs|albums|artists "<query>" --quiet` — search full Apple Music catalog
- `aux catalog charts --types songs --quiet` — top charts
- `aux recommendations list --quiet` — personalized recommendations
- `aux recently-played tracks --quiet` — recently played
- `aux history heavy-rotation --quiet` — heavy rotation
- `aux library add --ids <catalog-id> --type songs --quiet` — add catalog items to library
- `aux ratings get|set --type songs <id> --quiet` — star ratings
- `aux favorites add --type songs <id> --quiet` — add to favorites

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

`release` and `credits` take a numeric Discogs ID plus an optional `master` argument. Discogs master and release IDs are separate namespaces: `artist-releases` items include a `type` field, and when it is `"master"` you must call `credits <id> master` (which resolves to the main release) — a bare master ID fetches an unrelated record.

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
Installs Python dependencies, initializes the SQLite DB, verifies `aux` CLI, and tests Apple Music + MusicBrainz connections.

**Requirements:** macOS, Apple Music app running, `aux` CLI (v1.1.0+), Python 3, `sqlite3`, `jq`.

## Architecture Notes

- **Personas are not tone wrappers** — they define distinct search strategies, scoring biases, and anti-patterns. Each persona in `personas/` has `<search_strategy>`, `<scoring_bias>`, and `<anti_patterns>` sections that change how results are selected and ranked.
- **Subagents** (`agents/`) are autonomous research delegates with constrained workflows. They read their corresponding persona file, conduct multi-step MusicBrainz lookups, cross-reference against the user's library, and store all discoveries in the knowledge graph.
- **Commands** (`commands/`) reference `aux` CLI commands for Apple Music access and `${CLAUDE_PLUGIN_ROOT}` for Python scripts.
- **The comment field** on Apple Music tracks is used as an in-library annotation layer (tags like `#deep-cut`, `#crate-dig-find`). Written via `aux library set-tags`.
- **All output is JSON** — aux wraps in `{"data": ...}` envelope, Python scripts output raw JSON. Commands and agents parse this output, never present raw JSON to users.
- **The SessionStart hook** runs `scripts/session_context.sh`, which calls `aux playback now-playing` and `db.py stats` to inject current playback state and knowledge graph stats into every new conversation.
- **Two ID systems**: `database_id` (integer, for playback/tags/stats) and MusicKit `id` (string, for library/catalog operations). `aux playback now-playing` returns `database_id`; `aux library search` returns MusicKit `id`.
- **The auto-trigger skill** (`skills/music-agent/SKILL.md`) activates on any music-related conversation, providing tool references and workflow patterns without requiring a slash command.

## Development Conventions

- Scripts in `scripts/` are the data access layer; commands/agents/personas are the prompt layer. Keep them separate.
- Entity IDs in the knowledge graph use MusicBrainz IDs (MBIDs) when available, generated IDs otherwise.
- Relations use `ON CONFLICT ... DO UPDATE` for idempotent upserts.
- The `lookup_cache` table prevents redundant MusicBrainz API calls.
- JSON metadata fields use SQLite's `json_patch()` for partial updates on entities.

## Testing Individual Scripts

```bash
# Apple Music via aux — requires Music app running + aux CLI
aux playback now-playing --quiet | jq
aux library search "Autechre" --quiet | jq
aux playback status --quiet | jq
aux library songs --limit 5 --quiet | jq

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

All output is JSON. Pipe through `jq` for readable output.
