--  Creating two dimention tables for our star schema: dim_branch and dim_data


-- fact table reference these two tables using foreign keys.
-- Branch dimension
CREATE TABLE IF NOT EXISTS dim_branch (
    branch_key BIGSERIAL PRIMARY KEY,
    branch_id VARCHAR(20) NOT NULL UNIQUE,
    branch_name VARCHAR(150) NOT NULL,
    region VARCHAR(50),
    branch_type VARCHAR(50),
    open_date DATE,
    active_flag CHAR(1)
);

-- Date dimension
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(15) NOT NULL,
    day_of_month INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter_number INTEGER NOT NULL,
    year_number INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);



-- now we create three fact tables to store validated transactions, member visits, and staffing data.



-- Transaction fact table
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_key BIGSERIAL PRIMARY KEY,
    transaction_id VARCHAR(30) NOT NULL UNIQUE,
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    transaction_timestamp TIMESTAMP NOT NULL,
    transaction_type VARCHAR(50),
    channel VARCHAR(50),
    amount NUMERIC(12,2),
    processing_seconds INTEGER,
    status VARCHAR(30)
);

-- Member visits fact table
CREATE TABLE IF NOT EXISTS fact_member_visits (
    visit_key BIGSERIAL PRIMARY KEY,
    visit_id VARCHAR(30) NOT NULL UNIQUE,
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    arrival_timestamp TIMESTAMP NOT NULL,
    service_start_timestamp TIMESTAMP NOT NULL,
    service_end_timestamp TIMESTAMP NOT NULL,
    service_type VARCHAR(50),
    outcome VARCHAR(50),
    wait_minutes NUMERIC(10,2),
    service_minutes NUMERIC(10,2)
);

-- Staffing fact table
CREATE TABLE IF NOT EXISTS fact_staffing (
    staffing_key BIGSERIAL PRIMARY KEY,
    branch_key BIGINT NOT NULL REFERENCES dim_branch(branch_key),
    date_key INTEGER NOT NULL REFERENCES dim_date(date_key),
    scheduled_employees INTEGER,
    actual_employees INTEGER,
    employee_hours NUMERIC(10,2),
    UNIQUE (branch_key, date_key)
);
