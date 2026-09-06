-- ==========================================
-- GTD APP - DATABASE SCHEMA (v1)
-- Based on David Allen's Mastering Workflow
-- ==========================================

-- CONTEXTS: "@office", "@home", "@phone" etc.
-- Used in the DO phase: choose by context
CREATE TABLE contexts (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROJECTS: "If multi-step, what's the successful outcome?"
CREATE TABLE projects (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    outcome      TEXT,                    -- the successful outcome
    notes        TEXT,                    -- project plans / support materials
    status       VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | on_hold | completed
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ITEMS: every piece of "stuff" flows through here
CREATE TABLE items (
    id            SERIAL PRIMARY KEY,
    title         VARCHAR(500) NOT NULL,
    notes         TEXT,
    status        VARCHAR(30) NOT NULL DEFAULT 'inbox',
    -- inbox | next_action | scheduled | waiting_for | someday_maybe | reference | done | trash
    project_id    INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    context_id    INTEGER REFERENCES contexts(id) ON DELETE SET NULL,
    due_date      DATE,                   -- "Defer it" to a specific day (Calendar)
    due_time      TIME,                   -- optional time for calendar items
    delegated_to  VARCHAR(200),           -- "Delegate it" -> Waiting For (who?)
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at  TIMESTAMP
);

-- Indexes for the lists the app queries most
CREATE INDEX idx_items_status  ON items(status);
CREATE INDEX idx_items_project ON items(project_id);

-- Default starter contexts (you can add more later in the app)
INSERT INTO contexts (name) VALUES
    ('@office'),
    ('@home'),
    ('@computer'),
    ('@phone'),
    ('@errands'),
    ('@anywhere');