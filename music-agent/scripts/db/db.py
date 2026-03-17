#!/usr/bin/env python3
"""
db.py - Knowledge graph database operations for music-agent.

Usage:
    python3 scripts/db/db.py init
    python3 scripts/db/db.py store-entity <json>
    python3 scripts/db/db.py store-relation <json>
    python3 scripts/db/db.py annotate <json>
    python3 scripts/db/db.py query <sql>
    python3 scripts/db/db.py search <term> [type]
    python3 scripts/db/db.py log-session <json>
    python3 scripts/db/db.py cache-get <key>
    python3 scripts/db/db.py cache-set <key> <json>
    python3 scripts/db/db.py stats

DB location: ~/.music-agent/knowledge.db
"""

import sys
import json
import sqlite3
from pathlib import Path

DB_DIR = Path.home() / ".music-agent"
DB_PATH = DB_DIR / "knowledge.db"
SCHEMA_PATH = Path(__file__).parent.parent.parent / "db" / "schema.sql"


def get_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.close()
    return {"status": "initialized", "path": str(DB_PATH)}


def store_entity(data):
    """Store or update an entity. data = {id, type, name, metadata, sources, apple_music_id?}"""
    for key in ("id", "type", "name"):
        if key not in data:
            return {"error": f"Missing required field: {key}"}
    conn = get_db()
    conn.execute("""
        INSERT INTO entities (id, type, name, metadata, sources, apple_music_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            metadata = json_patch(entities.metadata, excluded.metadata),
            sources = excluded.sources,
            apple_music_id = COALESCE(excluded.apple_music_id, entities.apple_music_id),
            updated_at = CURRENT_TIMESTAMP
    """, (
        data["id"], data["type"], data["name"],
        json.dumps(data.get("metadata", {})),
        json.dumps(data.get("sources", [])),
        data.get("apple_music_id")
    ))
    conn.commit()
    conn.close()
    return {"stored": data["id"], "name": data["name"]}


def store_relation(data):
    """Store a relation. data = {source_id, target_id, relation, confidence?, attributed_to?, metadata?}"""
    conn = get_db()
    conn.execute("""
        INSERT INTO relations (source_id, target_id, relation, confidence, attributed_to, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id, target_id, relation) DO UPDATE SET
            confidence = excluded.confidence,
            metadata = excluded.metadata
    """, (
        data["source_id"], data["target_id"], data["relation"],
        data.get("confidence", 1.0),
        data.get("attributed_to"),
        json.dumps(data.get("metadata", {}))
    ))
    conn.commit()
    conn.close()
    return {"stored": f"{data['source_id']} --{data['relation']}--> {data['target_id']}"}


