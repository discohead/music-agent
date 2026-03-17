"""Tests for discogs_lookup.py using mocked Discogs client."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts" / "lookup")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_format_artist():
    from discogs_lookup import format_artist
    mock_artist = MagicMock()
    mock_artist.id = 27
    mock_artist.name = "Autechre"
    mock_artist.real_name = ""
    mock_artist.profile = "Electronic duo"
    mock_artist.members = []
    mock_artist.aliases = []
    mock_artist.groups = []

    result = format_artist(mock_artist)
    assert result["id"] == 27
    assert result["name"] == "Autechre"
    assert result["source"] == "discogs"


def test_format_release_credits():
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

    result = format_label_info(mock_label)
    assert result["name"] == "Warp Records"
    assert len(result["sublabels"]) == 1
    assert result["sublabels"][0]["name"] == "Warp Classics"
    assert result["parent"] is None
