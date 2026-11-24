/*
# DAZY Assistant — core schema (memories, conversations, messages, reminders, preferences)

1. Purpose
   Database foundation for the DAZY web personal assistant: stores long-term facts
   about the user, full chat history, scheduled reminders, and settings.

2. New Tables
   - `memories` — long-term facts (category, key, value, importance 1-5);
     unique on (category, key) so re-learning updates instead of duplicating.
   - `conversations` — one row per chat session.
   - `messages` — every chat message (role user/assistant, content, emotion),
     linked to conversations with cascade delete.
   - `reminders` — scheduled items (title, due_at, repeat once/daily/weekly,
     completed_at when handled).
   - `preferences` — key/value JSONB settings store.

3. Security
   - RLS ENABLED on all five tables.
   - Intentionally single-tenant (one personal assistant, no sign-in): full CRUD
     granted to anon + authenticated with documented USING (true) policies.

4. Notes
   - uuid primary keys with gen_random_uuid() (no sequence grants needed).
   - Indexes: messages(conversation_id, created_at), memories(category, key),
     reminders(due_at) partial on uncompleted.
*/

CREATE TABLE IF NOT EXISTS memories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  category text NOT NULL DEFAULT 'fact',
  key text NOT NULL,
  value text NOT NULL,
  importance integer NOT NULL DEFAULT 1 CHECK (importance BETWEEN 1 AND 5),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (category, key)
);

CREATE TABLE IF NOT EXISTS conversations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL DEFAULT 'New conversation',
  started_at timestamptz NOT NULL DEFAULT now(),
  last_message_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS messages (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('user', 'assistant')),
  content text NOT NULL,
  emotion text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reminders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  due_at timestamptz NOT NULL,
  repeat text NOT NULL DEFAULT 'once' CHECK (repeat IN ('once', 'daily', 'weekly')),
  completed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS preferences (
  key text PRIMARY KEY,
  value jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_memories_category_key ON memories(category, key);
CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(due_at) WHERE completed_at IS NULL;

ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE preferences ENABLE ROW LEVEL SECURITY;

GRANT SELECT, INSERT, UPDATE, DELETE ON memories TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON conversations TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON messages TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON reminders TO anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON preferences TO anon, authenticated;

DROP POLICY IF EXISTS "memories_public_read" ON memories;
CREATE POLICY "memories_public_read" ON memories FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "memories_public_insert" ON memories;
CREATE POLICY "memories_public_insert" ON memories FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "memories_public_update" ON memories;
CREATE POLICY "memories_public_update" ON memories FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "memories_public_delete" ON memories;
CREATE POLICY "memories_public_delete" ON memories FOR DELETE TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "conversations_public_read" ON conversations;
CREATE POLICY "conversations_public_read" ON conversations FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "conversations_public_insert" ON conversations;
CREATE POLICY "conversations_public_insert" ON conversations FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "conversations_public_update" ON conversations;
CREATE POLICY "conversations_public_update" ON conversations FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "conversations_public_delete" ON conversations;
CREATE POLICY "conversations_public_delete" ON conversations FOR DELETE TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "messages_public_read" ON messages;
CREATE POLICY "messages_public_read" ON messages FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "messages_public_insert" ON messages;
CREATE POLICY "messages_public_insert" ON messages FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "messages_public_update" ON messages;
CREATE POLICY "messages_public_update" ON messages FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "messages_public_delete" ON messages;
CREATE POLICY "messages_public_delete" ON messages FOR DELETE TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "reminders_public_read" ON reminders;
CREATE POLICY "reminders_public_read" ON reminders FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "reminders_public_insert" ON reminders;
CREATE POLICY "reminders_public_insert" ON reminders FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "reminders_public_update" ON reminders;
CREATE POLICY "reminders_public_update" ON reminders FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "reminders_public_delete" ON reminders;
CREATE POLICY "reminders_public_delete" ON reminders FOR DELETE TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "preferences_public_read" ON preferences;
CREATE POLICY "preferences_public_read" ON preferences FOR SELECT TO anon, authenticated USING (true);
DROP POLICY IF EXISTS "preferences_public_insert" ON preferences;
CREATE POLICY "preferences_public_insert" ON preferences FOR INSERT TO anon, authenticated WITH CHECK (true);
DROP POLICY IF EXISTS "preferences_public_update" ON preferences;
CREATE POLICY "preferences_public_update" ON preferences FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
DROP POLICY IF EXISTS "preferences_public_delete" ON preferences;
CREATE POLICY "preferences_public_delete" ON preferences FOR DELETE TO anon, authenticated USING (true);