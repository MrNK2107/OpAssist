-- Migration 008: Add new scraper sources to config
INSERT INTO scraper_config (source, enabled) VALUES
    ('internshala_jobs', true),
    ('naukri', true),
    ('adzuna', true),
    ('buddy4study', true),
    ('ambassador', true),
    ('fellowship', true)
ON CONFLICT (source) DO NOTHING;
