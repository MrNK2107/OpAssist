-- Indexes for performance

-- Opportunities: common query patterns
CREATE INDEX idx_opportunities_type ON opportunities(type);
CREATE INDEX idx_opportunities_deadline ON opportunities(deadline);
CREATE INDEX idx_opportunities_source ON opportunities(source);
CREATE INDEX idx_opportunities_difficulty ON opportunities(difficulty);
CREATE INDEX idx_opportunities_is_closed ON opportunities(is_closed);
CREATE INDEX idx_opportunities_created_at ON opportunities(created_at DESC);

-- Bookmarks: lookup by user
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_opportunity_id ON bookmarks(opportunity_id);

-- Applications: lookup by user and status
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_opportunity_id ON applications(opportunity_id);

-- Application events: lookup by application
CREATE INDEX idx_application_events_application_id ON application_events(application_id);

-- Peer activity: lookup by opportunity and recent activity
CREATE INDEX idx_peer_activity_opportunity_id ON peer_activity(opportunity_id);
CREATE INDEX idx_peer_activity_user_id ON peer_activity(user_id);
CREATE INDEX idx_peer_activity_created_at ON peer_activity(created_at DESC);

-- Profiles: lookup by user_id
CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_university ON profiles(university);
