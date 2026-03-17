import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_load_config_missing_file(tmp_path):
    from config import load_config
    result = load_config(tmp_path / "nonexistent.json")
    assert result == {}


def test_save_and_load_config(tmp_path):
    from config import load_config, save_config
    config_path = tmp_path / "config.json"
    save_config({"discogs_token": "abc123"}, config_path)
    result = load_config(config_path)
    assert result["discogs_token"] == "abc123"


def test_save_config_preserves_existing(tmp_path):
    from config import load_config, save_config
    config_path = tmp_path / "config.json"
    save_config({"discogs_token": "abc123"}, config_path)
    save_config({"other_key": "value"}, config_path)
    result = load_config(config_path)
    assert result["discogs_token"] == "abc123"
    assert result["other_key"] == "value"
