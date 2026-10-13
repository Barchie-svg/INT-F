-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS employee_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    priority VARCHAR(20) DEFAULT 'Medium',
    due_date TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Grant privileges and disable RLS to match other tables
GRANT ALL PRIVILEGES ON TABLE employee_tasks TO postgres, service_role, anon, authenticated;
ALTER TABLE employee_tasks DISABLE ROW LEVEL SECURITY;
