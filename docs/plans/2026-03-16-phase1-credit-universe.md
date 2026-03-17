# Phase 1: Credit Universe + Graph Engine

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enrich the knowledge graph with Discogs credit data and build a networkx-based graph engine exposing traversal primitives (shortest path, random walk, border nodes, clustering, centrality) that power all future Lenses.

**Architecture:** Three new Python scripts following existing patterns (CLI interface, JSON output, same `if __name__ == "__main__"` dispatch pattern as `db.py` and `musicbrainz_lookup.py`). Schema migration adds Discogs ID tracking. Entity resolution merges cross-source identities. Graph engine loads KB into networkx for traversal. No servers, no build steps.

**Tech Stack:** `python3-discogs-client`, `networkx`, SQLite, existing `db.py` patterns.

**Prerequisites:** Discogs user token (free at discogs.com/settings/developers). Will be read from `DISCOGS_TOKEN` env var or `~/.music-agent/config.json`.

---

## Task 1: Test Infrastructure

No tests exist yet. Set up pytest with a fixture that creates an in-memory KB.

**Files:**
- Create: `music-agent/tests/conftest.py`
- Create: `music-agent/tests/__init__.py`
- Create: `music-agent/tests/test_smoke.py`

**Step 1: Create test directory and conftest**

```python
# tests/__init__.py
# (empty)
```

```python
# tests/conftest.py
import pytest
import sqlite3
import json
import sys
from pathlib import Path

# Add scripts to path so we can import them
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR / "db"))
sys.path.insert(0, str(SCRIPTS_DIR / "lookup"))
sys.path.insert(0, str(SCRIPTS_DIR / "graph"))


@pytest.fixture
def db_path(tmp_path):
    """Return a temp DB path for testing."""
    return tmp_path / "test_knowledge.db"


@pytest.fixture
def db_conn(db_path):
    """Create an initialized test database, return connection."""
    schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    with open(schema_path) as f:
        conn.executescript(f.read())
    yield conn
    conn.close()


@pytest.fixture
def populated_db(db_conn):
    """DB with sample entities and relations for graph tests."""
    entities = [
        ("mbid-artist-1", "artist", "Autechre", '{"country":"UK"}', '["musicbrainz"]', None),
        ("mbid-artist-2", "artist", "Boards of Canada", '{"country":"UK"}', '["musicbrainz"]', None),
        ("mbid-engineer-1", "engineer", "Rashad Becker", '{}', '["musicbrainz"]', None),
        ("mbid-label-1", "label", "Warp Records", '{"country":"UK"}', '["musicbrainz"]', None),
        ("mbid-label-2", "label", "Skam Records", '{"country":"UK"}', '["musicbrainz"]', None),
        ("mbid-release-1", "release", "Tri Repetae", '{"year":"1995"}', '["musicbrainz"]', "apple-id-1"),
        ("mbid-release-2", "release", "Music Has the Right to Children", '{"year":"1998"}', '["musicbrainz"]', None),
        ("mbid-release-3", "release", "Confield", '{"year":"2001"}', '["musicbrainz"]', "apple-id-2"),
        ("mbid-artist-3", "artist", "Mark Fell", '{}', '["musicbrainz"]', None),
        ("mbid-release-4", "release", "Multistability", '{"year":"2010"}', '["musicbrainz"]', None),
    ]
    for e in entities:
        db_conn.execute(
            "INSERT INTO entities (id, type, name, metadata, sources, apple_music_id) VALUES (?,?,?,?,?,?)", e
        )

    relations = [
        ("mbid-artist-1", "mbid-release-1", "performed", 1.0),
        ("mbid-artist-1", "mbid-release-3", "performed", 1.0),
        ("mbid-artist-2", "mbid-release-2", "performed", 1.0),
        ("mbid-release-1", "mbid-label-1", "released_on", 1.0),
        ("mbid-release-2", "mbid-label-1", "released_on", 1.0),
        ("mbid-release-3", "mbid-label-1", "released_on", 1.0),
        ("mbid-release-4", "mbid-label-2", "released_on", 1.0),
        ("mbid-engineer-1", "mbid-release-1", "mastered", 1.0),
        ("mbid-engineer-1", "mbid-release-2", "mastered", 1.0),
        ("mbid-engineer-1", "mbid-release-4", "mastered", 1.0),
        ("mbid-artist-3", "mbid-release-4", "performed", 1.0),
        ("mbid-artist-1", "mbid-label-1", "signed_to", 1.0),
        ("mbid-artist-2", "mbid-label-1", "signed_to", 1.0),
    ]
    for r in relations:
        db_conn.execute(
            "INSERT INTO relations (source_id, target_id, relation, confidence) VALUES (?,?,?,?)", r
        )

    db_conn.commit()
    return db_conn
```

**Step 2: Write smoke test**

```python
# tests/test_smoke.py
def test_db_fixture_works(db_conn):
    row = db_conn.execute("SELECT COUNT(*) as c FROM entities").fetchone()
    assert row["c"] == 0


def test_populated_db_has_data(populated_db):
    row = populated_db.execute("SELECT COUNT(*) as c FROM entities").fetchone()
    assert row["c"] == 10
    row = populated_db.execute("SELECT COUNT(*) as c FROM relations").fetchone()
    assert row["c"] == 13
```

**Step 3: Run tests**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/ -v
```

Expected: 2 tests PASS.

**Step 4: Commit**

```bash
git add tests/
git commit -m "test: add pytest infrastructure with KB fixtures"
```

---

## Task 2: Schema Migration for Discogs

Add `discogs_id` column to entities and new relation types for richer credit data.

**Files:**
- Modify: `music-agent/db/schema.sql`
- Create: `music-agent/db/migration_001_discogs.sql`
- Modify: `music-agent/scripts/db/db.py` (add `migrate` command)
- Create: `music-agent/tests/test_schema.py`

**Step 1: Write failing test**

```python
# tests/test_schema.py
def test_entities_has_discogs_id(db_conn):
    """Schema should have discogs_id column on entities."""
    cols = [row[1] for row in db_conn.execute("PRAGMA table_info(entities)").fetchall()]
    assert "discogs_id" in cols


