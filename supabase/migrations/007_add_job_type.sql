-- Migration 007: Add 'job' to opportunity_type enum
ALTER TYPE opportunity_type ADD VALUE IF NOT EXISTS 'job';
