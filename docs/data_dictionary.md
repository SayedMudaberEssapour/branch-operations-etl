
# Branch Operations Data Dictionary

All datasets contain synthetic data only.

## 1. branches.csv
One record per branch.

| Column | Data Type |
|---|---|
| branch_id | String |
| branch_name | String |
| region | String |
| branch_type | String |
| open_date | Date |
| active_flag | String |

## 2. transactions.csv
One record per transaction.

| Column | Data Type |
|---|---|
| transaction_id | String |
| branch_id | String |
| transaction_timestamp | DateTime |
| transaction_type | String |
| channel | String |
| amount | Decimal |
| processing_seconds | Integer |
| status | String |

## 3. member_visits.csv
One record per member visit.

| Column | Data Type |
|---|---|
| visit_id | String |
| branch_id | String |
| arrival_timestamp | DateTime |
| service_start_timestamp | DateTime |
| service_end_timestamp | DateTime |
| service_type | String |
| outcome | String |

## 4. staffing.csv
One record per branch per work date.

| Column | Data Type |
|---|---|
| branch_id | String |
| work_date | Date |
| scheduled_employees | Integer |
| actual_employees | Integer |
| employee_hours | Decimal |