def test_discogs_id_indexed(db_conn):
    """discogs_id should be indexed for fast lookups."""
    indexes = [row[1] for row in db_conn.execute("PRAGMA index_list(entities)").fetchall()]
    assert any("discogs" in idx for idx in indexes)
```

**Step 2: Run tests to verify failure**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_schema.py -v
```

Expected: FAIL — `discogs_id` not in columns.

**Step 3: Update schema.sql**

In `schema.sql`, add `discogs_id` column to entities table (after `apple_music_id`):

```sql
-- Add after apple_music_id line:
    discogs_id TEXT,                  -- Discogs artist/release/label ID
```

Add index after the existing apple_music_id index:

```sql
CREATE INDEX IF NOT EXISTS idx_entities_discogs ON entities(discogs_id);
```

**Step 4: Create migration script for existing databases**

```sql
-- db/migration_001_discogs.sql
-- Add Discogs ID tracking to entities
ALTER TABLE entities ADD COLUMN discogs_id TEXT;
CREATE INDEX IF NOT EXISTS idx_entities_discogs ON entities(discogs_id);
```

**Step 5: Add `migrate` command to db.py**

Add to `db.py` — a `migrate` function that applies migrations idempotently, and register it in the dispatch table:

```python
def migrate():
    """Apply any pending migrations."""
    conn = get_db()
    migrations_dir = SCHEMA_PATH.parent
    applied = []

    # Check if discogs_id column exists
    cols = [row[1] for row in conn.execute("PRAGMA table_info(entities)").fetchall()]
    if "discogs_id" not in cols:
        migration_path = migrations_dir / "migration_001_discogs.sql"
        if migration_path.exists():
            with open(migration_path) as f:
                conn.executescript(f.read())
            applied.append("001_discogs")

    conn.close()
    return {"applied": applied, "status": "up to date" if not applied else "migrations applied"}
```

Add to dispatch:
```python
"migrate": lambda: migrate(),
```

**Step 6: Run tests**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_schema.py -v
```

Expected: PASS.

**Step 7: Commit**

```bash
git add db/ scripts/db/db.py tests/test_schema.py
git commit -m "feat: add discogs_id to entities schema with migration support"
```

---

## Task 3: Discogs Lookup Script

New script following the exact pattern of `musicbrainz_lookup.py`: CLI dispatch, JSON output, functions for each lookup type.

**Files:**
- Create: `music-agent/scripts/lookup/discogs_lookup.py`
- Create: `music-agent/tests/test_discogs_lookup.py`

**Step 1: Write failing tests (mocked — no real API calls in tests)**

```python
# tests/test_discogs_lookup.py
"""Tests for discogs_lookup.py using mocked Discogs client."""
import json
import pytest
from unittest.mock import MagicMock, patch


def test_search_artist_returns_structured_json():
    """search_artist should return {query, count, artists: [...]}"""
    # We test the output structure, not the API call
    sys_path_hack()
    from discogs_lookup import format_artist

    mock_artist = MagicMock()
    mock_artist.id = 27
    mock_artist.name = "Autechre"
    mock_artist.real_name = ""
    mock_artist.profile = "Electronic duo"
    mock_artist.data = {"uri": "https://discogs.com/artist/27"}

    result = format_artist(mock_artist)
    assert result["id"] == 27
    assert result["name"] == "Autechre"
    assert "profile" in result


def test_format_release_credits():
    """format_release_credits should extract credits with roles."""
    sys_path_hack()
    from discogs_lookup import format_release_credits

    mock_credit = MagicMock()
    mock_credit.id = 100
    mock_credit.name = "Rashad Becker"
    mock_credit.role = "Mastered By"

    mock_release = MagicMock()
    mock_release.id = 999
    mock_release.title = "Tri Repetae"
    mock_release.year = 1995
    mock_release.artists = []
    mock_release.credits = [mock_credit]
    mock_release.labels = []
    mock_release.tracklist = []
    mock_release.genres = ["Electronic"]
    mock_release.styles = ["IDM", "Ambient"]
    mock_release.country = "UK"

    result = format_release_credits(mock_release)
    assert result["title"] == "Tri Repetae"
    assert len(result["credits"]) == 1
    assert result["credits"][0]["role"] == "Mastered By"
    assert result["credits"][0]["name"] == "Rashad Becker"


def test_format_label_info():
    """format_label_info should include sublabels and parent."""
    sys_path_hack()
    from discogs_lookup import format_label_info

    mock_sublabel = MagicMock()
    mock_sublabel.id = 200
    mock_sublabel.name = "Warp Classics"

    mock_label = MagicMock()
    mock_label.id = 100
    mock_label.name = "Warp Records"
    mock_label.profile = "UK label"
    mock_label.sublabels = [mock_sublabel]
    mock_label.parent_label = None
    mock_label.data = {"uri": ""}

    result = format_label_info(mock_label)
    assert result["name"] == "Warp Records"
    assert len(result["sublabels"]) == 1
    assert result["sublabels"][0]["name"] == "Warp Classics"
    assert result["parent"] is None


def sys_path_hack():
    import sys
    from pathlib import Path
    scripts_dir = str(Path(__file__).parent.parent / "scripts" / "lookup")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
```

**Step 2: Run tests to verify failure**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_discogs_lookup.py -v
```

Expected: FAIL — `discogs_lookup` module not found.

**Step 3: Implement discogs_lookup.py**

