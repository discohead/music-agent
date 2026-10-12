#!/usr/bin/env bash
# session_context.sh - Gather session context for the SessionStart hook
# Outputs JSON with current playback state and knowledge graph stats
#
# TODO: All errors are silenced with 2>/dev/null fallbacks. If Apple Music is
#   not running or the DB is missing, the user gets "unknown" / "not initialized"
#   with no way to diagnose. Consider logging errors to ~/.music-agent/debug.log.

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

NOW=$(aux playback now-playing --quiet 2>/dev/null || echo '{"data":{"state":"unavailable"}}')
STATS=$(python3 "$PLUGIN_DIR/scripts/db/db.py" stats 2>/dev/null || echo '{"status":"not initialized"}')

TRACK_INFO=$(echo "$NOW" | python3 -c '
import sys, json
d = json.load(sys.stdin)
t = d.get("data") or {}
if t.get("title"):
    print(t.get("title", "nothing") + " by " + t.get("artist_name", "unknown"))
else:
    print("nothing")
' 2>/dev/null || echo "unknown")

KB_INFO=$(echo "$STATS" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print(str(d.get("entities", 0)) + " entities, " + str(d.get("relations", 0)) + " relations")
' 2>/dev/null || echo "not initialized")

cat <<EOF
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "music-agent active. Now playing: ${TRACK_INFO}. Knowledge graph: ${KB_INFO}. Commands: /now /dig /queue /who /taste /kb"}}
EOF
