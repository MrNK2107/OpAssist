-- Migration 006: Add members column to team_requests for join functionality

ALTER TABLE team_requests ADD COLUMN IF NOT EXISTS members TEXT[] DEFAULT '{}';

-- Update RLS policy to allow members to update the team request (for joining)
CREATE POLICY "Team members can view team requests" ON team_requests
    FOR SELECT USING (
        status = 'open'
        OR auth.uid() = user_id
        OR auth.uid() = ANY(members)
    );
