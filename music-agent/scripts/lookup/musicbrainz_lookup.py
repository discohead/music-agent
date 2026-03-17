#!/usr/bin/env python3
"""
musicbrainz_lookup.py - Query MusicBrainz for rich metadata and credits.

Usage:
    python3 scripts/lookup/musicbrainz_lookup.py artist "Mark Fell"
    python3 scripts/lookup/musicbrainz_lookup.py release "Multistability"
    python3 scripts/lookup/musicbrainz_lookup.py recording "Vortex 2"
    python3 scripts/lookup/musicbrainz_lookup.py label "Raster-Noton"
    python3 scripts/lookup/musicbrainz_lookup.py credits <release-mbid>

Requires: pip install musicbrainzngs (auto-installed by setup)
"""

import sys
import json

try:
    import musicbrainzngs as mb
    mb.set_useragent("music-agent", "0.1.0", "https://github.com/music-agent")
    mb.set_rate_limit(limit_or_interval=1.0, new_requests=1)
except ImportError:
    print(json.dumps({"error": "musicbrainzngs not installed. Run: pip3 install musicbrainzngs"}))
    sys.exit(1)


def search_artist(query, limit=10):
    result = mb.search_artists(artist=query, limit=limit)
    artists = []
    for a in result.get("artist-list", []):
        artists.append({
            "id": a.get("id"),
            "name": a.get("name"),
            "sortName": a.get("sort-name"),
            "type": a.get("type"),
            "country": a.get("country"),
            "disambiguation": a.get("disambiguation", ""),
            "score": a.get("ext:score"),
            "tags": [t["name"] for t in a.get("tag-list", [])],
            "beginDate": a.get("life-span", {}).get("begin"),
            "endDate": a.get("life-span", {}).get("end"),
            "ended": a.get("life-span", {}).get("ended", "false"),
        })
    return {"query": query, "count": len(artists), "artists": artists}


def search_release(query, limit=10):
    # TODO: MusicBrainz full-text search treats multi-word queries as a single
    # release title string. "Amber Autechre" searches for a release called
    # "Amber Autechre", not "Amber by Autechre". For artist+release queries,
    # callers should search artist first, get MBID, then use discography.
    result = mb.search_releases(release=query, limit=limit)
    releases = []
    for r in result.get("release-list", []):
        releases.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "status": r.get("status"),
            "date": r.get("date"),
            "country": r.get("country"),
            "score": r.get("ext:score"),
            "artists": [a["artist"]["name"] for a in r.get("artist-credit", []) if "artist" in a],
            "label": [li.get("label", {}).get("name") for li in r.get("label-info-list", [])],
            "catalogNumber": [li.get("catalog-number") for li in r.get("label-info-list", [])],
        })
    return {"query": query, "count": len(releases), "releases": releases}


def search_recording(query, limit=10):
    result = mb.search_recordings(recording=query, limit=limit)
    recordings = []
    for r in result.get("recording-list", []):
        recordings.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "length": r.get("length"),
            "score": r.get("ext:score"),
            "artists": [a["artist"]["name"] for a in r.get("artist-credit", []) if "artist" in a],
            "releases": [rel.get("title") for rel in r.get("release-list", [])],
        })
    return {"query": query, "count": len(recordings), "recordings": recordings}


def search_label(query, limit=10):
    result = mb.search_labels(label=query, limit=limit)
    labels = []
    for l in result.get("label-list", []):
        labels.append({
            "id": l.get("id"),
            "name": l.get("name"),
            "type": l.get("type"),
            "country": l.get("country"),
            "disambiguation": l.get("disambiguation", ""),
            "score": l.get("ext:score"),
            "founded": l.get("life-span", {}).get("begin"),
        })
    return {"query": query, "count": len(labels), "labels": labels}


def get_release_credits(release_mbid):
    """Get full credits for a release including engineers, producers, etc."""
    try:
        result = mb.get_release_by_id(
            release_mbid,
            includes=["artists", "recordings", "artist-credits", "artist-rels", "recording-rels", "release-rels", "labels"]
        )
        release = result.get("release", {})
        
        credits = []
        # Artist relations on the release
        for rel in release.get("artist-relation-list", []):
            credits.append({
                "type": rel.get("type"),
                "artist": rel.get("artist", {}).get("name"),
                "artistId": rel.get("artist", {}).get("id"),
                "attributes": rel.get("attribute-list", []),
            })
        
        # Recording-level credits
        recordings = []
        for medium in release.get("medium-list", []):
            for track in medium.get("track-list", []):
                rec = track.get("recording", {})
                rec_credits = []
                for rel in rec.get("artist-relation-list", []):
                    rec_credits.append({
                        "type": rel.get("type"),
                        "artist": rel.get("artist", {}).get("name"),
                        "artistId": rel.get("artist", {}).get("id"),
                    })
                recordings.append({
                    "position": track.get("position"),
                    "title": rec.get("title"),
                    "length": rec.get("length"),
                    "credits": rec_credits,
                })
        
        return {
            "releaseId": release_mbid,
            "title": release.get("title"),
            "releaseCredits": credits,
            "recordings": recordings,
        }
    except Exception as e:
        return {"error": str(e)}


def get_artist_releases(artist_mbid, limit=50):
    """Get all releases by an artist.

    TODO: Hardcoded limit=50. Prolific artists (e.g. Autechre has 200+ releases
    on MusicBrainz) will be truncated. Consider paginating with offset parameter,
    or at minimum returning a `total` count so the caller knows data is incomplete.

    TODO: Returns duplicate releases (same album, different countries/pressings).
    Consider deduplicating by release-group MBID to show unique albums only.
    """
    try:
        result = mb.browse_releases(artist=artist_mbid, limit=limit, includes=["labels"])
        releases = []
        for r in result.get("release-list", []):
            releases.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "date": r.get("date"),
                "status": r.get("status"),
                "country": r.get("country"),
                "labels": [li.get("label", {}).get("name") for li in r.get("label-info-list", [])],
            })
        return {
            "artistId": artist_mbid,
            "count": len(releases),
            "releases": sorted(releases, key=lambda x: x.get("date") or "9999")
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: musicbrainz_lookup.py <type> <query>"}))
        sys.exit(1)
    
    lookup_type = sys.argv[1]
    query = " ".join(sys.argv[2:])
    
    dispatch = {
        "artist": search_artist,
        "release": search_release,
        "recording": search_recording,
        "label": search_label,
        "credits": get_release_credits,
        "discography": get_artist_releases,
    }
    
    fn = dispatch.get(lookup_type)
    if not fn:
        print(json.dumps({"error": f"Unknown type: {lookup_type}. Use: artist, release, recording, label, credits, discography"}))
        sys.exit(1)
    
    try:
        result = fn(query)
    except Exception as e:
        result = {"error": str(e)}
    print(json.dumps(result, indent=2, default=str))
