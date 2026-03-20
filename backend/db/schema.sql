-- CMU Cafeteria initial PostgreSQL schema
-- Roles: Student, Apartment Resident, Staff, Admin

CREATE TABLE IF NOT EXISTS roles (
    id SMALLSERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    student_number VARCHAR(32) UNIQUE,
    username VARCHAR(64) UNIQUE,
    last_name VARCHAR(120),
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_login_identity_check CHECK (
        (student_number IS NOT NULL AND last_name IS NOT NULL)
        OR username IS NOT NULL
    )
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS token_periods (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT token_periods_date_check CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS user_token_balances (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_period_id BIGINT NOT NULL REFERENCES token_periods(id) ON DELETE CASCADE,
    lunches_remaining SMALLINT NOT NULL DEFAULT 0,
    suppers_remaining SMALLINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, token_period_id),
    CONSTRAINT token_balance_nonnegative CHECK (
        lunches_remaining >= 0 AND suppers_remaining >= 0
    )
);

CREATE TABLE IF NOT EXISTS meal_days (
    id BIGSERIAL PRIMARY KEY,
    service_date DATE NOT NULL UNIQUE,
    is_open BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS meals (
    id BIGSERIAL PRIMARY KEY,
    meal_day_id BIGINT NOT NULL REFERENCES meal_days(id) ON DELETE CASCADE,
    meal_type VARCHAR(16) NOT NULL,
    title VARCHAR(200),
    details TEXT,
    capacity INTEGER,
    is_signup_allowed BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (meal_day_id, meal_type),
    CONSTRAINT meals_type_check CHECK (meal_type IN ('Breakfast', 'Lunch', 'Supper', 'Snack'))
);

CREATE TABLE IF NOT EXISTS meal_signups (
    id BIGSERIAL PRIMARY KEY,
    meal_id BIGINT NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    signed_up_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    UNIQUE (meal_id, user_id),
    CONSTRAINT meal_signups_status_check CHECK (status IN ('active', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS menu_uploads (
    id BIGSERIAL PRIMARY KEY,
    uploaded_by BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    source_filename VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    parsed_success BOOLEAN NOT NULL DEFAULT FALSE,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS password_change_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meal_days_service_date ON meal_days(service_date);
CREATE INDEX IF NOT EXISTS idx_meals_day_type ON meals(meal_day_id, meal_type);
CREATE INDEX IF NOT EXISTS idx_signups_meal ON meal_signups(meal_id);
CREATE INDEX IF NOT EXISTS idx_signups_user ON meal_signups(user_id);

INSERT INTO roles(name)
VALUES ('Student'), ('Apartment Resident'), ('Staff'), ('Admin')
ON CONFLICT (name) DO NOTHING;

-- Use Alembic migration + startup seed logic for default user credentials.
