PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. Host（主持人）—— 每讨论独立，不跨讨论复用
-- ============================================================
CREATE TABLE IF NOT EXISTS host (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    system_prompt TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- 2. Discussion（讨论会话）
-- ============================================================
CREATE TABLE IF NOT EXISTS discussion (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    topic         TEXT    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'pending'
                         CHECK(status IN ('pending','active','paused','completed')),
    max_rounds    INTEGER NOT NULL DEFAULT 5,
    current_round INTEGER NOT NULL DEFAULT 0,
    host_id       INTEGER NOT NULL REFERENCES host(id) ON DELETE CASCADE,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- 3. Guest（嘉宾模板库）—— 全局动态模板，可跨讨论复用
-- ============================================================
CREATE TABLE IF NOT EXISTS guest (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    avatar        TEXT,
    persona       TEXT    NOT NULL,
    system_prompt TEXT    NOT NULL,
    speak_style   TEXT,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- 4. DiscussionGuest（讨论-嘉宾关联）—— M:N 联结
-- ============================================================
CREATE TABLE IF NOT EXISTS discussion_guest (
    discussion_id   INTEGER NOT NULL REFERENCES discussion(id) ON DELETE CASCADE,
    guest_id        INTEGER NOT NULL REFERENCES guest(id) ON DELETE CASCADE,
    stance_override TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    UNIQUE(discussion_id, guest_id)
);

-- ============================================================
-- 5. Message（消息）—— 方案B：分列FK，二选一约束
-- ============================================================
CREATE TABLE IF NOT EXISTS message (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id INTEGER NOT NULL REFERENCES discussion(id) ON DELETE CASCADE,
    host_id       INTEGER REFERENCES host(id) ON DELETE SET NULL,
    guest_id      INTEGER REFERENCES guest(id) ON DELETE SET NULL,
    role          TEXT    NOT NULL CHECK(role IN ('host','guest','system')),
    content       TEXT    NOT NULL,
    seq_num       INTEGER NOT NULL,
    token_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    CHECK (host_id IS NOT NULL OR guest_id IS NOT NULL)
);

-- ============================================================
-- 6. Opinion（观点快照）—— 1:0..1 关联 Message
-- ============================================================
CREATE TABLE IF NOT EXISTS opinion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL UNIQUE REFERENCES message(id) ON DELETE CASCADE,
    stance_summary  TEXT    NOT NULL,
    category        TEXT    NOT NULL CHECK(category IN ('consensus','disagreement','neutral')),
    confidence      REAL,
    evidence        TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- 索引
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_message_discussion_seq ON message(discussion_id, seq_num);
CREATE INDEX IF NOT EXISTS idx_opinion_message ON opinion(message_id);