```python
#!/usr/bin/env python3
"""
discogs_lookup.py - Query Discogs for credits, label rosters, and release data.

Usage:
    python3 scripts/lookup/discogs_lookup.py artist "Autechre"
    python3 scripts/lookup/discogs_lookup.py release <discogs-release-id>
    python3 scripts/lookup/discogs_lookup.py credits <discogs-release-id>
    python3 scripts/lookup/discogs_lookup.py label <discogs-label-id>
    python3 scripts/lookup/discogs_lookup.py label-releases <discogs-label-id> [page]
    python3 scripts/lookup/discogs_lookup.py artist-releases <discogs-artist-id> [page]

Requires: pip install python3-discogs-client
Auth: Set DISCOGS_TOKEN env var or add to ~/.music-agent/config.json
"""

import sys
import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".music-agent" / "config.json"


def get_token():
    """Get Discogs user token from env var or config file."""
    token = os.environ.get("DISCOGS_TOKEN")
    if token:
        return token
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = json.load(f)
            return config.get("discogs_token")
    return None


def get_client():
    """Initialize Discogs client with auth."""
    try:
        import discogs_client
    except ImportError:
        print(json.dumps({"error": "python3-discogs-client not installed. Run: pip3 install python3-discogs-client"}))
        sys.exit(1)

    token = get_token()
    if not token:
        print(json.dumps({
            "error": "No Discogs token. Set DISCOGS_TOKEN env var or add discogs_token to ~/.music-agent/config.json",
            "help": "Get a token at: https://www.discogs.com/settings/developers"
        }))
        sys.exit(1)

    client = discogs_client.Client("MusicAgent/1.0", user_token=token)
    return client


# --- Formatting functions (tested independently of API) ---

def format_artist(artist):
    """Format a Discogs artist object to our standard JSON."""
    members = []
    try:
        for m in (artist.members or []):
            members.append({"id": m.id, "name": m.name})
    except Exception:
        pass

    aliases = []
    try:
        for a in (artist.aliases or []):
            aliases.append({"id": a.id, "name": a.name})
    except Exception:
        pass

    groups = []
    try:
        for g in (artist.groups or []):
            groups.append({"id": g.id, "name": g.name})
    except Exception:
        pass

    return {
        "id": artist.id,
        "name": artist.name,
        "realName": getattr(artist, "real_name", None),
        "profile": getattr(artist, "profile", ""),
        "members": members,
        "aliases": aliases,
        "groups": groups,
        "source": "discogs",
    }


def format_release_credits(release):
    """Format a Discogs release with full credits."""
    artists = []
    try:
        for a in release.artists:
            artists.append({"id": a.id, "name": a.name})
    except Exception:
        pass

    credits = []
    try:
        for c in release.credits:
            credits.append({
                "id": c.id,
                "name": c.name,
                "role": c.role,
            })
    except Exception:
        pass

    labels = []
    try:
        for l in release.labels:
            labels.append({"id": l.id, "name": l.name, "catno": getattr(l, "catno", "")})
    except Exception:
        pass

    tracklist = []
    try:
        for t in release.tracklist:
            track_credits = []
            if hasattr(t, "credits") and t.credits:
                for c in t.credits:
                    track_credits.append({"id": c.id, "name": c.name, "role": c.role})
            tracklist.append({
                "position": t.position,
                "title": t.title,
                "duration": t.duration,
                "credits": track_credits,
            })
    except Exception:
        pass

    return {
        "id": release.id,
        "title": release.title,
        "year": getattr(release, "year", None),
        "country": getattr(release, "country", None),
        "genres": getattr(release, "genres", []),
        "styles": getattr(release, "styles", []),
        "artists": artists,
        "credits": credits,
        "labels": labels,
        "tracklist": tracklist,
        "source": "discogs",
    }


def format_label_info(label):
    """Format a Discogs label with sublabel hierarchy."""
    sublabels = []
    try:
        for s in (label.sublabels or []):
            sublabels.append({"id": s.id, "name": s.name})
    except Exception:
        pass

    return {
        "id": label.id,
        "name": label.name,
        "profile": getattr(label, "profile", ""),
        "parent": label.parent_label.name if getattr(label, "parent_label", None) else None,
        "parentId": label.parent_label.id if getattr(label, "parent_label", None) else None,
        "sublabels": sublabels,
        "source": "discogs",
    }


# --- API functions ---

def search_artist(query, limit=10):
    client = get_client()
    results = client.search(query, type="artist")
    artists = []
    for r in results.page(1)[:limit]:
        try:
            artist = client.artist(r.id)
            artists.append(format_artist(artist))
        except Exception:
            artists.append({"id": r.id, "name": getattr(r, "title", str(r)), "source": "discogs"})
    return {"query": query, "count": len(artists), "artists": artists}


def get_release_credits(release_id):
    client = get_client()
    release = client.release(int(release_id))
    return format_release_credits(release)


def get_label_info(label_id):
    client = get_client()
    label = client.label(int(label_id))
    return format_label_info(label)


def get_label_releases(label_id, page=1):
    client = get_client()
    label = client.label(int(label_id))
    releases = label.releases.page(int(page))
    items = []
    for r in releases:
        items.append({
            "id": r.id,
            "title": getattr(r, "title", ""),
            "year": getattr(r, "year", None),
            "artist": getattr(r, "artist", ""),
            "catno": getattr(r, "catno", ""),
        })
    return {
        "labelId": int(label_id),
        "labelName": label.name,
        "page": int(page),
        "totalPages": label.releases.pages,
        "totalReleases": label.releases.count,
        "releases": items,
    }


def get_artist_releases(artist_id, page=1):
    client = get_client()
    artist = client.artist(int(artist_id))
    releases = artist.releases.page(int(page))
    items = []
    for r in releases:
        items.append({
            "id": r.id,
            "title": getattr(r, "title", ""),
            "year": getattr(r, "year", None),
            "role": getattr(r, "role", ""),
        })
    return {
        "artistId": int(artist_id),
        "artistName": artist.name,
        "page": int(page),
        "totalPages": artist.releases.pages,
        "totalReleases": artist.releases.count,
        "releases": items,
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: discogs_lookup.py <type> <query|id> [page]"}))
        sys.exit(1)

    lookup_type = sys.argv[1]
    query = sys.argv[2]
    page = sys.argv[3] if len(sys.argv) > 3 else 1

    dispatch = {
        "artist": lambda: search_artist(query),
        "release": lambda: get_release_credits(query),
        "credits": lambda: get_release_credits(query),
        "label": lambda: get_label_info(query),
        "label-releases": lambda: get_label_releases(query, page),
        "artist-releases": lambda: get_artist_releases(query, page),
    }

    fn = dispatch.get(lookup_type)
    if not fn:
        print(json.dumps({"error": f"Unknown type: {lookup_type}. Use: artist, release, credits, label, label-releases, artist-releases"}))
        sys.exit(1)

    try:
        result = fn()
    except Exception as e:
        result = {"error": str(e)}
    print(json.dumps(result, indent=2, default=str))
```

