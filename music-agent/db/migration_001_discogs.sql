-- Migration 001: Add Discogs ID support to entities table
ALTER TABLE entities ADD COLUMN discogs_id TEXT;
CREATE INDEX IF NOT EXISTS idx_entities_discogs ON entities(discogs_id);
