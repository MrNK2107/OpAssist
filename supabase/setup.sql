-- Run this in Supabase SQL Editor (Dashboard > SQL Editor > New query)

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE opportunity_type AS ENUM ('hackathon', 'internship', 'scholarship', 'oss', 'ambassador', 'event');
CREATE TYPE difficulty_level AS ENUM ('beginner', 'intermediate', 'advanced');
CREATE TYPE application_status AS ENUM ('saved', 'preparing', 'applied', 'interviewing', 'offered', 'rejected');
CREATE TYPE activity_action AS ENUM ('bookmarked', 'applied', 'won');

-- Universities table
CREATE TABLE universities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    domain TEXT UNIQUE,
    academic_calendar_json JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Profiles table
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL DEFAULT '',
    bio TEXT DEFAULT '',
    university TEXT DEFAULT '',
    year INT DEFAULT 1,
    avatar_url TEXT DEFAULT '',
    skills TEXT[] DEFAULT '{}',
    interests TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Opportunities table
CREATE TABLE opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    type opportunity_type NOT NULL DEFAULT 'hackathon',
    url TEXT UNIQUE,
    source TEXT DEFAULT '',
    description TEXT DEFAULT '',
    organizer TEXT DEFAULT '',
    start_date DATE,
    end_date DATE,
    deadline DATE,
    location TEXT DEFAULT '',
    is_offline BOOL DEFAULT false,
    image_url TEXT DEFAULT '',
    prize TEXT DEFAULT '',
    tags TEXT[] DEFAULT '{}',
    difficulty difficulty_level DEFAULT 'beginner',
    is_closed BOOL DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bookmarks table
CREATE TABLE bookmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, opportunity_id)
);

-- Applications table
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    status application_status NOT NULL DEFAULT 'saved',
    applied_at TIMESTAMPTZ,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, opportunity_id)
);

-- Application events table
CREATE TABLE application_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Peer activity table
CREATE TABLE peer_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    opportunity_id UUID NOT NULL REFERENCES opportunities(id) ON DELETE CASCADE,
    action activity_action NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Indexes
CREATE INDEX idx_opportunities_type ON opportunities(type);
CREATE INDEX idx_opportunities_deadline ON opportunities(deadline);
CREATE INDEX idx_opportunities_source ON opportunities(source);
CREATE INDEX idx_opportunities_difficulty ON opportunities(difficulty);
CREATE INDEX idx_opportunities_is_closed ON opportunities(is_closed);
CREATE INDEX idx_opportunities_created_at ON opportunities(created_at DESC);
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_opportunity_id ON bookmarks(opportunity_id);
CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_opportunity_id ON applications(opportunity_id);
CREATE INDEX idx_application_events_application_id ON application_events(application_id);
CREATE INDEX idx_peer_activity_opportunity_id ON peer_activity(opportunity_id);
CREATE INDEX idx_peer_activity_user_id ON peer_activity(user_id);
CREATE INDEX idx_peer_activity_created_at ON peer_activity(created_at DESC);
CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_university ON profiles(university);

-- RLS Policies
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE application_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE peer_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE universities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Profiles are viewable by everyone" ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can insert their own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own profile" ON profiles FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Opportunities are viewable by everyone" ON opportunities FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert opportunities" ON opportunities FOR INSERT WITH CHECK (auth.role() = 'authenticated');
CREATE POLICY "Authenticated users can update opportunities" ON opportunities FOR UPDATE USING (auth.role() = 'authenticated');

CREATE POLICY "Users can view their own bookmarks" ON bookmarks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own bookmarks" ON bookmarks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete their own bookmarks" ON bookmarks FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own applications" ON applications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own applications" ON applications FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update their own applications" ON applications FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own applications" ON applications FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own application events" ON application_events
    FOR SELECT USING (EXISTS (SELECT 1 FROM applications WHERE applications.id = application_events.application_id AND applications.user_id = auth.uid()));
CREATE POLICY "Users can insert events for their own applications" ON application_events
    FOR INSERT WITH CHECK (EXISTS (SELECT 1 FROM applications WHERE applications.id = application_events.application_id AND applications.user_id = auth.uid()));

CREATE POLICY "Peer activity is viewable by everyone" ON peer_activity FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert peer activity" ON peer_activity FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Universities are viewable by everyone" ON universities FOR SELECT USING (true);
