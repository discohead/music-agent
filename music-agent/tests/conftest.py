import pytest
import sqlite3
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR / "db"))
sys.path.insert(0, str(SCRIPTS_DIR / "lookup"))
sys.path.insert(0, str(SCRIPTS_DIR / "graph"))


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_knowledge.db"


@pytest.fixture
def db_conn(db_path):
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
