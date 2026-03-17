# music-agent: Improvements & Roadmap

Based on the QA audit and research into available APIs, tools, and architectural options.

---

## 1. The `mk` CLI: MusicKit as the Foundation Layer

### Why

The single biggest limitation today is that **music-agent can only work with tracks already in the local library**. Every playlist, every queue, every recommendation — constrained to what the user already owns. A MusicKit-based Swift CLI (`mk`) would unlock the full Apple Music catalog (100M+ tracks) and solve the "Up Next" queue gap that JXA can't fill.

### What MusicKit Unlocks (vs JXA)

| Capability | JXA (current) | `mk` (MusicKit CLI) |
|---|---|---|
| Search local library | Yes | Yes |
| Search Apple Music catalog (100M+ tracks) | **No** | **Yes** |
| Play/pause/next/prev | Yes | Yes |
| Queue manipulation (Up Next) | **No** | **Yes** |
| Add catalog songs to library | **No** | **Yes** (via Apple Music API) |
| Create playlists with catalog songs | **No** | **Yes** (via Apple Music API) |
| Play history / recently played | **No** | **Yes** |
| `loved` property (reliable) | **Broken** | Likely reliable |
| BPM/key/tempo | No | No (Apple doesn't expose this) |
| Requires Apple Developer account | No | **Yes ($99/yr)** |

### Architecture Notes

- MusicKit requires `com.apple.application-identifier` entitlement → the CLI binary must be wrapped in an `.app` bundle (no window, runs headless). Apple documents this as the ["Signing a Daemon with a Restricted Entitlement"](https://developer.apple.com/documentation/xcode/signing-a-daemon-with-a-restricted-entitlement) pattern.
- Two auth layers: **Developer Token** (JWT, baked into the tool) + **Music User Token** (one-time user authorization prompt on first run).
- `ApplicationMusicPlayer.shared.queue` provides `insert(_:position:)` with `.afterCurrentEntry` (Play Next) and `.tail` (Play Last) — this is the queue API that JXA completely lacks.
- `MusicLibraryAddable` and `MusicLibrary.shared.createPlaylist()` are marked `@available(macOS, unavailable)` in MusicKit proper — but the **Apple Music REST API** handles both. The [MusadoraKit](https://github.com/rryam/MusadoraKit) package wraps this.
- No existing production-quality Swift MusicKit CLI exists — this would be novel.

### Suggested `mk` Command Surface

```
mk search "Autechre" [--type artist|album|song|playlist] [--catalog|--library]
mk play <id> [--next|--last]           # play now, or add to Up Next
mk queue list                           # show current Up Next
mk queue add <id> [--position next|last]
mk library add <catalog-id>            # add catalog track to library
mk playlist create <name> [--description]
mk playlist add <playlist-id> <track-id>
mk now                                  # current track (reliable loved, etc.)
mk recent                               # recently played
mk status                               # player state
```

### Migration Path

- `mk` replaces JXA scripts incrementally — not a rewrite, an augmentation
- Commands/agents update their script references from `osascript -l JavaScript` to `mk`
- JXA scripts remain as fallback for users without Apple Developer accounts
- The plugin detects `mk` availability and routes accordingly

### Open Question: Distribution

`mk` requires signing with a developer certificate. Options:
1. User builds from source with their own Apple Developer account
2. Pre-built binary distributed via Homebrew (requires notarization)
3. The plugin ships a setup script that guides the user through `mk` setup

---

## 2. API Augmentation: Beyond MusicBrainz

MusicBrainz is solid for structured metadata (MBIDs, credits, discographies) but weak on: popularity signals, community tags, similar-artist graphs, physical release data, and audio features. Here's what to add:

### Tier 1: High Value, Low Effort

#### Discogs API
- **What it adds:** Physical release details (pressings, editions, formats), marketplace pricing, label catalogs with catalog numbers, community ratings, detailed personnel credits (often richer than MusicBrainz), cover art
- **Why it matters for music-agent:** The crate-digger persona would benefit enormously — Discogs *is* the crate-digging database. Label exploration, pressing histories, and pricing data add a dimension MusicBrainz can't touch.
- **Auth:** Personal access token (free, instant) or OAuth 1.0a
- **Rate limits:** 60 req/min (authenticated). Generous.
- **Cost:** Free
- **Python client:** `python3-discogs-client` (mature)
- **Integration:** New script `scripts/lookup/discogs_lookup.py` with types: `artist`, `release`, `label`, `master`, `search`

#### Last.fm API
- **What it adds:** Similar artists (trained on billions of scrobbles — best-in-class), community tags (granular: "shoegaze", "melancholic", "driving music"), global play counts, listener counts
- **Why it matters for music-agent:** The anti-bubble persona needs "what's adjacent to what you like" — Last.fm's similar-artist graph is the best source for this. Community tags also provide mood/energy signals that Apple Music's genre field can't express.
- **Auth:** API key (free, instant)
- **Rate limits:** ~5 req/sec
- **Cost:** Free for non-commercial
- **Python client:** `pylast` (mature)
- **Integration:** New script `scripts/lookup/lastfm_lookup.py` with types: `similar-artists`, `artist-tags`, `track-tags`, `artist-info`

#### ListenBrainz API
- **What it adds:** Popularity/listener counts (open-source alternative to Last.fm), personalized recommendations, listening stats. Uses **MusicBrainz IDs** as primary keys — zero mapping needed.
- **Why it matters for music-agent:** Same ID system as our existing MusicBrainz integration. Popularity data helps the crate-digger persona gauge obscurity. Recommendation engine provides a "what to explore next" signal.
- **Auth:** User token (free, from profile page)
- **Rate limits:** Generous (indicated via headers)
- **Cost:** Completely free, open source (MetaBrainz Foundation)
- **Python client:** Official `pylistenbrainz`
- **Integration:** Extends existing `musicbrainz_lookup.py` or new `listenbrainz_lookup.py`

### Tier 2: Moderate Value, Low-Medium Effort

#### Genius API
- **What it adds:** Lyric annotations (crowdsourced explanations of meaning/context), artist bios, song metadata
- **Why it matters for music-agent:** The historian persona could use lyric annotations to add narrative context. Understanding what a song is *about* enriches the research.
- **Auth:** Client access token (free)
- **Rate limits:** ~5 req/sec
- **Caveat:** The API returns song URLs but not lyrics text directly. The `lyricsgenius` Python library handles the HTML scraping.
- **Integration:** New script `scripts/lookup/genius_lookup.py`

#### Setlist.fm API
- **What it adds:** Concert setlists (which songs played at which show), venue data, tour histories
- **Why it matters for music-agent:** "What does this artist play live?" and "Have they played in my city?" add a dimension no other source covers. The historian persona could use tour data to trace how scenes spread geographically.
- **Auth:** API key (free registration)
- **Cost:** Free for non-commercial
- **Integration:** New script `scripts/lookup/setlistfm_lookup.py`

### Tier 3: Specialized

#### Essentia (Local Audio Analysis)
- **What it adds:** BPM, key, scale, mood, genre classification, danceability — extracted from actual audio files
- **Why it matters for music-agent:** The harmonic-dj persona currently assigns energy levels (1-10) using LLM inference from genre/duration. Actual BPM and key data would make queue composition dramatically better. Essentia is the open-source tool that powered AcousticBrainz before it shut down.
- **Constraint:** Requires access to audio files (won't work with streaming-only Apple Music tracks). Only useful for tracks the user has downloaded locally.
- **Cost:** Free, open source (Music Technology Group, Barcelona)
- **Integration:** New script `scripts/analysis/audio_features.py`

#### AcousticBrainz (Archive)
- **What it adds:** Pre-computed audio features (BPM, key, mood) for tracks analyzed before 2022. Indexed by MusicBrainz Recording IDs.
- **Status:** Read-only archive. Data collection stopped in 2022. API still accessible.
- **Limitation:** No data for anything released after ~2022. Still useful for catalog tracks.

### Skip These

| Source | Why Skip |
|---|---|
| **Spotify Web API** | Locked down for new apps (Nov 2024). Audio features, related artists, and recommendations endpoints no longer available to new registrations. |
| **Bandcamp** | No usable public API. Official API is restricted to label partners for merch/sales only. |
| **Rate Your Music / Sonemic** | No API. Never offered one. Actively blocks scraping. |
| **Songkick** | Paid licensing only. Not available for hobbyist/educational use. |
| **AllMusic** | API discontinued years ago. Editorial content locked in platform. |

---

## 3. Fundamental Architecture Improvements

### 3a. Unified Lookup Layer

Currently `musicbrainz_lookup.py` is the only external lookup script. With Discogs, Last.fm, ListenBrainz, and potentially others, each as its own script, the commands and agents need to know which script to call for what.

**Proposal:** A single `lookup.py` dispatcher that routes queries to the appropriate source(s) and merges results:

```bash
python3 scripts/lookup/lookup.py artist "Autechre"
# → queries MusicBrainz + Discogs + Last.fm, returns unified JSON

python3 scripts/lookup/lookup.py similar "Autechre"
# → queries Last.fm similar artists, cross-references with MusicBrainz

python3 scripts/lookup/lookup.py release "Amber" --artist "Autechre"
# → queries MusicBrainz + Discogs, merges credits + pressing info
```

Benefits:
- Commands/agents call one script, not five
- Cross-referencing happens at the data layer (match MBIDs across sources)
- Rate limiting managed centrally
- Results cached in `lookup_cache` table with source attribution

### 3b. Library Export: Compact Mode

The `/taste` command exports 500 tracks (~200KB JSON) which consumes significant context window space. Two improvements:

1. **Compact mode** in `library_export.jxa`: export only analysis-relevant fields (name, artist, genre, year, playedCount, skippedCount, rating, duration, dateAdded). Drops albumArtist, sortArtist, sortAlbum, kind, size, bitRate, sampleRate, persistentID, comment, composer, grouping. Estimated savings: ~40% size reduction.

2. **Summary mode**: a new script (`library_summary.jxa` or a flag on `library_export.jxa`) that pre-aggregates data and returns distributions rather than raw tracks:

```json
{
  "total": 19897,
  "genres": {"Electronic": 4521, "Hip-Hop/Rap": 2103, ...},
  "decades": {"2020s": 5200, "2010s": 8100, ...},
  "topArtists": [{"name": "Autechre", "tracks": 243, "avgPlays": 4.2}, ...],
  "dormant": [{"name": "...", "artist": "...", "rating": 80, "lastPlayed": null}, ...],
  "recentlyAdded": [...],
  "highSkipRate": [...]
}
```

This would reduce the context footprint from ~200KB to ~5KB while providing the same analytical value.

### 3c. Persistent Taste Profile

The anti-bubble and harmonic-dj agents need to understand the user's library boundaries (what genres/regions/eras are present vs absent). Currently they re-analyze the library export each time.

**Proposal:** Build a persistent taste profile in the `taste_signals` table (already in the schema, currently unused):

```bash
python3 scripts/db/db.py build-taste-profile
# → runs library_export, computes distributions, stores in taste_signals table

python3 scripts/db/db.py get-taste-profile
# → returns the stored profile without re-analyzing
```

The profile auto-refreshes periodically (e.g., if older than 7 days) or on demand. Agents read the profile instead of the raw export.

### 3d. Recommendation Tracking

The anti-bubble persona says "User has encountered and skipped before: penalty (respect their no)" — but there's no mechanism to track what was recommended and whether the user acted on it.

**Proposal:** A `recommendations` table in the knowledge graph:

```sql
CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT,              -- what was recommended (artist/release MBID)
    persona TEXT,                -- which persona recommended it
    context TEXT,                -- what session/command triggered it
    status TEXT DEFAULT 'pending', -- pending, accepted, rejected, ignored
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);
```

When an agent recommends something, it logs it. When the user plays it, adds it to library, or explicitly dismisses it, the status updates. Over time, the agents learn what the user actually acts on.

### 3e. `mk` + JXA Fallback Architecture

With `mk` as an optional upgrade, the plugin needs a routing layer:

```bash
# scripts/apple-music/router.sh
# Detects mk availability, routes to mk or JXA

if command -v mk &> /dev/null; then
    mk "$@"
else
    # Map mk commands to JXA equivalents
    case "$1" in
        now)     osascript -l JavaScript "$PLUGIN_DIR/scripts/apple-music/now_playing.jxa" ;;
        search)  osascript -l JavaScript "$PLUGIN_DIR/scripts/apple-music/search_library.jxa" "${@:2}" ;;
        # ... etc
    esac
fi
```

Commands and agents call `router.sh` instead of specific scripts. Users with `mk` get catalog search, queue control, and reliable `loved`. Users without get the current JXA behavior.

---

## 4. Priority Order

### Phase 1: Quick Wins (days)
- [ ] Add Discogs lookup script (`discogs_lookup.py`)
- [ ] Add Last.fm lookup script (`lastfm_lookup.py`)
- [ ] Add library export compact/summary mode
- [ ] Build persistent taste profile (use existing `taste_signals` table)

### Phase 2: The `mk` CLI (weeks)
- [ ] Scaffold Swift package with MusicKit dependency
- [ ] Implement app-bundle wrapper for CLI distribution
- [ ] Core commands: `search --catalog`, `queue add`, `now`, `status`
- [ ] Library commands: `library add`, `playlist create/add`
- [ ] Router script for mk/JXA fallback
- [ ] Update all commands and agents to use router

### Phase 3: Intelligence Layer (weeks)
- [ ] Unified lookup dispatcher across MusicBrainz + Discogs + Last.fm
- [ ] ListenBrainz integration (popularity data, recommendations)
- [ ] Recommendation tracking table
- [ ] Genius integration for historian persona
- [ ] Setlist.fm integration

### Phase 4: Audio Analysis (stretch)
- [ ] Essentia integration for local audio feature extraction
- [ ] AcousticBrainz archive lookup for pre-2022 tracks
- [ ] BPM/key-aware queue composition for harmonic-dj
