-- =============================================================================
-- AESA Database Schema
-- AI Engineering Study Assistant - PostgreSQL Initialization Script
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Subjects table (e.g., MATH101, PHYS102)
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,  -- Format: [A-Z]{4}[0-9]{3}
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7),  -- Hex color code
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, code)
);

-- Chapters within subjects
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    chapter_number INT NOT NULL,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chapter progress tracking
CREATE TABLE chapter_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    progress_type VARCHAR(50) NOT NULL,  -- reading, practice, revision
    progress_percent FLOAT DEFAULT 0,
    last_activity TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,  -- university, study, revision, practice, etc.
    duration_minutes INT NOT NULL,
    priority INT DEFAULT 50,  -- 0-100 scale
    deadline TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Time blocks (scheduled activities)
CREATE TABLE time_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    block_type VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    is_fixed BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Revision schedule (spaced repetition)
CREATE TABLE revision_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    interval_days INT NOT NULL,  -- 1, 3, 7, 14, 30
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- Study Tracking Tables
-- =============================================================================

-- Study sessions
CREATE TABLE study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_minutes INT,
    is_deep_work BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Active timer (one per user)
CREATE TABLE active_timer (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    started_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Study goals
CREATE TABLE study_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID,  -- References goal_categories
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_value FLOAT,
    current_value FLOAT DEFAULT 0,
    unit VARCHAR(50),  -- hours, chapters, problems, etc.
    deadline DATE,
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, abandoned
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Goal categories
CREATE TABLE goal_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add foreign key for study_goals category
ALTER TABLE study_goals 
ADD CONSTRAINT fk_goal_category 
FOREIGN KEY (category_id) REFERENCES goal_categories(id) ON DELETE SET NULL;

-- Daily study statistics (aggregated)
CREATE TABLE daily_study_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stat_date DATE NOT NULL,
    total_study_minutes INT DEFAULT 0,
    deep_work_minutes INT DEFAULT 0,
    tasks_completed INT DEFAULT 0,
    subjects_studied INT DEFAULT 0,
    streak_days INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, stat_date)
);

-- =============================================================================
-- AI Memory and Guidelines Tables
-- =============================================================================

-- AI memory (key-value storage for user preferences)
CREATE TABLE ai_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, key)
);

-- AI guidelines (user-defined behavior rules)
CREATE TABLE ai_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    guideline TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- User Preferences and Configuration
-- =============================================================================

-- User preferences (daily routine, study constraints)
CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    sleep_start TIME DEFAULT '23:00',
    sleep_end TIME DEFAULT '06:00',
    wake_routine_mins INT DEFAULT 30,
    breakfast_mins INT DEFAULT 30,
    lunch_time TIME DEFAULT '13:00',
    dinner_time TIME DEFAULT '19:30',
    max_study_block_mins INT DEFAULT 90,
    min_break_after_study INT DEFAULT 15,
    preferences JSONB,  -- Additional preferences as JSON
    updated_at TIMESTAMP DEFAULT NOW()
);

