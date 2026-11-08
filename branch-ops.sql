
-- here we are creating staging tables for the branch operations data. These tables will be used to load raw data before it is transformed and loaded into the final destination tables.

CREATE TABLE IF NOT EXISTS stg_branches (
    staging_id BIGSERIAL PRIMARY KEY,
    branch_id TEXT,
    branch_name TEXT,
    region TEXT,
    branch_type TEXT,
    open_date TEXT,
    active_flag TEXT,
    pipeline_run_id TEXT,
    source_file_name TEXT,
    source_row_number INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_hash TEXT
);

CREATE TABLE IF NOT EXISTS stg_transactions (
    staging_id BIGSERIAL PRIMARY KEY,
    transaction_id TEXT,
    branch_id TEXT,
    transaction_timestamp TEXT,
    transaction_type TEXT,
    channel TEXT,
    amount TEXT,
    processing_seconds TEXT,
    status TEXT,
    pipeline_run_id TEXT,
    source_file_name TEXT,
    source_row_number INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_hash TEXT
);

CREATE TABLE IF NOT EXISTS stg_member_visits (
    staging_id BIGSERIAL PRIMARY KEY,
    visit_id TEXT,
    branch_id TEXT,
    arrival_timestamp TEXT,
    service_start_timestamp TEXT,
    service_end_timestamp TEXT,
    service_type TEXT,
    outcome TEXT,
    pipeline_run_id TEXT,
    source_file_name TEXT,
    source_row_number INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_hash TEXT
);

CREATE TABLE IF NOT EXISTS stg_staffing (
    staging_id BIGSERIAL PRIMARY KEY,
    branch_id TEXT,
    work_date TEXT,
    scheduled_employees TEXT,
    actual_employees TEXT,
    employee_hours TEXT,
    pipeline_run_id TEXT,
    source_file_name TEXT,
    source_row_number INTEGER,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_hash TEXT
);


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'stg_%'
ORDER BY table_name;




-- Track ETL pipeline executions
CREATE TABLE IF NOT EXISTS pipeline_run_log (
    pipeline_run_id TEXT PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT NOT NULL,
    records_extracted INTEGER DEFAULT 0,
    records_loaded INTEGER DEFAULT 0,
    records_rejected INTEGER DEFAULT 0,
    error_message TEXT
);

-- Track rejected records and quality failures
CREATE TABLE IF NOT EXISTS data_quality_exceptions (
    exception_id BIGSERIAL PRIMARY KEY,
    pipeline_run_id TEXT,
    source_file_name TEXT,
    source_row_number INTEGER,
    record_id TEXT,
    rule_id TEXT NOT NULL,
    error_message TEXT NOT NULL,
    rejected_record JSONB,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pipeline_run_id)
        REFERENCES pipeline_run_log(pipeline_run_id)
);


SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'pipeline_run_log',
      'data_quality_exceptions'
  )
ORDER BY table_name;







-- our 2 dim table



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

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('dim_branch', 'dim_date')
ORDER BY table_name;




-- our three fact tables 


-- Volume, completion rate, and processing time.
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

-- Customer wait time and service duration
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


-- staffing coverage and employee productivity
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

-- Foreign keys ensure that every loaded fact record references a valid branch and date.

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'fact_%'
ORDER BY table_name;



SELECT 'branches' AS dataset, COUNT(*) FROM stg_branches
UNION ALL
SELECT 'transactions', COUNT(*) FROM stg_transactions
UNION ALL
SELECT 'member_visits', COUNT(*) FROM stg_member_visits
UNION ALL
SELECT 'staffing', COUNT(*) FROM stg_staffing;




-- here we are preventing duplicate staging 



CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_branches_hash
ON stg_branches (record_hash);

CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_transactions_hash
ON stg_transactions (record_hash);

CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_member_visits_hash
ON stg_member_visits (record_hash);

CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_staffing_hash
ON stg_staffing (record_hash);


-- this matters because We need to detect duplicate source records without losing the ability to audit them.
SELECT record_hash, COUNT(*) AS duplicate_count
FROM stg_transactions
GROUP BY record_hash
HAVING COUNT(*) > 1;



