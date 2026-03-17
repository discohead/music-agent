def test_db_fixture_works(db_conn):
    row = db_conn.execute("SELECT COUNT(*) as c FROM entities").fetchone()
    assert row["c"] == 0


def test_populated_db_has_data(populated_db):
    row = populated_db.execute("SELECT COUNT(*) as c FROM entities").fetchone()
    assert row["c"] == 10
    row = populated_db.execute("SELECT COUNT(*) as c FROM relations").fetchone()
    assert row["c"] == 13
