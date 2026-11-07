
# Data-Quality Rules

## Purpose
Ensure reliable branch operations data before loading records into analytical tables.

Invalid records will be rejected and recorded for investigation rather than silently deleted.

| Code | Validation Rule | Severity |
|---|---|---|
| DQ001 | Missing required primary identifier | ERROR |
| DQ002 | Duplicate business identifier | ERROR |
| DQ003 | Unknown branch identifier | ERROR |
| DQ004 | Invalid or unparseable timestamp | ERROR |
| DQ005 | Future-dated transaction or visit | ERROR |
| DQ006 | Negative transaction amount | ERROR |
| DQ007 | Negative processing time | ERROR |
| DQ008 | Service start occurs before arrival | ERROR |
| DQ009 | Service end occurs before service start | ERROR |
| DQ010 | Invalid category value | ERROR |
| DQ011 | Negative staffing value | ERROR |
| DQ012 | Employee hours inconsistent with actual staffing | ERROR |
| DQ013 | Missing required field | ERROR |
| DQ014 | Duplicate complete source record | WARNING |
| DQ015 | Invalid active flag | ERROR |

## Rejection Behavior
- Records failing ERROR rules are rejected.
- Duplicate complete source records are flagged and excluded from analytical loading.
- Rejected records retain their original values.
- Every exception is associated with a rule code.
- Exceptions are stored for investigation and reporting.

## Resolution Statuses
- OPEN
- REVIEWED
- RESOLVED
- ACCEPTED

## Severity Levels
- WARNING
- ERROR
- CRITICAL

## Data-Quality Reporting
The pipeline will report:
- Valid record count
- Rejected record count
- Exceptions by rule
- Exceptions by source
- Exceptions by severity
