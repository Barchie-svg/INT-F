-- Run this in Supabase SQL Editor

CREATE TABLE employee_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    priority VARCHAR(20) DEFAULT 'Medium',
    due_date TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE employee_tasks ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role only on employee_tasks"
  ON employee_tasks FOR ALL USING (true) WITH CHECK (true);