**Step 4: Run tests**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_discogs_lookup.py -v
```

Expected: 3 tests PASS.

**Step 5: Commit**

```bash
git add scripts/lookup/discogs_lookup.py tests/test_discogs_lookup.py
git commit -m "feat: add Discogs lookup script with credit, label, and artist queries"
```

---

## Task 4: Entity Resolution

Add a `resolve` command to `db.py` that links entities across sources (MusicBrainz + Discogs + Apple Music). When we discover that Discogs artist #27 = MusicBrainz artist mbid-xyz = Apple Music library artist "Autechre", we merge them into a single entity with multiple source IDs.

**Files:**
- Modify: `music-agent/scripts/db/db.py`
- Create: `music-agent/tests/test_entity_resolution.py`

**Step 1: Write failing tests**

```python
# tests/test_entity_resolution.py
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "db"))


def test_link_discogs_id(db_conn):
    """link-discogs should add discogs_id to an existing entity."""
    from db import link_discogs, get_db
    # Patch get_db to use test connection
    import db as db_module
    original_get_db = db_module.get_db
    db_module.get_db = lambda: db_conn

    # Insert an entity first
    db_conn.execute(
        "INSERT INTO entities (id, type, name, metadata, sources) VALUES (?, ?, ?, ?, ?)",
        ("mbid-123", "artist", "Autechre", "{}", '["musicbrainz"]')
    )
    db_conn.commit()

    result = link_discogs("mbid-123", "27")
    assert result["linked"] == "mbid-123"
    assert result["discogs_id"] == "27"

    # Verify it was stored
    row = db_conn.execute("SELECT discogs_id, sources FROM entities WHERE id = ?", ("mbid-123",)).fetchone()
    assert row["discogs_id"] == "27"
    sources = json.loads(row["sources"])
    assert "discogs" in sources

    db_module.get_db = original_get_db


def test_find_entity_by_discogs_id(db_conn):
    """Should find entity by discogs_id."""
    from db import find_by_discogs_id
    import db as db_module
    original_get_db = db_module.get_db
    db_module.get_db = lambda: db_conn

    db_conn.execute(
        "INSERT INTO entities (id, type, name, metadata, sources, discogs_id) VALUES (?, ?, ?, ?, ?, ?)",
        ("mbid-123", "artist", "Autechre", "{}", '["musicbrainz","discogs"]', "27")
    )
    db_conn.commit()

    result = find_by_discogs_id("27")
    assert result is not None
    assert result["id"] == "mbid-123"

    result = find_by_discogs_id("9999")
    assert result is None

    db_module.get_db = original_get_db
```

**Step 2: Run to verify failure**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_entity_resolution.py -v
```

Expected: FAIL — `link_discogs` not found.

**Step 3: Implement entity resolution functions in db.py**

Add these functions to `db.py`:

```python
def link_discogs(entity_id, discogs_id):
    """Link a Discogs ID to an existing entity."""
    conn = get_db()
    # Update discogs_id
    conn.execute("UPDATE entities SET discogs_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                 (discogs_id, entity_id))
    # Add 'discogs' to sources array if not present
    row = conn.execute("SELECT sources FROM entities WHERE id = ?", (entity_id,)).fetchone()
    if row:
        sources = json.loads(row["sources"] or "[]")
        if "discogs" not in sources:
            sources.append("discogs")
            conn.execute("UPDATE entities SET sources = ? WHERE id = ?",
                         (json.dumps(sources), entity_id))
    conn.commit()
    conn.close()
    return {"linked": entity_id, "discogs_id": discogs_id}


def find_by_discogs_id(discogs_id):
    """Find an entity by its Discogs ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM entities WHERE discogs_id = ?", (discogs_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None
```

Add to dispatch:
```python
"link-discogs": lambda: link_discogs(sys.argv[2], sys.argv[3]),
"find-discogs": lambda: find_by_discogs_id(sys.argv[2]) or {"found": False},
```

