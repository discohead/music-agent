#!/usr/bin/env bash
set -euo pipefail

# music-agent setup script
# Run this once after installing the plugin

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

echo "🎵 music-agent setup"
echo "===================="

# 0. Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "  ✗ python3 not found. Please install Python 3.7+ and try again."
    exit 1
fi
echo "  ✓ $(python3 --version)"

# 1. Install Python dependencies
echo ""
echo "→ Installing Python dependencies..."
pip3 install musicbrainzngs --quiet && echo "  ✓ musicbrainzngs installed" || echo "  ⚠ musicbrainzngs install failed — MusicBrainz lookups won't work"

# 2. Initialize the knowledge graph database
echo ""
echo "→ Initializing knowledge graph..."
python3 "$PLUGIN_DIR/scripts/db/db.py" init
echo "  ✓ Database at ~/.music-agent/knowledge.db"

# 3. Make JXA scripts executable (they're run via osascript, but just in case)
echo ""
echo "→ Setting script permissions..."
chmod +x "$PLUGIN_DIR"/scripts/apple-music/*.jxa 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/lookup/*.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/db/*.py 2>/dev/null || true
echo "  ✓ Permissions set"

# 4. Test Apple Music connection
echo ""
echo "→ Testing Apple Music connection..."
if command -v osascript &> /dev/null; then
    RESULT=$(osascript -l JavaScript "$PLUGIN_DIR/scripts/apple-music/now_playing.jxa" 2>/dev/null || echo '{"status":"error"}')
    STATUS=$(echo "$RESULT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status","unknown"))' 2>/dev/null || echo "unknown")
    if [ "$STATUS" = "error" ] || [ "$STATUS" = "unknown" ]; then
        echo "  ⚠ Apple Music not running or not accessible"
        echo "    Open Apple Music and try again"
    else
        echo "  ✓ Apple Music connected (state: $STATUS)"
    fi
else
    echo "  ⚠ osascript not found — are you on macOS?"
fi

# 5. Test MusicBrainz connection
echo ""
echo "→ Testing MusicBrainz connection..."
MB_RESULT=$(python3 "$PLUGIN_DIR/scripts/lookup/musicbrainz_lookup.py" artist "Autechre" 2>/dev/null || echo '{"error":"failed"}')
MB_COUNT=$(echo "$MB_RESULT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("count",0))' 2>/dev/null || echo "0")
if [ "$MB_COUNT" -gt "0" ]; then
    echo "  ✓ MusicBrainz API accessible"
else
    echo "  ⚠ MusicBrainz connection failed"
fi

echo ""
echo "===================="
echo "✓ Setup complete!"
echo ""
echo "Available commands:"
echo "  /now              — What's playing? Research it."
echo "  /dig <subject>    — Deep research mode"
echo "  /queue <seed>     — Build an intelligent queue"
echo "  /who <artist>     — Explore the credit graph"
echo "  /taste            — Analyze your library"
echo "  /kb               — Inspect the knowledge graph"
echo ""
echo "Personas (add --persona <name> to any command):"
echo "  crate-digger      — Obscure finds, deep cuts, small labels"
echo "  historian         — Lineage, context, influence chains"
echo "  harmonic-dj       — Energy arcs, transitions, flow"
echo "  anti-bubble       — Deliberate filter bubble breaking"
echo ""