def annotate(data):
    """Add annotation. data = {entity_id, persona?, annotation_type?, content, tags?}"""
    conn = get_db()
    conn.execute("""
        INSERT INTO annotations (entity_id, persona, annotation_type, content, tags)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["entity_id"],
        data.get("persona", "agent"),
        data.get("annotation_type", "note"),
        data["content"],
        json.dumps(data.get("tags", []))
    ))
    conn.commit()
    conn.close()
    return {"annotated": data["entity_id"]}


def query(sql):
    """Run arbitrary read query (SELECT/WITH only)."""
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
        return {"error": "Only SELECT/WITH queries allowed. Use specific commands for writes."}
    conn = get_db()
    try:
        rows = conn.execute(sql).fetchall()
        result = [dict(r) for r in rows]
        conn.close()
        return {"count": len(result), "rows": result}
    except Exception as e:
        conn.close()
        return {"error": str(e)}


def search(term, entity_type=None):
    """Search entities by name."""
    conn = get_db()
    if entity_type:
        rows = conn.execute(
            "SELECT * FROM entities WHERE name LIKE ? AND type = ? ORDER BY updated_at DESC LIMIT 20",
            (f"%{term}%", entity_type)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM entities WHERE name LIKE ? ORDER BY updated_at DESC LIMIT 20",
            (f"%{term}%",)
        ).fetchall()
    
    results = []
    for r in rows:
        row = dict(r)
        # Get relations
        rels = conn.execute(
            "SELECT relation, target_id FROM relations WHERE source_id = ? LIMIT 10",
            (row["id"],)
        ).fetchall()
        row["relations"] = [dict(rel) for rel in rels]
        # Get annotations
        anns = conn.execute(
            "SELECT persona, content, tags FROM annotations WHERE entity_id = ? ORDER BY created_at DESC LIMIT 5",
            (row["id"],)
        ).fetchall()
        row["annotations"] = [dict(a) for a in anns]
        results.append(row)
    
    conn.close()
    return {"query": term, "type": entity_type, "count": len(results), "results": results}


def log_session(data):
    """Log a listening session. data = {context?, persona?, seed?, tracks: [{name, artist, album, apple_music_id?, skipped?}]}"""
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO sessions (context, persona, seed) VALUES (?, ?, ?)
    """, (data.get("context"), data.get("persona"), data.get("seed")))
    session_id = cur.lastrowid
    
    for i, track in enumerate(data.get("tracks", [])):
        conn.execute("""
            INSERT INTO session_tracks (session_id, position, track_name, track_artist, track_album, apple_music_id, skipped)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, i,
            track.get("name"), track.get("artist"), track.get("album"),
            track.get("apple_music_id"),
            track.get("skipped", False)
        ))
    
    conn.commit()
    conn.close()
    return {"session_id": session_id, "tracks_logged": len(data.get("tracks", []))}


def cache_get(key):
    conn = get_db()
    row = conn.execute(
        "SELECT result, fetched_at FROM lookup_cache WHERE cache_key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))",
        (key,)
    ).fetchone()
    conn.close()
    if row:
        return {"hit": True, "result": json.loads(row["result"]), "fetched_at": row["fetched_at"]}
    return {"hit": False}


def cache_set(key, result_json):
    conn = get_db()
    conn.execute("""
        INSERT INTO lookup_cache (cache_key, result) VALUES (?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET result = excluded.result, fetched_at = CURRENT_TIMESTAMP
    """, (key, result_json))
    conn.commit()
    conn.close()
    return {"cached": key}


def start_thread(data):
    """Start a research thread. data = {title, seed, persona?}"""
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO research_threads (title, seed, persona, steps, findings)
        VALUES (?, ?, ?, '[]', '[]')
    """, (data.get("title"), data.get("seed"), data.get("persona")))
    conn.commit()
    thread_id = cur.lastrowid
    conn.close()
    return {"thread_id": thread_id, "title": data.get("title")}


def update_thread(data):
    """Update a research thread. data = {id, steps?, findings?}"""
    if "id" not in data:
        return {"error": "Missing required field: id"}
    conn = get_db()
    if "steps" in data:
        conn.execute("""
            UPDATE research_threads SET steps = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (json.dumps(data["steps"]), data["id"]))
    if "findings" in data:
        conn.execute("""
            UPDATE research_threads SET findings = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (json.dumps(data["findings"]), data["id"]))
    conn.commit()
    conn.close()
    return {"updated": data["id"]}


def get_threads(limit=10):
    """List recent research threads."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM research_threads ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return {"count": len(rows), "threads": [dict(r) for r in rows]}


def migrate():
    """Apply pending schema migrations."""
    conn = get_db()
    migrations_dir = SCHEMA_PATH.parent
    applied = []
    cols = [row[1] for row in conn.execute("PRAGMA table_info(entities)").fetchall()]
    if "discogs_id" not in cols:
        migration_path = migrations_dir / "migration_001_discogs.sql"
        if migration_path.exists():
            with open(migration_path) as f:
                conn.executescript(f.read())
            applied.append("001_discogs")
    conn.close()
    return {"applied": applied, "status": "up to date" if not applied else "migrations applied"}


def stats():
    # TODO: The bare `except Exception` below silently returns 0 if a table doesn't
    # exist (e.g. after schema change). This masks schema drift. Consider checking
    # table existence explicitly or logging the exception.
    #
    # TODO: The f-string table name is safe (hardcoded list) but looks like SQL
    # injection surface. Could use parameterized query with sqlite_master instead.
    conn = get_db()
    result = {}
    for table in ["entities", "relations", "annotations", "sessions", "session_tracks", "lookup_cache", "taste_signals", "research_threads"]:
        try:
            row = conn.execute(f"SELECT COUNT(*) as c FROM {table}").fetchone()
            result[table] = row["c"]
        except Exception:
            result[table] = 0
    
    # Entity type breakdown
    rows = conn.execute("SELECT type, COUNT(*) as c FROM entities GROUP BY type").fetchall()
    result["entity_types"] = {r["type"]: r["c"] for r in rows}
    
    # Recent sessions
    rows = conn.execute("SELECT id, started_at, context, seed FROM sessions ORDER BY started_at DESC LIMIT 5").fetchall()
    result["recent_sessions"] = [dict(r) for r in rows]
    
    conn.close()
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: db.py <command> [args]"}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    dispatch = {
        "init": lambda: init_db(),
        "store-entity": lambda: store_entity(json.loads(sys.argv[2])),
        "store-relation": lambda: store_relation(json.loads(sys.argv[2])),
        "annotate": lambda: annotate(json.loads(sys.argv[2])),
        "query": lambda: query(sys.argv[2]),
        "search": lambda: search(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None),
        "log-session": lambda: log_session(json.loads(sys.argv[2])),
        "cache-get": lambda: cache_get(sys.argv[2]),
        "cache-set": lambda: cache_set(sys.argv[2], sys.argv[3]),
        "start-thread": lambda: start_thread(json.loads(sys.argv[2])),
        "update-thread": lambda: update_thread(json.loads(sys.argv[2])),
        "threads": lambda: get_threads(),
        "migrate": lambda: migrate(),
        "stats": lambda: stats(),
    }
    
    fn = dispatch.get(cmd)
    if not fn:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

    try:
        print(json.dumps(fn(), indent=2, default=str))
    except (json.JSONDecodeError, IndexError) as e:
        print(json.dumps({"error": f"Invalid arguments for '{cmd}': {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