**Step 4: Run tests**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_entity_resolution.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/db/db.py tests/test_entity_resolution.py
git commit -m "feat: add entity resolution for linking Discogs IDs to KB entities"
```

---

## Task 5: Graph Engine

The heart of the Lenses framework. A Python script that loads the KB into a `networkx` graph and exposes traversal primitives.

**Files:**
- Create: `music-agent/scripts/graph/__init__.py`
- Create: `music-agent/scripts/graph/engine.py`
- Create: `music-agent/tests/test_graph_engine.py`

**Step 1: Write failing tests**

```python
# tests/test_graph_engine.py
"""Tests for the graph engine traversal primitives."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "graph"))


def test_load_graph(populated_db):
    """Engine should load entities and relations into a networkx graph."""
    from engine import load_graph
    G = load_graph(populated_db)
    assert G.number_of_nodes() == 10
    assert G.number_of_edges() == 13


def test_shortest_path(populated_db):
    """Find shortest credit path between two artists."""
    from engine import load_graph, shortest_path
    G = load_graph(populated_db)
    # Autechre → Tri Repetae → (mastered) ← Rashad Becker → (mastered) → Multistability → Mark Fell
    path = shortest_path(G, "mbid-artist-1", "mbid-artist-3")
    assert path is not None
    assert path[0] == "mbid-artist-1"
    assert path[-1] == "mbid-artist-3"
    assert len(path) >= 3  # at least through one intermediate


def test_shortest_path_no_connection(populated_db):
    """Should return None when no path exists."""
    from engine import load_graph, shortest_path
    G = load_graph(populated_db)
    # Add an isolated node
    G.add_node("island", type="artist", name="Isolated Artist")
    path = shortest_path(G, "mbid-artist-1", "island")
    assert path is None


def test_ego_graph(populated_db):
    """Get N-hop neighborhood around an entity."""
    from engine import load_graph, ego_graph
    G = load_graph(populated_db)
    subgraph = ego_graph(G, "mbid-engineer-1", depth=1)
    # Rashad Becker connects to 3 releases directly
    assert "mbid-engineer-1" in subgraph.nodes
    assert subgraph.number_of_nodes() >= 4  # Rashad + 3 releases


def test_border_nodes(populated_db):
    """Find entities connected to collection but not in it."""
    from engine import load_graph, border_nodes
    G = load_graph(populated_db)
    # apple-id-1 = Tri Repetae, apple-id-2 = Confield → both are in "collection"
    # Entities connected to collection entities but without apple_music_id = border
    collection_ids = {"mbid-release-1", "mbid-release-3"}  # releases with apple_music_id
    borders = border_nodes(G, collection_ids)
    # Should include things connected to Tri Repetae and Confield but not in collection
    assert len(borders) > 0
    # None of the border nodes should be in the collection
    for node_id, _ in borders:
        assert node_id not in collection_ids


def test_random_walk(populated_db):
    """Random walk should return a path of requested length."""
    from engine import load_graph, random_walk
    G = load_graph(populated_db)
    walk = random_walk(G, "mbid-artist-1", steps=4)
    assert walk[0] == "mbid-artist-1"
    assert len(walk) <= 5  # start + up to 4 steps
    # Each step should be connected to the previous
    for i in range(1, len(walk)):
        assert G.has_edge(walk[i - 1], walk[i]) or G.has_edge(walk[i], walk[i - 1])


def test_centrality(populated_db):
    """Most-connected nodes should have highest centrality."""
    from engine import load_graph, centrality
    G = load_graph(populated_db)
    scores = centrality(G)
    # Warp Records (mbid-label-1) has 5 connections → should be among top
    top_ids = [node_id for node_id, _ in sorted(scores.items(), key=lambda x: -x[1])[:3]]
    assert "mbid-label-1" in top_ids


def test_clusters(populated_db):
    """Should detect communities in the graph."""
    from engine import load_graph, clusters
    G = load_graph(populated_db)
    communities = clusters(G)
    assert len(communities) >= 1
    # All nodes should be in some community
    all_nodes = set()
    for c in communities:
        all_nodes.update(c)
    assert all_nodes == set(G.nodes)


def test_path_detail(populated_db):
    """Path detail should include entity names and relation types."""
    from engine import load_graph, path_detail
    G = load_graph(populated_db)
    path = ["mbid-artist-1", "mbid-release-1", "mbid-engineer-1"]
    detail = path_detail(G, path)
    assert len(detail) == 3
    assert detail[0]["name"] == "Autechre"
    assert detail[0]["type"] == "artist"
    # Each step (except first) should have edge_from info
    assert "edge_relation" in detail[1]
```

**Step 2: Run to verify failure**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_graph_engine.py -v
```

Expected: FAIL — engine module not found.

**Step 3: Implement engine.py**

```python
#!/usr/bin/env python3
"""
engine.py - Graph traversal engine for the music-agent knowledge graph.

Loads entities and relations from SQLite into a networkx graph,
then exposes traversal primitives that power all Lenses.

Usage:
    python3 scripts/graph/engine.py shortest-path <entity-a> <entity-b>
    python3 scripts/graph/engine.py ego <entity-id> [depth]
    python3 scripts/graph/engine.py border <comma-separated-collection-ids>
    python3 scripts/graph/engine.py walk <start-id> [steps]
    python3 scripts/graph/engine.py centrality [top-n]
    python3 scripts/graph/engine.py clusters
    python3 scripts/graph/engine.py stats

DB location: ~/.music-agent/knowledge.db
Requires: pip install networkx
"""

import sys
import json
import sqlite3
import random
from pathlib import Path

try:
    import networkx as nx
except ImportError:
    print(json.dumps({"error": "networkx not installed. Run: pip3 install networkx"}))
    sys.exit(1)

DB_PATH = Path.home() / ".music-agent" / "knowledge.db"


def load_graph(conn=None):
    """Load the knowledge graph from SQLite into a networkx Graph.

    Args:
        conn: Optional sqlite3 connection (for testing). If None, connects to default DB.

    Returns:
        networkx.Graph with entity attributes on nodes and relation attributes on edges.
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        close_conn = True

    G = nx.Graph()

    # Load nodes
    for row in conn.execute("SELECT id, type, name, metadata, apple_music_id, discogs_id FROM entities").fetchall():
        G.add_node(
            row["id"],
            type=row["type"],
            name=row["name"],
            metadata=row["metadata"],
            apple_music_id=row["apple_music_id"],
            discogs_id=row.get("discogs_id") if "discogs_id" in row.keys() else None,
        )

    # Load edges
    for row in conn.execute("SELECT source_id, target_id, relation, confidence, metadata FROM relations").fetchall():
        if row["source_id"] in G and row["target_id"] in G:
            G.add_edge(
                row["source_id"],
                row["target_id"],
                relation=row["relation"],
                confidence=row["confidence"],
                metadata=row["metadata"],
            )

    if close_conn:
        conn.close()

    return G


