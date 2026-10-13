-- ============================================================
-- PASTE THIS INTO SUPABASE SQL EDITOR AND CLICK RUN
-- Project: Tech Africa IT Secure Access System
-- ============================================================

-- 1. Create employee_tasks table
CREATE TABLE IF NOT EXISTS employee_tasks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    title        VARCHAR(255) NOT NULL,
    priority     VARCHAR(20) DEFAULT 'Medium',
    due_date     TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create employee_messages table
CREATE TABLE IF NOT EXISTS employee_messages (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id    UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    receiver_id  UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    is_read      BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Compatibility view for profiles (in case any query references profiles)
CREATE OR REPLACE VIEW profiles AS SELECT * FROM employees;

-- 4. Permissions & RLS
GRANT ALL PRIVILEGES ON TABLE employee_tasks TO postgres, service_role, anon, authenticated;
GRANT ALL PRIVILEGES ON TABLE employee_messages TO postgres, service_role, anon, authenticated;
GRANT ALL PRIVILEGES ON profiles TO postgres, service_role, anon, authenticated;

ALTER TABLE employee_tasks DISABLE ROW LEVEL SECURITY;
ALTER TABLE employee_messages DISABLE ROW LEVEL SECURITY;
