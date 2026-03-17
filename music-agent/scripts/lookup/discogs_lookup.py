#!/usr/bin/env python3
"""
discogs_lookup.py - Query Discogs for rich metadata, credits, and label info.

Usage:
    python3 scripts/lookup/discogs_lookup.py artist "Autechre"
    python3 scripts/lookup/discogs_lookup.py release <discogs-release-id>
    python3 scripts/lookup/discogs_lookup.py credits <discogs-release-id>
    python3 scripts/lookup/discogs_lookup.py label <discogs-label-id>
    python3 scripts/lookup/discogs_lookup.py label-releases <discogs-label-id> [page]
    python3 scripts/lookup/discogs_lookup.py artist-releases <discogs-artist-id> [page]

Requires: pip install python3-discogs-client (auto-installed by setup)
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config

try:
    import discogs_client
except ImportError:
    print(json.dumps({"error": "python3-discogs-client not installed. Run: pip3 install python3-discogs-client"}))
    sys.exit(1)


def get_client():
    """Return an authenticated Discogs client."""
    token = os.environ.get("DISCOGS_TOKEN")
    if not token:
        config = load_config()
        token = config.get("discogs_token")
    if not token:
        raise ValueError("No Discogs token found. Set DISCOGS_TOKEN env var or run: python3 scripts/config.py set discogs_token <token>")
    return discogs_client.Client("music-agent/0.1.0", user_token=token)


# --- Pure formatting functions (tested independently) ---

def format_artist(artist):
    """Format a Discogs artist object into a dict."""
    return {
        "id": artist.id,
        "name": artist.name,
        "real_name": getattr(artist, "real_name", "") or "",
        "profile": getattr(artist, "profile", "") or "",
        "members": [{"id": m.id, "name": m.name} for m in getattr(artist, "members", []) or []],
        "aliases": [{"id": a.id, "name": a.name} for a in getattr(artist, "aliases", []) or []],
        "groups": [{"id": g.id, "name": g.name} for g in getattr(artist, "groups", []) or []],
        "source": "discogs",
    }


def format_release_credits(release):
    """Format a Discogs release object with full credits."""
    artists = []
    for a in getattr(release, "artists", []) or []:
        artists.append({"id": a.id, "name": a.name})

    credits = []
    for c in getattr(release, "credits", []) or []:
        credits.append({
            "id": c.id,
            "name": c.name,
            "role": getattr(c, "role", ""),
        })

    labels = []
    for l in getattr(release, "labels", []) or []:
        labels.append({"id": l.id, "name": l.name})

    tracklist = []
    for t in getattr(release, "tracklist", []) or []:
        tracklist.append({
            "position": getattr(t, "position", ""),
            "title": getattr(t, "title", ""),
            "duration": getattr(t, "duration", ""),
        })

    return {
        "id": release.id,
        "title": release.title,
        "year": getattr(release, "year", None),
        "artists": artists,
        "credits": credits,
        "labels": labels,
        "tracklist": tracklist,
        "genres": getattr(release, "genres", []) or [],
        "styles": getattr(release, "styles", []) or [],
        "country": getattr(release, "country", ""),
        "source": "discogs",
    }


def format_label_info(label):
    """Format a Discogs label object into a dict."""
    sublabels = []
    for s in getattr(label, "sublabels", []) or []:
        sublabels.append({"id": s.id, "name": s.name})

    parent = None
    parent_label = getattr(label, "parent_label", None)
    if parent_label:
        parent = {"id": parent_label.id, "name": parent_label.name}

    return {
        "id": label.id,
        "name": label.name,
        "profile": getattr(label, "profile", "") or "",
        "sublabels": sublabels,
        "parent": parent,
        "source": "discogs",
    }


# --- API functions ---

def search_artist(query, limit=10):
    """Search for artists by name."""
    try:
        client = get_client()
        results = client.search(query, type="artist")
        artists = []
        for item in results.page(1)[:limit]:
            try:
                artists.append(format_artist(item))
            except Exception:
                continue
        return {"query": query, "count": len(artists), "artists": artists}
    except Exception as e:
        return {"error": str(e)}


def get_release_credits(release_id):
    """Get release with full credits by Discogs release ID."""
    try:
        client = get_client()
        release = client.release(int(release_id))
        return format_release_credits(release)
    except Exception as e:
        return {"error": str(e)}


def get_label_info(label_id):
    """Get label info with sublabels."""
    try:
        client = get_client()
        label = client.label(int(label_id))
        return format_label_info(label)
    except Exception as e:
        return {"error": str(e)}


def get_label_releases(label_id, page=1):
    """Get paginated releases for a label."""
    try:
        client = get_client()
        label = client.label(int(label_id))
        releases = label.releases.page(int(page))
        items = []
        for r in releases:
            items.append({
                "id": r.id,
                "title": getattr(r, "title", ""),
                "year": getattr(r, "year", None),
                "artist": getattr(r, "artist", ""),
            })
        return {
            "labelId": int(label_id),
            "page": int(page),
            "count": len(items),
            "releases": items,
        }
    except Exception as e:
        return {"error": str(e)}


def get_artist_releases(artist_id, page=1):
    """Get paginated releases for an artist."""
    try:
        client = get_client()
        artist = client.artist(int(artist_id))
        releases = artist.releases.page(int(page))
        items = []
        for r in releases:
            items.append({
                "id": r.id,
                "title": getattr(r, "title", ""),
                "year": getattr(r, "year", None),
            })
        return {
            "artistId": int(artist_id),
            "page": int(page),
            "count": len(items),
            "releases": items,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: discogs_lookup.py <type> <query>"}))
        sys.exit(1)

    lookup_type = sys.argv[1]
    query = " ".join(sys.argv[2:])

    dispatch = {
        "artist": search_artist,
        "release": get_release_credits,
        "credits": get_release_credits,
        "label": get_label_info,
        "label-releases": get_label_releases,
        "artist-releases": get_artist_releases,
    }

    fn = dispatch.get(lookup_type)
    if not fn:
        print(json.dumps({"error": f"Unknown type: {lookup_type}. Use: artist, release, credits, label, label-releases, artist-releases"}))
        sys.exit(1)

    try:
        result = fn(query)
    except Exception as e:
        result = {"error": str(e)}
    print(json.dumps(result, indent=2, default=str))