def shortest_path(G, source, target):
    """Find shortest path between two entities.

    Returns list of entity IDs, or None if no path exists.
    """
    try:
        return nx.shortest_path(G, source, target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def path_detail(G, path):
    """Annotate a path with entity names and edge relations.

    Returns list of dicts with node info and connecting edge info.
    """
    details = []
    for i, node_id in enumerate(path):
        node_data = G.nodes[node_id]
        entry = {
            "id": node_id,
            "name": node_data.get("name", ""),
            "type": node_data.get("type", ""),
        }
        if i > 0:
            edge_data = G.edges[path[i - 1], node_id]
            entry["edge_from"] = path[i - 1]
            entry["edge_relation"] = edge_data.get("relation", "connected")
        details.append(entry)
    return details


def ego_graph(G, entity_id, depth=1):
    """Get the N-hop neighborhood subgraph around an entity."""
    return nx.ego_graph(G, entity_id, radius=depth)


def border_nodes(G, collection_ids):
    """Find entities connected to the collection but not in it.

    Args:
        G: The full graph.
        collection_ids: Set of entity IDs that are "in the collection" (have apple_music_id).

    Returns:
        List of (entity_id, connection_count) tuples, sorted by connection count descending.
        connection_count = how many collection entities this border node connects to.
    """
    border = {}
    for cid in collection_ids:
        if cid not in G:
            continue
        for neighbor in G.neighbors(cid):
            if neighbor not in collection_ids:
                border[neighbor] = border.get(neighbor, 0) + 1

    return sorted(border.items(), key=lambda x: -x[1])


def random_walk(G, start, steps=5, edge_types=None):
    """Weighted random walk from a starting entity.

    Args:
        G: The graph.
        start: Starting entity ID.
        steps: Maximum number of steps.
        edge_types: Optional list of relation types to follow. None = follow all.

    Returns:
        List of entity IDs visited.
    """
    path = [start]
    current = start

    for _ in range(steps):
        neighbors = list(G.neighbors(current))
        if edge_types:
            neighbors = [
                n for n in neighbors
                if G.edges[current, n].get("relation") in edge_types
            ]
        if not neighbors:
            break
        # Avoid revisiting nodes when possible
        unvisited = [n for n in neighbors if n not in path]
        if unvisited:
            current = random.choice(unvisited)
        else:
            current = random.choice(neighbors)
        path.append(current)

    return path


def centrality(G, top_n=None):
    """Calculate degree centrality for all nodes.

    Returns dict of {entity_id: centrality_score}.
    If top_n specified, returns only the top N.
    """
    scores = nx.degree_centrality(G)
    if top_n:
        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])[:top_n]
        return dict(sorted_scores)
    return scores


def clusters(G, min_size=1):
    """Detect communities using greedy modularity optimization.

    Returns list of sets, each set containing entity IDs in one community.
    """
    if G.number_of_nodes() == 0:
        return []
    from networkx.algorithms.community import greedy_modularity_communities
    communities = list(greedy_modularity_communities(G))
    return [c for c in communities if len(c) >= min_size]


# --- CLI output helpers ---

def _enrich_node(G, node_id):
    """Add name/type to a node ID for CLI output."""
    if node_id in G.nodes:
        data = G.nodes[node_id]
        return {"id": node_id, "name": data.get("name", ""), "type": data.get("type", "")}
    return {"id": node_id}


def cli_shortest_path(source, target):
    G = load_graph()
    path = shortest_path(G, source, target)
    if path is None:
        return {"error": "No path found", "source": source, "target": target}
    return {
        "source": source,
        "target": target,
        "length": len(path) - 1,
        "path": path_detail(G, path),
    }


def cli_ego(entity_id, depth=2):
    G = load_graph()
    if entity_id not in G:
        return {"error": f"Entity {entity_id} not found in graph"}
    sub = ego_graph(G, entity_id, depth=int(depth))
    nodes = [_enrich_node(G, n) for n in sub.nodes]
    edges = [
        {"source": u, "target": v, "relation": G.edges[u, v].get("relation", "")}
        for u, v in sub.edges
    ]
    return {
        "center": entity_id,
        "depth": int(depth),
        "nodes": len(nodes),
        "edges": len(edges),
        "graph": {"nodes": nodes, "edges": edges},
    }


def cli_border(collection_csv):
    G = load_graph()
    # If "auto", find all entities with apple_music_id
    if collection_csv == "auto":
        cids = {n for n, d in G.nodes(data=True) if d.get("apple_music_id")}
    else:
        cids = set(collection_csv.split(","))
    borders = border_nodes(G, cids)
    return {
        "collectionSize": len(cids),
        "borderNodes": len(borders),
        "border": [
            {**_enrich_node(G, nid), "connections": count}
            for nid, count in borders[:20]
        ],
    }


def cli_walk(start, steps=5):
    G = load_graph()
    if start not in G:
        return {"error": f"Entity {start} not found in graph"}
    walk = random_walk(G, start, steps=int(steps))
    return {
        "start": start,
        "steps": int(steps),
        "actualSteps": len(walk) - 1,
        "walk": path_detail(G, walk),
    }


def cli_centrality(top_n=10):
    G = load_graph()
    scores = centrality(G, top_n=int(top_n))
    return {
        "totalNodes": G.number_of_nodes(),
        "topN": int(top_n),
        "nodes": [
            {**_enrich_node(G, nid), "centrality": round(score, 4)}
            for nid, score in sorted(scores.items(), key=lambda x: -x[1])
        ],
    }


def cli_clusters():
    G = load_graph()
    communities = clusters(G)
    result = []
    for i, community in enumerate(communities):
        nodes = [_enrich_node(G, n) for n in community]
        result.append({
            "cluster": i,
            "size": len(nodes),
            "nodes": sorted(nodes, key=lambda x: x.get("name", "")),
        })
    return {"totalClusters": len(result), "clusters": sorted(result, key=lambda x: -x["size"])}


def cli_stats():
    G = load_graph()
    type_counts = {}
    for _, data in G.nodes(data=True):
        t = data.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "components": nx.number_connected_components(G),
        "nodeTypes": type_counts,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: engine.py <command> [args]"}))
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    dispatch = {
        "shortest-path": lambda: cli_shortest_path(args[0], args[1]),
        "ego": lambda: cli_ego(args[0], args[1] if len(args) > 1 else 2),
        "border": lambda: cli_border(args[0] if args else "auto"),
        "walk": lambda: cli_walk(args[0], args[1] if len(args) > 1 else 5),
        "centrality": lambda: cli_centrality(args[0] if args else 10),
        "clusters": lambda: cli_clusters(),
        "stats": lambda: cli_stats(),
    }

    fn = dispatch.get(cmd)
    if not fn:
        print(json.dumps({"error": f"Unknown command: {cmd}. Use: shortest-path, ego, border, walk, centrality, clusters, stats"}))
        sys.exit(1)

    try:
        result = fn()
    except Exception as e:
        result = {"error": str(e)}
    print(json.dumps(result, indent=2, default=str))
