
//here we are creating staging tables for the branch operations data. These tables will be used to load raw data before it is transformed and loaded into the final destination tables.

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




-- Here we are tracking every ETL execution and record data-quality failures. This will help us monitor the ETL process and identify any issues with the data.
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
