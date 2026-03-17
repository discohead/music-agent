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
    path = path or DEFAULT_CONFIG_PATH
    if not Path(path).exists():
        return {}
    with open(path) as f:
        return json.load(f)


def save_config(updates, path=None):
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