```

```python
# scripts/graph/__init__.py
# (empty)
```

**Step 4: Run tests**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_graph_engine.py -v
```

Expected: 9 tests PASS.

**Step 5: Commit**

```bash
git add scripts/graph/ tests/test_graph_engine.py
git commit -m "feat: add graph engine with traversal primitives (shortest path, walk, border, centrality, clusters)"
```

---

## Task 6: Config File Support

Create `~/.music-agent/config.json` management for storing the Discogs token and future config.

**Files:**
- Create: `music-agent/scripts/config.py`
- Create: `music-agent/tests/test_config.py`

**Step 1: Write failing tests**

```python
# tests/test_config.py
import json
from pathlib import Path


def test_load_config_missing_file(tmp_path):
    """Should return empty config when file doesn't exist."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from config import load_config
    result = load_config(tmp_path / "nonexistent.json")
    assert result == {}


def test_save_and_load_config(tmp_path):
    """Should round-trip config data."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from config import load_config, save_config

    config_path = tmp_path / "config.json"
    save_config({"discogs_token": "abc123"}, config_path)
    result = load_config(config_path)
    assert result["discogs_token"] == "abc123"


def test_save_config_preserves_existing(tmp_path):
    """Should merge new keys without losing existing ones."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from config import load_config, save_config

    config_path = tmp_path / "config.json"
    save_config({"discogs_token": "abc123"}, config_path)
    save_config({"other_key": "value"}, config_path)
    result = load_config(config_path)
    assert result["discogs_token"] == "abc123"
    assert result["other_key"] == "value"
```

**Step 2: Run to verify failure**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_config.py -v
```

Expected: FAIL.

**Step 3: Implement config.py**

```python
#!/usr/bin/env python3
"""
config.py - Configuration management for music-agent.

Stores settings in ~/.music-agent/config.json.

Usage:
    python3 scripts/config.py get <key>
    python3 scripts/config.py set <key> <value>
    python3 scripts/config.py show
"""

import sys
import json
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".music-agent" / "config.json"


