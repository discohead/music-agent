-- music-agent knowledge graph schema
-- Location: ~/.music-agent/knowledge.db

-- Core entities accumulated from lookups (artists, labels, releases, tracks, engineers...)
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,              -- mbid, discogs id, or generated
    type TEXT NOT NULL,               -- artist, label, release, track, engineer, genre
    name TEXT NOT NULL,
    metadata JSON,                    -- source-specific structured data
    sources JSON,                     -- which APIs contributed: ["musicbrainz", "discogs", "library"]
    apple_music_id TEXT,              -- persistentID from Apple Music library if matched
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_apple ON entities(apple_music_id);

-- Relationships (the graph edges)
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,           -- released_on, mastered_by, member_of, similar_to,
                                     -- influenced_by, collaborated_with, engineered_by, etc.
    confidence REAL DEFAULT 1.0,      -- 0.0 to 1.0, lower for agent-inferred relations
    attributed_to TEXT,               -- which persona/source asserted this
    metadata JSON,                    -- extra context about the relationship
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id, target_id, relation),
    FOREIGN KEY (source_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);
CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation);

-- Agent annotations - notes, observations, recommendations
CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    persona TEXT,                     -- crate-digger, historian, harmonic-dj, anti-bubble, user
    annotation_type TEXT DEFAULT 'note', -- note, recommendation, context, warning, tag
    content TEXT NOT NULL,
    tags JSON,                        -- ["deep-cut", "microsound", "overlooked"]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_annotations_entity ON annotations(entity_id);
CREATE INDEX IF NOT EXISTS idx_annotations_persona ON annotations(persona);

-- Listening sessions - chronological log of what was played
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    context TEXT,                     -- what the user asked for or was doing
    persona TEXT,                     -- which persona was active
    seed TEXT,                        -- what seeded this session (artist, track, concept)
    metadata JSON                    -- any extra session-level data
);

-- Individual plays within a session
CREATE TABLE IF NOT EXISTS session_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    position INTEGER,                -- order in the session
    track_name TEXT,
    track_artist TEXT,
    track_album TEXT,
    apple_music_id TEXT,             -- persistentID
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    skipped BOOLEAN DEFAULT FALSE,
    skip_position REAL,              -- seconds into track when skipped
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_session_tracks_session ON session_tracks(session_id);

-- Lookup cache - avoid redundant API calls
CREATE TABLE IF NOT EXISTS lookup_cache (
    cache_key TEXT PRIMARY KEY,       -- e.g. "musicbrainz:artist:Mark Fell"
    result JSON NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP             -- NULL = never expires
);

-- Research threads - track multi-step research journeys
CREATE TABLE IF NOT EXISTS research_threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    seed TEXT,                        -- starting point
    persona TEXT,
    steps JSON,                       -- ordered list of lookups and decisions
    findings JSON,                    -- summary of discoveries
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User taste profile - aggregated preferences
CREATE TABLE IF NOT EXISTS taste_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT NOT NULL,        -- genre_affinity, label_affinity, era_preference,
                                     -- bpm_range, duration_preference, skip_pattern
    signal_key TEXT NOT NULL,         -- e.g. "electronic", "Raster-Noton", "2000-2010"
    strength REAL DEFAULT 0.5,        -- 0.0 to 1.0
    evidence JSON,                    -- what data supports this signal
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(signal_type, signal_key)
);
