
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