def load_config(path=None):
    """Load config from JSON file. Returns empty dict if missing."""
    path = path or DEFAULT_CONFIG_PATH
    if not Path(path).exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_config(updates, path=None):
    """Merge updates into existing config and save."""
    path = Path(path or DEFAULT_CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_config(path)
    existing.update(updates)
    with open(path, "w") as f:
        json.dump(existing, f, indent=2)
    return existing


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: config.py <get|set|show> [key] [value]"}))
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "show":
        print(json.dumps(load_config(), indent=2))
    elif cmd == "get":
        config = load_config()
        key = sys.argv[2]
        print(json.dumps({"key": key, "value": config.get(key)}))
    elif cmd == "set":
        key, value = sys.argv[2], sys.argv[3]
        result = save_config({key: value})
        print(json.dumps({"set": key, "config": result}, indent=2))
    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
```

**Step 4: Run tests**

```bash
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/test_config.py -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/config.py tests/test_config.py
git commit -m "feat: add config management for API tokens and settings"
```

---

## Task 7: Update Setup Script

Add Discogs + networkx installation and token configuration.

**Files:**
- Modify: `music-agent/scripts/setup.sh`

**Step 1: Add new dependencies and Discogs token check to setup.sh**

After the `musicbrainzngs` install line, add:

```bash
pip3 install python3-discogs-client --quiet && echo "  ✓ python3-discogs-client installed" || echo "  ⚠ python3-discogs-client install failed — Discogs lookups won't work"
pip3 install networkx --quiet && echo "  ✓ networkx installed" || echo "  ⚠ networkx install failed — Graph engine won't work"
```

After the permissions section, add:

```bash
# 3b. Set permissions on new scripts
chmod +x "$PLUGIN_DIR"/scripts/graph/*.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/config.py 2>/dev/null || true
```

After the MusicBrainz test, add:

```bash
# 6. Check Discogs token
echo ""
echo "→ Checking Discogs configuration..."
DISCOGS_TOKEN="${DISCOGS_TOKEN:-}"
if [ -z "$DISCOGS_TOKEN" ]; then
    # Check config file
    DISCOGS_TOKEN=$(python3 "$PLUGIN_DIR/scripts/config.py" get discogs_token 2>/dev/null | python3 -c 'import sys,json; print(json.load(sys.stdin).get("value",""))' 2>/dev/null || echo "")
fi
if [ -z "$DISCOGS_TOKEN" ] || [ "$DISCOGS_TOKEN" = "None" ]; then
    echo "  ⚠ No Discogs token configured"
    echo "    Get one at: https://www.discogs.com/settings/developers"
    echo "    Then run: python3 $PLUGIN_DIR/scripts/config.py set discogs_token YOUR_TOKEN"
else
    echo "  ✓ Discogs token configured"
fi

# 7. Test graph engine
echo ""
echo "→ Testing graph engine..."
GRAPH_RESULT=$(python3 "$PLUGIN_DIR/scripts/graph/engine.py" stats 2>/dev/null || echo '{"error":"failed"}')
GRAPH_NODES=$(echo "$GRAPH_RESULT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("nodes",0))' 2>/dev/null || echo "0")
echo "  ✓ Graph engine ready ($GRAPH_NODES nodes in knowledge graph)"
```

Update the final commands list to include new capabilities:

```bash
echo "  /dig <subject>    — Deep research (now with Discogs credits)"
```

And add a graph engine section:

```bash
echo ""
echo "Graph engine commands (via python3 scripts/graph/engine.py):"
echo "  shortest-path     — Find credit path between two entities"
echo "  walk              — Random credit-graph walk"
echo "  border            — Find entities at the edge of your collection"
echo "  centrality        — Most-connected entities in your graph"
echo "  clusters          — Detect communities/scenes"
```

**Step 2: Verify setup script runs**

```bash
bash /Users/jaredmcfarland/Developer/music-agent/music-agent/scripts/setup.sh
```

Expected: All checks pass (Discogs token may warn if not yet configured).

**Step 3: Commit**

```bash
git add scripts/setup.sh
git commit -m "feat: update setup for Discogs, networkx, and graph engine"
```

---

## Task 8: Update /dig Command for Discogs

Extend the `/dig` command to use Discogs credits when available, enriching the knowledge graph with denser credit data.

**Files:**
- Modify: `music-agent/commands/dig.md`

**Step 1: Update dig.md process section**

Add Discogs lookups after the MusicBrainz section in the process. Insert after step 4:

```markdown
4b. If Discogs token is configured, enrich with Discogs data:
   - For artists: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/discogs_lookup.py artist "<name>"`
   - Match Discogs artist to MusicBrainz entity, link: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/db/db.py link-discogs "<mbid>" "<discogs-id>"`
   - For key releases, get full credits: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/discogs_lookup.py credits <discogs-release-id>`
   - Discogs credits include roles MusicBrainz may lack: remix credits, sleeve design, A&R, liner notes
   - Store all new entities and credit relations in the knowledge graph
4c. Use the graph engine to surface connections:
   - Check centrality: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/graph/engine.py centrality 5` — who's most connected?
   - Check border: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/graph/engine.py border auto` — what's at the edge of the collection?
   - If two entities seem related, check path: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/graph/engine.py shortest-path <id-a> <id-b>`
```

Update success criteria to add:

```markdown
- Discogs credits incorporated when available (producers, engineers, remix credits, sleeve design)
- Graph engine used to surface non-obvious connections
```

**Step 2: Commit**

```bash
git add commands/dig.md
git commit -m "feat: extend /dig to use Discogs credits and graph engine"
```

---

## Task 9: Update SKILL.md with New Tools

Add graph engine and Discogs references to the auto-trigger skill.

**Files:**
- Modify: `music-agent/skills/music-agent/SKILL.md`

**Step 1: Add new tool references**

In the tools reference section, add:

```markdown
- **Discogs (Python)**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lookup/discogs_lookup.py <type> <query|id>`
  - Types: `artist <name>`, `release <discogs-id>`, `credits <discogs-id>`, `label <discogs-id>`, `label-releases <discogs-id> [page]`, `artist-releases <discogs-id> [page]`
  - Requires DISCOGS_TOKEN env var or ~/.music-agent/config.json

- **Graph Engine (Python)**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/graph/engine.py <command> [args]`
  - Commands: `shortest-path <id-a> <id-b>`, `ego <id> [depth]`, `border [auto|ids]`, `walk <start> [steps]`, `centrality [top-n]`, `clusters`, `stats`
  - Powers the Lenses: Drift (random walk), Six Degrees (shortest path), Expedition (border nodes)
```

Add a new workflow pattern:

```markdown
5. **"Connect these"**: shortest-path via graph engine → display credit chain with entity names and relation types → offer to explore intermediate nodes
6. **"What's at the edge?"**: border nodes via graph engine → entities connected to collection but not in it → ranked by connection density → offer to research top candidates
```

**Step 2: Commit**

```bash
git add skills/music-agent/SKILL.md
git commit -m "feat: add Discogs and graph engine references to auto-trigger skill"
```

---

## Task 10: Update CLAUDE.md

Add Phase 1 tools to the project documentation.

**Files:**
- Modify: `music-agent/CLAUDE.md`

**Step 1: Add new sections to CLAUDE.md**

Under "Key Scripts", add:

```markdown
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
```

Under "Testing Individual Scripts", add:

```markdown
# Discogs — requires DISCOGS_TOKEN
python3 music-agent/scripts/lookup/discogs_lookup.py artist "Autechre"
python3 music-agent/scripts/lookup/discogs_lookup.py credits 12345

# Graph engine — requires populated KB
python3 music-agent/scripts/graph/engine.py stats
python3 music-agent/scripts/graph/engine.py centrality 5
python3 music-agent/scripts/graph/engine.py border auto

# Config
python3 music-agent/scripts/config.py show

# Tests
cd music-agent && python3 -m pytest tests/ -v
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add Discogs, graph engine, and config to CLAUDE.md"
```

---

## Verification Checklist

After all tasks, run the full suite:

```bash
# All tests pass
cd /Users/jaredmcfarland/Developer/music-agent/music-agent && python3 -m pytest tests/ -v

# Graph engine works with real KB
python3 music-agent/scripts/graph/engine.py stats

# Discogs lookup works (requires token)
python3 music-agent/scripts/lookup/discogs_lookup.py artist "Autechre"

# Setup script runs clean
bash music-agent/scripts/setup.sh
```

---

## What This Enables

With Phase 1 complete, the system has:

1. **Dense credit data** — MusicBrainz + Discogs credits fused into the KB. Producers, engineers, mastering, remix credits, sleeve designers, A&R, label hierarchies.

2. **Traversal primitives** — shortest path, random walk, border nodes, centrality, clustering. All via CLI, all JSON output, all composable.

3. **Entity resolution** — Same artist/label/release linked across MusicBrainz, Discogs, and Apple Music. One entity, multiple source IDs.

4. **Foundation for all four Lenses**:
   - **The Drift** → `engine.py walk` (random walk following credit edges)
   - **Six Degrees** → `engine.py shortest-path` (credit chain between entities)
   - **The Expedition** → `engine.py border` (edges leading out of collection)
   - **Seasonal Self** → Needs Phase 2 (temporal stream), but centrality/clustering already reveal structural insights

**Next**: Phase 2 — Living Awareness (background listener + temporal stream).
