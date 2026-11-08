
-- Identify branches with high wait times and low staffing
-- This query demonstrates how your ETL pipeline supports business decisions by identifying potential relationships 
--between staffing shortages and customer wait times. It does not, by itself, prove that understaffing caused the longer 
-- waits.

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
