
# Branch Operations KPI Definitions

All KPIs use synthetic branch operations data.

| # | KPI | Definition |
|---|---|---|
| 1 | Daily Transaction Volume | Number of transactions per branch per day |
| 2 | Average Member Wait Time | Average minutes between arrival and service start |
| 3 | Average Service Duration | Average minutes spent receiving service |
| 4 | Transaction Completion Rate | Completed transactions / Total transactions × 100 |
| 5 | Transactions per Employee Hour | Total transactions / Employee hours |
| 6 | Staffing Variance | Actual employees - Scheduled employees |
| 7 | Staffing Ratio | Actual employees / Scheduled employees × 100 |
| 8 | Peak Service Hour | Hour with the highest number of member visits |
| 9 | Wait Threshold Exceedance Rate | Visits exceeding threshold / Total visits × 100 |
| 10 | Data-Quality Exception Count | Number of exceptions grouped by rule |
| 11 | Seven-Day Rolling Transaction Average | Average daily transaction volume over seven days |
| 12 | Transaction Volume by Channel | Transaction counts grouped by channel |
| 13 | Transaction Volume by Type | Transaction counts grouped by transaction type |
| 14 | Visit Outcomes by Branch | Member visit counts grouped by outcome and branch |
| 15 | Branch Operational Performance Summary | Combined daily transaction, service, staffing, and quality metrics |

## Business Investigation Query

Identify branches where:
- Average member wait time > 10 minutes
- Staffing ratio < 90%

Return:
- Branch name
- Date
- Average wait time
- Staffing ratio
- Transaction volume
- Service volume

Sort the most severe cases first.

## Calculation Rules

- Use validated records only.
- Prevent division by zero.
- Use branch and date as the primary reporting dimensions.
- Apply the configured wait-time threshold.
- Document exclusions and null values.
- Calculate KPIs in SQL for consistent reporting.
