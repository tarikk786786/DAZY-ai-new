/*
# DAZY Assistant — core schema (memories, conversations, messages, reminders, preferences)

1. Purpose
   This migration creates the database foundation for a personal AI assistant app
   ("DAZY" — a Hinglish-speaking companion with JARVIS-style features). It stores
   everything the assistant needs to remember across sessions: facts about the user,
   the full conversation history, scheduled reminders, and assistant preferences.

2. New Tables
   - `memories`
     Long-term facts the assistant learns about the user (e.g. "user's favourite
     food is biryani", "user's sister is called Ayşe").
     - `id` (uuid, primary key)
     - `category` (text) — grouping label such as "preference", "person", "fact"
     - `key` (text) — short name for the fact, e.g. "favourite_food"
     - `value` (text) — the fact itself
     - `importance` (integer 1-5) — how strongly this fact should be prioritised
     - `created_at`, `updated_at` (timestamps)
     Unique on (category, key) so re-learning a fact updates it instead of duplicating.

   - `conversations`
     One row per chat session (a session groups messages).
     - `id` (uuid, primary key)
     - `title` (text) — auto or user-given session title
     - `started_at`, `last_message_at` (timestamps)

   - `messages`
     Every individual chat message in every conversation.
     - `id` (uuid, primary key)
     - `conversation_id` (uuid, references conversations, cascade delete)
     - `role` (text) — "user" or "assistant"
     - `content` (text) — the message text
     - `emotion` (text, nullable) — detected/expressed emotion for this message
     - `created_at` (timestamp)

   - `reminders`
     Scheduled things the assistant should surface (reminders, briefings).
     - `id` (uuid, primary key)
     - `title` (text) — what to say/show
     - `due_at` (timestamptz) — when it becomes due
     - `repeat` (text) — "once", "daily", "weekly"
     - `completed_at` (timestamptz, nullable) — set when handled
     - `created_at` (timestamp)

   - `preferences`
     Single-row-style key/value store for assistant settings
     (assistant name, user's preferred nickname, voice settings, etc.).
     - `key` (text, primary key)
     - `value` (jsonb)
     - `updated_at` (timestamp)

3. Modified Tables
   None — this is the first migration.

4. Security
   - Row Level Security is ENABLED on all five tables.
   - This app is intentionally single-tenant (one personal assistant for one
     person, no sign-in). Policies therefore allow full CRUD to the anon and
     authenticated roles, which is the documented, intentional design here.
   - Grants: SELECT/INSERT/UPDATE/DELETE on all five tables to anon and
     authenticated, matching what the browser client needs.

5. Notes
   - All ids are uuid with gen_random_uuid() defaults (no sequence grants needed).
   - Indexes added on messages(conversation_id, created_at), memories(category, key),
     reminders(due_at) for query performance.
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