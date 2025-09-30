-- Initial database setup for ProjectPlanning
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create basic tables for demo purposes (optional)
-- The main data will be stored in Bonita's Business Data Model

-- Example: User management table (for future use)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert demo user (password: admin123)
INSERT INTO users (email, full_name, hashed_password) 
VALUES (
    'admin@example.org', 
    'Demo Admin', 
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW'
) ON CONFLICT (email) DO NOTHING;

-- Example: Project tracking table (for audit/logging)
CREATE TABLE IF NOT EXISTS project_submissions (
    id SERIAL PRIMARY KEY,
    bonita_case_id BIGINT,
    project_name VARCHAR(255) NOT NULL,
    requesting_organization VARCHAR(255) NOT NULL,
    submitted_by VARCHAR(255) NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'submitted'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_project_submissions_case_id ON project_submissions(bonita_case_id);
CREATE INDEX IF NOT EXISTS idx_project_submissions_submitted_at ON project_submissions(submitted_at);