-- KU Timetable configuration
CREATE TABLE ku_timetable (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    day_of_week INT NOT NULL,  -- 0=Sunday, 1=Monday, etc.
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(50),
    class_type VARCHAR(20) DEFAULT 'lecture',  -- lecture, lab
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- Notifications Table
-- =============================================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- reminder, suggestion, achievement, warning, motivation
    title VARCHAR(255) NOT NULL,
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    scheduled_for TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- System Logs Table
-- =============================================================================

CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level VARCHAR(20) NOT NULL,  -- error, warning, info, debug
    message TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Tasks indexes
CREATE INDEX idx_tasks_user_deadline ON tasks(user_id, deadline);
CREATE INDEX idx_tasks_user_type ON tasks(user_id, task_type);
CREATE INDEX idx_tasks_user_priority ON tasks(user_id, priority DESC);
CREATE INDEX idx_tasks_user_completed ON tasks(user_id, is_completed);

-- Time blocks indexes
CREATE INDEX idx_time_blocks_user_time ON time_blocks(user_id, start_time);
CREATE INDEX idx_time_blocks_user_date ON time_blocks(user_id, DATE(start_time));

-- Study sessions indexes
CREATE INDEX idx_study_sessions_user_date ON study_sessions(user_id, started_at);
CREATE INDEX idx_study_sessions_subject ON study_sessions(subject_id);

-- Notifications indexes
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_user_scheduled ON notifications(user_id, scheduled_for);

-- AI memory index
CREATE INDEX idx_ai_memory_user_key ON ai_memory(user_id, key);

-- Revision schedule index
CREATE INDEX idx_revision_schedule_date ON revision_schedule(scheduled_date, is_completed);

-- KU timetable index
CREATE INDEX idx_ku_timetable_user_day ON ku_timetable(user_id, day_of_week);

-- =============================================================================
-- Triggers
-- =============================================================================

-- Function to update timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update_timestamp trigger to relevant tables
CREATE TRIGGER tasks_updated
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER study_goals_updated
    BEFORE UPDATE ON study_goals
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER users_updated
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER ai_memory_updated
    BEFORE UPDATE ON ai_memory
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER user_preferences_updated
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER daily_study_stats_updated
    BEFORE UPDATE ON daily_study_stats
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Function to auto-calculate session duration and deep work flag
CREATE OR REPLACE FUNCTION calculate_session_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
        NEW.duration_minutes = EXTRACT(EPOCH FROM (NEW.ended_at - NEW.started_at)) / 60;
        NEW.is_deep_work = NEW.duration_minutes >= 90;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER session_duration
    BEFORE UPDATE ON study_sessions
    FOR EACH ROW EXECUTE FUNCTION calculate_session_duration();

-- Function to schedule revisions when chapter is completed
CREATE OR REPLACE FUNCTION schedule_chapter_revisions()
RETURNS TRIGGER AS $$
DECLARE
    intervals INT[] := ARRAY[1, 3, 7, 14, 30];
    interval_val INT;
BEGIN
    IF NEW.is_completed = TRUE AND OLD.is_completed = FALSE THEN
        NEW.completed_at = NOW();
        
        -- Schedule revisions at spaced intervals
        FOREACH interval_val IN ARRAY intervals
        LOOP
            INSERT INTO revision_schedule (chapter_id, scheduled_date, interval_days)
            VALUES (NEW.id, CURRENT_DATE + interval_val, interval_val)
            ON CONFLICT DO NOTHING;
        END LOOP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER chapter_completion_revisions
    BEFORE UPDATE ON chapters
    FOR EACH ROW EXECUTE FUNCTION schedule_chapter_revisions();

-- Function to update daily stats when session ends
CREATE OR REPLACE FUNCTION update_daily_stats_on_session()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL AND OLD.ended_at IS NULL THEN
        INSERT INTO daily_study_stats (user_id, stat_date, total_study_minutes, deep_work_minutes)
        VALUES (
            NEW.user_id,
            DATE(NEW.started_at),
            NEW.duration_minutes,
            CASE WHEN NEW.is_deep_work THEN NEW.duration_minutes ELSE 0 END
        )
        ON CONFLICT (user_id, stat_date) DO UPDATE SET
            total_study_minutes = daily_study_stats.total_study_minutes + NEW.duration_minutes,
            deep_work_minutes = daily_study_stats.deep_work_minutes + 
                CASE WHEN NEW.is_deep_work THEN NEW.duration_minutes ELSE 0 END,
            updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER session_stats_update
    AFTER UPDATE ON study_sessions
    FOR EACH ROW EXECUTE FUNCTION update_daily_stats_on_session();

-- =============================================================================
-- Default Data (Optional - for development)
-- =============================================================================

-- Insert a default user for development
INSERT INTO users (id, email, name) 
VALUES ('00000000-0000-0000-0000-000000000001', 'dev@aesa.local', 'Development User')
ON CONFLICT (email) DO NOTHING;

-- Insert default preferences for dev user
INSERT INTO user_preferences (user_id)
VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (user_id) DO NOTHING;
