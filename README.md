<div align="center">

# 🎧 music-agent

### your music library, but it talks back

**A Claude Code plugin that turns your terminal into a crate-digging, credit-chasing, playlist-composing music companion for Apple Music.**

![macOS](https://img.shields.io/badge/macOS-only-black?logo=apple)
![Apple Music](https://img.shields.io/badge/Apple%20Music-fa243c?logo=applemusic&logoColor=white)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-d97757)
![Python](https://img.shields.io/badge/python-3.7%2B-3776ab?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

</div>

---

Streaming algorithms want you to keep listening. **music-agent wants you to know what you're listening to.**

It hooks Claude Code up to your Apple Music library, MusicBrainz, Discogs, and a local knowledge graph that remembers everything it digs up. Ask who mastered that record. Get a 30-minute set that starts ambient and dissolves into noise. Find out what 2019-you was into that today-you forgot about. Ask for a curriculum, not a playlist.

No servers, no build step, no web UI. Just markdown, a few scripts, and a SQLite file that gets smarter every time you use it.

```
> /now
▶ "Multistability" — Mark Fell (2010, Raster-Noton)
  47 plays · added 2018-03-12 · ♥ loved
  Mark Fell is one half of SND, and his solo work on Raster-Noton ...
  → /who Mark Fell   → /dig Raster-Noton   → /queue "more like this, but stranger"
```

## ✨ What it does

| Command | Vibe |
|---|---|
| **`/now`** | What's playing, who made it, and what the knowledge graph already knows about it. |
| **`/dig <thing>`** | Research an artist, label, release, or idea using MusicBrainz, Discogs, and your library. |
| **`/queue <seed>`** | Build a queue from any seed (an artist, a mood, *"a rainy Tuesday in 1997 Bristol"*) and optionally save it as a playlist. |
| **`/who <artist>`** | Follow the credits. Producers, engineers, mastering folks, and everything else they touched. |
| **`/taste [focus]`** | Taste archaeology: patterns, blind spots, dormant favorites, and how your listening has drifted. |
| **`/kb`** | Poke the knowledge graph directly: stats, search, raw SQL, sessions, annotations. |

All of them are conversational. You can skip the slash commands and just talk about music; the auto-trigger skill kicks in either way.

## 🎭 Personas (they're strategies, not costumes)

Add `--persona <name>` to `/dig`, `/queue`, or `/now`. Each persona has its own **search strategy, scoring bias, and anti-patterns**, so it changes *what* gets found as well as how it's described.

| Persona | Energy | How it searches |
|---|---|---|
| 🪩 **crate-digger** | "You've never heard of it. That's the point." | Follows credits and label rosters, ranks tracks *inversely* to popularity, lives for B-sides. |
| 📜 **historian** | "To understand this, we have to go back to 1958." | Builds timelines, traces influence chains, maps scenes and movements. |
| 🎚️ **harmonic-dj** | "That transition would be a crime." | Thinks in energy arcs, tempo, density, and flow. Every track has to earn its slot. |
| 🫧 **anti-bubble** | "Your library has a geography problem." | Finds gaps in genre, region, and era and pushes you across them on purpose. |

Each persona also runs as an autonomous **subagent** that does multi-step research, checks the results against your library, and saves what it finds to the graph.

## 🧠 The knowledge graph

Every session feeds a local SQLite graph at `~/.music-agent/knowledge.db`:

- **Entities**: artists, labels, releases, tracks, engineers
- **Relations**: `released_on`, `mastered_by`, `member_of`, `influenced_by`, `similar_to`, …
- **Annotations**: persona-attributed notes and tags
- **Sessions**: listening logs, skips included

On top of the graph sits a small **networkx engine** for Lenses-style exploration: **Drift** (random walks), **Six Degrees** (shortest paths between any two nodes), and **Expedition** (the edge of what you know).

**Bonus:** agent tags like `#deep-cut` and `#crate-dig-find` get written into the Apple Music **comment field**, so the annotations live in your library too.

## 🚀 Getting started

### You'll need

- **macOS** with the **Music** app open
- **[`aux`](https://github.com/discohead/aux)** v1.1.0+, the Swift CLI that bridges MusicKit, the Apple Music REST API, and AppleScript into tidy JSON
- **Python 3.7+**, **`sqlite3`**, and **`jq`** (`brew install jq`)
- **[Claude Code](https://claude.com/claude-code)**
- *Optional:* a [Discogs personal access token](https://www.discogs.com/settings/developers) for the deep credits

### Install

```bash
git clone https://github.com/discohead/music-agent.git
cd music-agent

# one-time setup: Python deps, knowledge graph, connectivity checks
bash music-agent/scripts/setup.sh

# launch Claude Code with the plugin loaded
claude --plugin-dir ./music-agent
```

Prefer a permanent install? Add the plugin directory as a local marketplace from inside Claude Code:

```
/plugin marketplace add /path/to/music-agent/music-agent
/plugin install music-agent@music-agent-dev
```

### Discogs (optional, recommended)

```bash
export DISCOGS_TOKEN=your_token_here
# or persist it:
python3 music-agent/scripts/config.py set discogs_token your_token_here
```

### Smoke test

Start a new session. You should see something like:

```
music-agent active. Now playing: … Knowledge graph: 43 entities, 29 relations.
```

Then press play on something and type `/now`.

## 🎛️ Try these

```
/dig Mark Fell --persona crate-digger
/queue "start ambient, build tension for 30 minutes, then dissolve" --count 15 --save "Tuesday Night"
/who "Rashad Becker"
/taste genres
/kb search Raster-Noton
```

Or just ask:

> *"What's the through-line from musique concrète to modern microsound?"*
> *"Find me the shortest path from Aphex Twin to Alice Coltrane."*
> *"What was I obsessed with in 2019 that I haven't played since?"*

## 🏗️ How it's built

The whole system is text files plus a few scripts. The **prompt layer** (commands, agents, personas, skill) sits on a **data layer** (`aux` plus Python scripts), and everything talks JSON.

```
music-agent/
├── commands/        /now /dig /queue /who /taste /kb
├── agents/          crate-digger · historian · harmonic-dj · anti-bubble
├── personas/        search strategies, scoring biases, anti-patterns
├── skills/          auto-trigger skill for music-y conversations
├── hooks/           SessionStart → now-playing + graph stats
├── scripts/
│   ├── lookup/      MusicBrainz + Discogs wrappers
│   ├── db/          knowledge graph CRUD
│   ├── graph/       networkx traversal engine
│   ├── config.py    tokens & settings (~/.music-agent/config.json)
│   └── setup.sh
├── db/              SQLite schema + migrations
└── tests/           pytest suite
```

| Source | Via | Gives you |
|---|---|---|
| Apple Music | `aux` CLI | Library, playback, queue, playlists, play stats, ratings, catalog search, charts, recommendations |
| MusicBrainz | `musicbrainzngs` | Artists, discographies, release credits, labels (rate-limited to 1 req/sec) |
| Discogs | `python3-discogs-client` | Deep personnel credits, label catalogs, masters and releases |
| Knowledge graph | SQLite + networkx | Everything above, remembered and connected |

## 🧪 Development

```bash
cd music-agent && python3 -m pytest tests/ -v

# poke individual pieces (all output is JSON, so pipe it to jq)
aux playback now-playing --quiet | jq
python3 music-agent/scripts/lookup/musicbrainz_lookup.py artist "Autechre" | jq
python3 music-agent/scripts/graph/engine.py centrality 5 | jq
bash music-agent/scripts/session_context.sh
```

See [`CLAUDE.md`](CLAUDE.md) for the full script reference and [`music-agent-vision.md`](music-agent-vision.md) for the design rationale.

## 🩹 Troubleshooting

| Symptom | Fix |
|---|---|
| Commands don't show up | Restart Claude Code, then check `/plugin list` |
| "Nothing playing" forever | Open Music.app, press play, and run `aux playback now-playing --quiet` |
| MusicBrainz errors | Check your network. The 1 req/sec rate limit is enforced, so be patient |
| Discogs lookups skipped | Set `DISCOGS_TOKEN` (see above) |
| Graph looks broken | `python3 music-agent/scripts/db/db.py init` |

## 💿 Credits

Built on [**aux**](https://github.com/discohead/aux), [MusicBrainz](https://musicbrainz.org), [Discogs](https://www.discogs.com), [networkx](https://networkx.org), and a lot of late-night listening.

MIT licensed. See [LICENSE](music-agent/LICENSE).

<div align="center"><sub>made for people who read liner notes 📀</sub></div>
