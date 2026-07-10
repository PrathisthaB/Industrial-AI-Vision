-- ============================================================================
-- AI-Powered Industrial Safety Monitoring Platform - Database Schema
-- Engine: SQLite
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Users: authentication + role based access
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'operator',   -- admin | operator | viewer
    full_name       TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at   TEXT
);

-- ----------------------------------------------------------------------------
-- Cameras: logical sources (webcam / uploaded video / CCTV stream)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cameras (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    location        TEXT,
    source_type     TEXT NOT NULL DEFAULT 'upload',      -- webcam | upload | cctv
    source_path     TEXT,                                 -- device index, file path, or RTSP URL
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
-- Detection sessions: one row per processing run (webcam session / video job)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id       INTEGER REFERENCES cameras(id) ON DELETE SET NULL,
    source_type     TEXT NOT NULL,
    source_label    TEXT,
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at        TEXT,
    frames_processed INTEGER NOT NULL DEFAULT 0,
    workers_detected  INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'running'       -- running | completed | failed
);

-- ----------------------------------------------------------------------------
-- Violations: every recorded PPE non-compliance event
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS violations (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    camera_id         INTEGER REFERENCES cameras(id) ON DELETE SET NULL,
    violation_type    TEXT NOT NULL,      -- missing_helmet | missing_vest | missing_boots
    confidence        REAL NOT NULL,
    severity          TEXT NOT NULL DEFAULT 'medium',   -- low | medium | high | critical
    screenshot_path   TEXT,
    compliance_score  REAL,
    worker_bbox       TEXT,               -- JSON encoded bounding box
    timestamp         TEXT NOT NULL DEFAULT (datetime('now')),
    status            TEXT NOT NULL DEFAULT 'open'       -- open | reviewed | resolved
);

CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_violations_type ON violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_violations_camera ON violations(camera_id);

-- ----------------------------------------------------------------------------
-- Incident reports: generated documents summarizing one or more violations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS incident_reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_code   TEXT NOT NULL UNIQUE,
    violation_id    INTEGER REFERENCES violations(id) ON DELETE CASCADE,
    severity        TEXT NOT NULL,
    recommended_action TEXT,
    file_path       TEXT,
    generated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------------
-- Daily aggregate stats: pre-computed rollups powering the analytics dashboard
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_stats (
    date                TEXT PRIMARY KEY,     -- YYYY-MM-DD
    total_workers       INTEGER NOT NULL DEFAULT 0,
    total_violations    INTEGER NOT NULL DEFAULT 0,
    missing_helmet      INTEGER NOT NULL DEFAULT 0,
    missing_vest        INTEGER NOT NULL DEFAULT 0,
    missing_boots       INTEGER NOT NULL DEFAULT 0,
    helmet_compliance   REAL NOT NULL DEFAULT 100,
    vest_compliance     REAL NOT NULL DEFAULT 100,
    boot_compliance     REAL NOT NULL DEFAULT 100
);

-- ----------------------------------------------------------------------------
-- Seed default camera so the dashboard has something to show out of the box
-- ----------------------------------------------------------------------------
INSERT OR IGNORE INTO cameras (id, name, location, source_type, source_path, is_active)
VALUES (1, 'Main Entrance Cam', 'Plant Floor - Gate A', 'webcam', '0', 1);
