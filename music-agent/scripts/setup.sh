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

# 0b. Check aux CLI
if ! command -v aux &> /dev/null; then
    echo "  ✗ aux not found. Install from https://github.com/jaredmcfarland/aux"
    exit 1
fi
echo "  ✓ aux $(aux --version 2>/dev/null || echo '(version unknown)')"

# 1. Install Python dependencies
echo ""
echo "→ Installing Python dependencies..."
pip3 install musicbrainzngs --quiet && echo "  ✓ musicbrainzngs installed" || echo "  ⚠ musicbrainzngs install failed — MusicBrainz lookups won't work"
pip3 install python3-discogs-client --quiet && echo "  ✓ python3-discogs-client installed" || echo "  ⚠ python3-discogs-client install failed — Discogs lookups won't work"
pip3 install networkx --quiet && echo "  ✓ networkx installed" || echo "  ⚠ networkx install failed — Graph engine won't work"

# 2. Initialize the knowledge graph database
echo ""
echo "→ Initializing knowledge graph..."
python3 "$PLUGIN_DIR/scripts/db/db.py" init
echo "  ✓ Database at ~/.music-agent/knowledge.db"

# 3. Set script permissions
echo ""
echo "→ Setting script permissions..."
chmod +x "$PLUGIN_DIR"/scripts/lookup/*.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/db/*.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/graph/*.py 2>/dev/null || true
chmod +x "$PLUGIN_DIR"/scripts/config.py 2>/dev/null || true
echo "  ✓ Permissions set"

# 4. Test Apple Music connection
echo ""
echo "→ Testing Apple Music connection..."
RESULT=$(aux playback status --quiet 2>/dev/null || echo '{"data":{}}')
STATUS=$(echo "$RESULT" | python3 -c 'import sys,json; d=json.load(sys.stdin); s=d.get("data",{}).get("state",""); print(s if s else "unknown")' 2>/dev/null || echo "unknown")
if [ "$STATUS" = "unknown" ]; then
    echo "  ⚠ Apple Music not running or not accessible"
    echo "    Open Apple Music and try again"
else
    echo "  ✓ Apple Music connected (state: $STATUS)"
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

# 6. Check Discogs configuration
echo ""
echo "→ Checking Discogs configuration..."
DISCOGS_TOKEN="${DISCOGS_TOKEN:-}"
if [ -z "$DISCOGS_TOKEN" ]; then
    DISCOGS_TOKEN=$(python3 "$PLUGIN_DIR/scripts/config.py" get discogs_token 2>/dev/null | python3 -c 'import sys,json; v=json.load(sys.stdin).get("value",""); print(v if v and v != "None" else "")' 2>/dev/null || echo "")
fi
if [ -z "$DISCOGS_TOKEN" ]; then
    echo "  ⚠ No Discogs token configured"
    echo "    Get one at: https://www.discogs.com/settings/developers"
    echo "    Then run: python3 $PLUGIN_DIR/scripts/config.py set discogs_token YOUR_TOKEN"
else
    echo "  ✓ Discogs token configured"
fi

# 7. Test graph engine
echo ""
echo "→ Testing graph engine..."
GRAPH_RESULT=$(python3 "$PLUGIN_DIR/scripts/graph/engine.py" stats 2>/dev/null || echo '{"error":"failed"}')
GRAPH_NODES=$(echo "$GRAPH_RESULT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("nodes",0))' 2>/dev/null || echo "0")
echo "  ✓ Graph engine ready ($GRAPH_NODES nodes in knowledge graph)"

echo ""
echo "===================="
echo "✓ Setup complete!"
echo ""
echo "Available commands:"
echo "  /now              — What's playing? Research it."
echo "  /dig <subject>    — Deep research (now with Discogs credits)"
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
echo "Graph engine (python3 scripts/graph/engine.py):"
echo "  shortest-path     — Find credit path between two entities"
echo "  walk              — Random credit-graph walk"
echo "  border            — Entities at the edge of your collection"
echo "  centrality        — Most-connected entities"
echo "  clusters          — Detect communities/scenes"
echo ""
