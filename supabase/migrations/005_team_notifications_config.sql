-- Migration 005: Team requests, notifications, and scraper config tables

-- Team requests table for hackathon team finding
CREATE TABLE IF NOT EXISTS team_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    looking_for TEXT[] DEFAULT '{}',
    description TEXT DEFAULT '',
    max_members INT DEFAULT 4,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'matched')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, opportunity_id)
);

-- Notifications table for persistent notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('deadline', 'match', 'team', 'system')),
    urgency TEXT DEFAULT 'info' CHECK (urgency IN ('urgent', 'warning', 'info')),
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scraper configuration table
CREATE TABLE IF NOT EXISTS scraper_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL UNIQUE,
    enabled BOOLEAN DEFAULT true,
    last_run TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE team_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraper_config ENABLE ROW LEVEL SECURITY;

-- Team requests policies
CREATE POLICY "Users can view all open team requests" ON team_requests
    FOR SELECT USING (status = 'open' OR auth.uid() = user_id);

CREATE POLICY "Users can create own team requests" ON team_requests
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own team requests" ON team_requests
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own team requests" ON team_requests
    FOR DELETE USING (auth.uid() = user_id);

-- Notifications policies
CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON notifications
    FOR UPDATE USING (auth.uid() = user_id);

-- Scraper config policies (read for all, write for service role only)
CREATE POLICY "Anyone can read scraper config" ON scraper_config
    FOR SELECT USING (true);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_team_requests_user_id ON team_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_team_requests_opportunity_id ON team_requests(opportunity_id);
CREATE INDEX IF NOT EXISTS idx_team_requests_status ON team_requests(status);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Insert default scraper config
INSERT INTO scraper_config (source, enabled) VALUES
    ('devfolio', true),
    ('unstop', true),
    ('hackerearth', true),
    ('github', true),
    ('devpost', true),
    ('hack2skill', true),
    ('mlh', true)
ON CONFLICT (source) DO NOTHING;