-- implementing idempotent staging loads Prevent repeated pipeline executions from loading the same CSV records again,
-- while preserving intentional duplicates within a source file for auditing.

DROP INDEX IF EXISTS ux_stg_branches_hash;
DROP INDEX IF EXISTS ux_stg_transactions_hash;
DROP INDEX IF EXISTS ux_stg_member_visits_hash;
DROP INDEX IF EXISTS ux_stg_staffing_hash;

-- adding source-row uniqueness

-- These indexes prevent the same source row from being staged twice, while allowing two different rows with 
-- identical contents.
CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_branches_source
ON stg_branches (source_file_name, source_row_number);

CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_transactions_source
ON stg_transactions (source_file_name, source_row_number);

CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_visits_source
ON stg_member_visits (source_file_name, source_row_number);

CREATE UNIQUE INDEX IF NOT EXISTS ux_stg_staffing_source
ON stg_staffing (source_file_name, source_row_number);

-- Why this matters: Idempotency protects KPI calculations from inflated counts when pipelines are rerun.
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
  AND indexname LIKE 'ux_stg_%_source'
ORDER BY indexname;



-- verifying Handling repeated pipeline runs
--Why this matters: This protects against repeated ingestion of the same source rows. Later, we'll strengthen 
--this with file-version tracking and database-level conflict handling so updated CSV files and concurrent runs are 
--handled correctly.
SELECT 'branches' AS dataset, COUNT(*) FROM stg_branches
UNION ALL
SELECT 'transactions', COUNT(*) FROM stg_transactions
UNION ALL
SELECT 'member_visits', COUNT(*) FROM stg_member_visits
UNION ALL
SELECT 'staffing', COUNT(*) FROM stg_staffing;





-- verfying pipeline log 



SELECT
    pipeline_run_id,
    status,
    records_extracted,
    records_loaded,
    records_rejected,
    start_time,
    end_time
FROM pipeline_run_log
ORDER BY start_time DESC;





--  verifying if new records have been inserted 

SELECT
    status,
    records_extracted,
    records_loaded
FROM pipeline_run_log
ORDER BY start_time DESC
LIMIT 1;





-- storing all 217 rejected record in the data_quality_exceptions table for auditing and monitoring

SELECT rule_id, COUNT(*) AS rejected_count
FROM data_quality_exceptions
GROUP BY rule_id
ORDER BY rule_id;






-- now we will populate data into our different schemas


