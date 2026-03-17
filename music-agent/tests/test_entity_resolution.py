import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "db"))


def test_link_discogs_id(db_conn, db_path):
    """link_discogs should add discogs_id to an existing entity."""
    import db as db_module
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = db_path

    db_conn.execute(
        "INSERT INTO entities (id, type, name, metadata, sources) VALUES (?, ?, ?, ?, ?)",
        ("mbid-123", "artist", "Autechre", "{}", '["musicbrainz"]')
    )
    db_conn.commit()

    result = db_module.link_discogs("mbid-123", "27")
    assert result["linked"] == "mbid-123"
    assert result["discogs_id"] == "27"

    row = db_conn.execute("SELECT discogs_id, sources FROM entities WHERE id = ?", ("mbid-123",)).fetchone()
    assert row["discogs_id"] == "27"
    sources = json.loads(row["sources"])
    assert "discogs" in sources

    db_module.DB_PATH = original_db_path


def test_find_entity_by_discogs_id(db_conn, db_path):
    """Should find entity by discogs_id."""
    import db as db_module
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = db_path

    db_conn.execute(
        "INSERT INTO entities (id, type, name, metadata, sources, discogs_id) VALUES (?, ?, ?, ?, ?, ?)",
        ("mbid-123", "artist", "Autechre", "{}", '["musicbrainz","discogs"]', "27")
    )
    db_conn.commit()

    result = db_module.find_by_discogs_id("27")
    assert result is not None
    assert result["id"] == "mbid-123"

    result = db_module.find_by_discogs_id("9999")
    assert result is None

    db_module.DB_PATH = original_db_path
