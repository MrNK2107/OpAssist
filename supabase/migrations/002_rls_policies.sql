-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE application_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE peer_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE universities ENABLE ROW LEVEL SECURITY;

-- Profiles: users can read all profiles, but only update their own
CREATE POLICY "Profiles are viewable by everyone" ON profiles
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Opportunities: public read, authenticated write
CREATE POLICY "Opportunities are viewable by everyone" ON opportunities
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can insert opportunities" ON opportunities
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can update opportunities" ON opportunities
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Bookmarks: users can only see/modify their own
CREATE POLICY "Users can view their own bookmarks" ON bookmarks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own bookmarks" ON bookmarks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own bookmarks" ON bookmarks
    FOR DELETE USING (auth.uid() = user_id);

-- Applications: users can only see/modify their own
CREATE POLICY "Users can view their own applications" ON applications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own applications" ON applications
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own applications" ON applications
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own applications" ON applications
    FOR DELETE USING (auth.uid() = user_id);

-- Application events: users can see events for their own applications
CREATE POLICY "Users can view their own application events" ON application_events
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications
            WHERE applications.id = application_events.application_id
            AND applications.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert events for their own applications" ON application_events
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM applications
            WHERE applications.id = application_events.application_id
            AND applications.user_id = auth.uid()
        )
    );

-- Peer activity: viewable by everyone, insertable by authenticated
CREATE POLICY "Peer activity is viewable by everyone" ON peer_activity
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can insert peer activity" ON peer_activity
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Universities: public read
CREATE POLICY "Universities are viewable by everyone" ON universities
    FOR SELECT USING (true);
