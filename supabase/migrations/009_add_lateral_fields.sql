-- Migration 009: Add fields for lateral/experienced roles and enriched job data
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS experience_min INTEGER;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS experience_max INTEGER;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS salary_currency TEXT DEFAULT 'INR';
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS employment_type TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS remote BOOLEAN DEFAULT false;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS application_deadline TEXT;

-- Index for experience-range queries
CREATE INDEX IF NOT EXISTS idx_opportunities_experience ON opportunities(experience_min, experience_max);
CREATE INDEX IF NOT EXISTS idx_opportunities_employment_type ON opportunities(employment_type);
CREATE INDEX IF NOT EXISTS idx_opportunities_remote ON opportunities(remote);
