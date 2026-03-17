"""Tests for schema: discogs_id column and index on entities table."""


def test_entities_has_discogs_id(db_conn):
    cols = [row[1] for row in db_conn.execute("PRAGMA table_info(entities)").fetchall()]
    assert "discogs_id" in cols


def test_discogs_id_indexed(db_conn):
    indexes = [row[1] for row in db_conn.execute("PRAGMA index_list(entities)").fetchall()]
    assert any("discogs" in idx for idx in indexes)
