-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS employee_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Grant privileges and disable RLS to match other tables
GRANT ALL PRIVILEGES ON TABLE employee_messages TO postgres, service_role, anon, authenticated;
ALTER TABLE employee_messages DISABLE ROW LEVEL SECURITY;
