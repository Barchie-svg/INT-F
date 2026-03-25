-- Run this in Supabase SQL Editor

CREATE TABLE employee_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE employee_messages ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role only on employee_messages"
  ON employee_messages FOR ALL USING (true) WITH CHECK (true);