INSERT INTO dim_date (
    date_key,
    full_date,
    day_of_week,
    day_name,
    day_of_month,
    month_number,
    month_name,
    quarter_number,
    year_number,
    is_weekend
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER,
    d::DATE,
    EXTRACT(ISODOW FROM d)::INTEGER,
    TRIM(TO_CHAR(d, 'Day')),
    EXTRACT(DAY FROM d)::INTEGER,
    EXTRACT(MONTH FROM d)::INTEGER,
    TRIM(TO_CHAR(d, 'Month')),
    EXTRACT(QUARTER FROM d)::INTEGER,
    EXTRACT(YEAR FROM d)::INTEGER,
    EXTRACT(ISODOW FROM d) IN (6, 7)
FROM GENERATE_SERIES(
    DATE '2020-01-01',
    DATE '2030-12-31',
    INTERVAL '1 day'
) AS dates(d)
ON CONFLICT (date_key) DO NOTHING;

-- Why this matters: The date dimension enables daily, weekly, monthly, quarterly, and yearly 
-- KPI analysis in SQL and Power BI.

SELECT COUNT(*) AS total_dates,
       MIN(full_date) AS first_date,
       MAX(full_date) AS last_date
FROM dim_date;



-- now populating branch dimention

SELECT
    branch_key,
    branch_id,
    branch_name,
    region,
    branch_type,
    active_flag
FROM dim_branch
ORDER BY branch_id;


-- verifying fact transitions table 

SELECT
    COUNT(*) AS total_transactions,
    COUNT(DISTINCT transaction_id) AS unique_transactions,
    ROUND(SUM(amount), 2) AS total_amount
FROM fact_transactions;


-- loeading member visit and staffing


SELECT 'Transactions' AS dataset, COUNT(*) AS records
FROM fact_transactions
UNION ALL
SELECT 'Member Visits', COUNT(*)
FROM fact_member_visits
UNION ALL
SELECT 'Staffing', COUNT(*)
FROM fact_staffing;





-- KPI 


-- KPI 1: Daily transaction volume
CREATE OR REPLACE VIEW vw_daily_transaction_volume AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    COUNT(*) AS transaction_count
FROM fact_transactions t
JOIN dim_branch b ON t.branch_key = b.branch_key
JOIN dim_date d ON t.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date;


-- KPI 2: Average member wait time
CREATE OR REPLACE VIEW vw_average_wait_time AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    ROUND(AVG(v.wait_minutes), 2) AS avg_wait_minutes
FROM fact_member_visits v
JOIN dim_branch b ON v.branch_key = b.branch_key
JOIN dim_date d ON v.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date;


-- KPI 3: Average service duration
CREATE OR REPLACE VIEW vw_average_service_time AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    ROUND(AVG(v.service_minutes), 2) AS avg_service_minutes
FROM fact_member_visits v
JOIN dim_branch b ON v.branch_key = b.branch_key
JOIN dim_date d ON v.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date;


-- KPI 4: Transaction completion rate
CREATE OR REPLACE VIEW vw_transaction_completion_rate AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    COUNT(*) AS total_transactions,
    COUNT(*) FILTER (
        WHERE t.status = 'Completed'
    ) AS completed_transactions,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE t.status = 'Completed'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS completion_rate_pct
FROM fact_transactions t
JOIN dim_branch b ON t.branch_key = b.branch_key
JOIN dim_date d ON t.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date;


-- KPI 5: Transactions per employee hour
CREATE OR REPLACE VIEW vw_transactions_per_employee_hour AS
WITH daily_transactions AS (
    SELECT
        branch_key,
        date_key,
        COUNT(*) AS transaction_count
    FROM fact_transactions
    GROUP BY branch_key, date_key
)
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    t.transaction_count,
    s.employee_hours,
    ROUND(
        t.transaction_count::NUMERIC
        / NULLIF(s.employee_hours, 0),
        2
    ) AS transactions_per_employee_hour
FROM daily_transactions t
JOIN fact_staffing s
    ON t.branch_key = s.branch_key
   AND t.date_key = s.date_key
JOIN dim_branch b ON t.branch_key = b.branch_key
JOIN dim_date d ON t.date_key = d.date_key;


SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name LIKE 'vw_%'
ORDER BY table_name;


SELECT *
FROM vw_daily_transaction_volume
ORDER BY full_date DESC
LIMIT 10;






-- KPI 6: Daily staffing variance and coverage ratio
CREATE OR REPLACE VIEW vw_staffing_coverage AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    s.scheduled_employees,
    s.actual_employees,
    s.actual_employees - s.scheduled_employees AS staffing_variance,
    ROUND(
        100.0 * s.actual_employees
        / NULLIF(s.scheduled_employees, 0), 2
    ) AS staffing_ratio_pct
FROM fact_staffing s
JOIN dim_branch b ON s.branch_key = b.branch_key
JOIN dim_date d ON s.date_key = d.date_key;


-- KPI 7: Peak member service hour
CREATE OR REPLACE VIEW vw_peak_service_hour AS
WITH hourly_visits AS (
    SELECT
        branch_key,
        date_key,
        EXTRACT(HOUR FROM arrival_timestamp)::INTEGER AS service_hour,
        COUNT(*) AS visit_count
    FROM fact_member_visits
    GROUP BY branch_key, date_key, service_hour
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY branch_key, date_key
            ORDER BY visit_count DESC, service_hour
        ) AS hour_rank
    FROM hourly_visits
)
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    r.service_hour,
    r.visit_count
FROM ranked r
JOIN dim_branch b ON r.branch_key = b.branch_key
JOIN dim_date d ON r.date_key = d.date_key
WHERE r.hour_rank = 1;


