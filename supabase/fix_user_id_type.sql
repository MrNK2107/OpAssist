-- Drop RLS policies that depend on user_id
DROP POLICY IF EXISTS "Users can insert their own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update their own profile" ON profiles;
DROP POLICY IF EXISTS "Users can view their own bookmarks" ON bookmarks;
DROP POLICY IF EXISTS "Users can insert their own bookmarks" ON bookmarks;
DROP POLICY IF EXISTS "Users can delete their own bookmarks" ON bookmarks;
DROP POLICY IF EXISTS "Users can view their own applications" ON applications;
DROP POLICY IF EXISTS "Users can insert their own applications" ON applications;
DROP POLICY IF EXISTS "Users can update their own applications" ON applications;
DROP POLICY IF EXISTS "Users can delete their own applications" ON applications;
DROP POLICY IF EXISTS "Users can view their own application events" ON application_events;
DROP POLICY IF EXISTS "Users can insert events for their own applications" ON application_events;
DROP POLICY IF EXISTS "Authenticated users can insert peer activity" ON peer_activity;

-- Alter column types (Firebase UIDs are strings, not UUIDs)
ALTER TABLE profiles ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE bookmarks ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE applications ALTER COLUMN user_id TYPE TEXT;
ALTER TABLE peer_activity ALTER COLUMN user_id TYPE TEXT;

-- Recreate policies (using TEXT comparison now)
CREATE POLICY "Users can insert their own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own bookmarks" ON bookmarks
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own bookmarks" ON bookmarks
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own bookmarks" ON bookmarks
    FOR DELETE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own applications" ON applications
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own applications" ON applications
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own applications" ON applications
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own applications" ON applications
    FOR DELETE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can view their own application events" ON application_events
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM applications
        WHERE applications.id = application_events.application_id
        AND applications.user_id = auth.uid()::text
    ));

CREATE POLICY "Users can insert events for their own applications" ON application_events
    FOR INSERT WITH CHECK (EXISTS (
        SELECT 1 FROM applications
        WHERE applications.id = application_events.application_id
        AND applications.user_id = auth.uid()::text
    ));

CREATE POLICY "Authenticated users can insert peer activity" ON peer_activity
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);