-- KPI 8: Percentage of visits waiting over 10 minutes
CREATE OR REPLACE VIEW vw_wait_threshold AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    COUNT(*) AS total_visits,
    COUNT(*) FILTER (
        WHERE v.wait_minutes > 10
    ) AS visits_over_10_minutes,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE v.wait_minutes > 10
        ) / NULLIF(COUNT(*), 0), 2
    ) AS pct_over_10_minutes
FROM fact_member_visits v
JOIN dim_branch b ON v.branch_key = b.branch_key
JOIN dim_date d ON v.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date;


-- KPI 9: Data-quality exception counts by rule
CREATE OR REPLACE VIEW vw_quality_exceptions AS
SELECT
    rule_id,
    source_file_name,
    COUNT(*) AS exception_count
FROM data_quality_exceptions
GROUP BY rule_id, source_file_name;


-- KPI 10: Seven-day rolling average transaction volume
CREATE OR REPLACE VIEW vw_rolling_transaction_volume AS
WITH calendar AS (
    SELECT
        b.branch_id,
        b.branch_name,
        b.branch_key,
        d.full_date
    FROM dim_branch b
    CROSS JOIN dim_date d
    WHERE d.full_date BETWEEN
        (SELECT MIN(full_date) FROM dim_date dd
         JOIN fact_transactions t ON dd.date_key = t.date_key)
        AND
        (SELECT MAX(full_date) FROM dim_date dd
         JOIN fact_transactions t ON dd.date_key = t.date_key)
),
daily AS (
    SELECT
        c.branch_id,
        c.branch_name,
        c.full_date,
        COUNT(t.transaction_key) AS transaction_count
    FROM calendar c
    LEFT JOIN fact_transactions t
        ON t.branch_key = c.branch_key
       AND t.transaction_timestamp::DATE = c.full_date
    GROUP BY c.branch_id, c.branch_name, c.full_date
)
SELECT
    branch_id,
    branch_name,
    full_date,
    transaction_count,
    ROUND(
        AVG(transaction_count) OVER (
            PARTITION BY branch_id
            ORDER BY full_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    ) AS rolling_7day_avg
FROM daily;


-- KPI 11: Transaction volume by channel and type
CREATE OR REPLACE VIEW vw_transaction_channels AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    t.channel,
    t.transaction_type,
    COUNT(*) AS transaction_count
FROM fact_transactions t
JOIN dim_branch b ON t.branch_key = b.branch_key
JOIN dim_date d ON t.date_key = d.date_key
GROUP BY
    b.branch_id, b.branch_name, d.full_date,
    t.channel, t.transaction_type;


-- KPI 12: Member visit outcomes
CREATE OR REPLACE VIEW vw_visit_outcomes AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    v.outcome,
    COUNT(*) AS visit_count
FROM fact_member_visits v
JOIN dim_branch b ON v.branch_key = b.branch_key
JOIN dim_date d ON v.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date, v.outcome;


-- KPI 13: Branch operational summary
CREATE OR REPLACE VIEW vw_branch_operational_summary AS
WITH tx AS (
    SELECT branch_key,
           COUNT(*) AS total_transactions,
           ROUND(AVG(processing_seconds), 2) AS avg_processing_seconds
    FROM fact_transactions
    GROUP BY branch_key
),
visits AS (
    SELECT branch_key,
           COUNT(*) AS total_visits,
           ROUND(AVG(wait_minutes), 2) AS avg_wait_minutes
    FROM fact_member_visits
    GROUP BY branch_key
),
staff AS (
    SELECT branch_key,
           SUM(employee_hours) AS total_employee_hours
    FROM fact_staffing
    GROUP BY branch_key
)
SELECT
    b.branch_id,
    b.branch_name,
    b.region,
    COALESCE(tx.total_transactions, 0) AS total_transactions,
    COALESCE(v.total_visits, 0) AS total_visits,
    v.avg_wait_minutes,
    tx.avg_processing_seconds,
    COALESCE(s.total_employee_hours, 0) AS total_employee_hours
FROM dim_branch b
LEFT JOIN tx ON b.branch_key = tx.branch_key
LEFT JOIN visits v ON b.branch_key = v.branch_key
LEFT JOIN staff s ON b.branch_key = s.branch_key;


-- KPI 14: Daily member visit volume
CREATE OR REPLACE VIEW vw_daily_member_visits AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    COUNT(*) AS visit_count
FROM fact_member_visits v
JOIN dim_branch b ON v.branch_key = b.branch_key
JOIN dim_date d ON v.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date;


-- KPI 15: Daily average transaction processing time
CREATE OR REPLACE VIEW vw_processing_time AS
SELECT
    b.branch_id,
    b.branch_name,
    d.full_date,
    ROUND(AVG(t.processing_seconds), 2) AS avg_processing_seconds
FROM fact_transactions t
JOIN dim_branch b ON t.branch_key = b.branch_key
JOIN dim_date d ON t.date_key = d.date_key
GROUP BY b.branch_id, b.branch_name, d.full_date;


-- verifying all 15 kpis

SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name LIKE 'vw_%'
ORDER BY table_name;

-- testing branch summary 

SELECT *
FROM vw_branch_operational_summary
ORDER BY total_transactions DESC;



-- Confirming that our SQL views produce consistent results before connecting PBI

-- Check 1: Transaction volume matches the fact table
SELECT
    (SELECT COUNT(*) FROM fact_transactions) AS fact_count,
    (SELECT SUM(transaction_count)
     FROM vw_daily_transaction_volume) AS kpi_count;

-- Check 2: Member visit volume matches the fact table
SELECT
    (SELECT COUNT(*) FROM fact_member_visits) AS fact_count,
    (SELECT SUM(visit_count)
     FROM vw_daily_member_visits) AS kpi_count;

-- Check 3: No negative wait or service durations
SELECT
    COUNT(*) AS invalid_durations
FROM fact_member_visits
WHERE wait_minutes < 0
   OR service_minutes < 0;




SELECT
    (SELECT COUNT(*) FROM fact_transactions) AS transaction_fact_count,
    (SELECT SUM(transaction_count)
     FROM vw_daily_transaction_volume) AS transaction_kpi_count,
    (SELECT COUNT(*) FROM fact_member_visits) AS visit_fact_count,
    (SELECT SUM(visit_count)
     FROM vw_daily_member_visits) AS visit_kpi_count;





-- Business Analysis Query Identifying branch-days where avg member wait time exceeds 10 minutes and staffind coverage is below 90%

-- Identify branches with high wait times and low staffing

SELECT
    w.branch_id,
    w.branch_name,
    w.full_date,
    w.avg_wait_minutes,
    s.scheduled_employees,
    s.actual_employees,
    s.staffing_ratio_pct
FROM vw_average_wait_time w
JOIN vw_staffing_coverage s
    ON w.branch_id = s.branch_id
   AND w.full_date = s.full_date
WHERE w.avg_wait_minutes > 10
  AND s.staffing_ratio_pct < 90
ORDER BY
    w.avg_wait_minutes DESC,
    s.staffing_ratio_pct ASC;




-- Stop the pipeline from inserting the same 217 rejected records every time it runs.


ALTER TABLE data_quality_exceptions
ADD COLUMN IF NOT EXISTS source_record_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_quality_exception_source
ON data_quality_exceptions (
    source_file_name,
    source_record_hash,
    rule_id
)
WHERE source_record_hash IS NOT NULL;

SELECT
    COUNT(*) AS total_exceptions,
    COUNT(DISTINCT pipeline_run_id) AS validation_runs
FROM data_quality_exceptions;



SELECT
    COUNT(*) AS total_exceptions,
    COUNT(*) FILTER (
        WHERE source_record_hash IS NOT NULL
    ) AS hashed_exceptions,
    COUNT(DISTINCT source_record_hash) AS unique_hashes
FROM data_quality_exceptions;





ALTER TABLE data_quality_exceptions
ADD COLUMN IF NOT EXISTS source_record_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_quality_exception_source
ON data_quality_exceptions (
    source_file_name,
    source_record_hash,
    rule_id
)
WHERE source_record_hash IS NOT NULL;


SELECT
    COUNT(*) AS total_exceptions,
    COUNT(source_record_hash) AS hashed_exceptions,
    COUNT(DISTINCT source_record_hash) AS unique_hashes
FROM data_quality_exceptions;

