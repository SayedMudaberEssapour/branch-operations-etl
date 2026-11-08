# Branch Operations ETL & KPI Monitoring Pipeline

An end-to-end data engineering portfolio project that transforms synthetic branch operations data into validated, analytics-ready PostgreSQL datasets and an interactive Power BI dashboard.

## Project Overview

This project demonstrates a complete ETL workflow:

1. Generate reproducible synthetic operational data.
2. Extract CSV datasets using Python.
3. Validate records against 15 data quality rules.
4. Separate rejected records and log quality exceptions.
5. Load validated data into PostgreSQL staging and dimensional warehouse tables.
6. Transform warehouse data into 15 SQL KPI views.
7. Visualize operational performance in Power BI.
8. Run automated tests through GitHub Actions.

## Architecture

```text
Synthetic CSV Data
        |
        v
Python Extraction
        |
        v
Data Quality Validation
        |
        +----> Rejected Records / Exception Logs
        |
        v
PostgreSQL Staging Tables
        |
        v
Dimensional Data Warehouse
        |
        v
15 SQL KPI Views
        |
        v
Power BI Dashboard
```

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data generation and ETL orchestration |
| Pandas | Data extraction and validation |
| PostgreSQL | Staging, warehouse, and analytical views |
| SQLAlchemy / psycopg | Database connectivity |
| SQL | Data transformations and KPI calculations |
| Power BI | Interactive reporting |
| Pytest | Automated data quality testing |
| GitHub Actions | Continuous integration |
| Git / GitHub | Version control and project delivery |

## Data Pipeline Results

The pipeline processes four synthetic datasets representing 10 branches and a 30-day operational period.

| Dataset | Valid Records | Rejected Records |
|---|---:|---:|
| Branches | 10 | 0 |
| Transactions | 7,350 | 151 |
| Member Visits | 2,940 | 60 |
| Staffing | 294 | 6 |
| **Total** | **10,594** | **217** |

Rejected records are tracked separately to support data quality monitoring and troubleshooting.

## Data Warehouse

The PostgreSQL warehouse follows a dimensional model.

**Dimensions**
- `dim_branch`
- `dim_date`

**Facts**
- `fact_transactions`
- `fact_member_visits`
- `fact_staffing`

The project includes staging tables, pipeline execution logs, and data quality exception tracking.

## Data Quality Framework

The pipeline implements 15 validation rules covering:

- Missing and duplicate identifiers
- Invalid branch references
- Invalid and future timestamps
- Negative amounts and processing durations
- Incorrect service event sequences
- Invalid categories and active flags
- Inconsistent staffing information
- Duplicate source records

Rejected records are exported for investigation, while valid records continue through the ETL process.

## KPI Monitoring

Fifteen PostgreSQL analytical views support operational reporting, including transaction volume, average wait time, completion rate, staffing coverage, service duration, peak service hours, and branch-level performance.

## Power BI Dashboard

![Branch Operations Power BI Dashboard](docs\Screen_shots\powerbi_dashboard.png)



The interactive dashboard includes:

- Total Transactions
- Average Wait Time
- Transaction Completion Rate
- Staffing Coverage
- Daily Transaction Volume
- Transaction Volume by Branch
- Branch and Date Range filters

The dashboard is built using PostgreSQL analytical views and is provided as a Power BI Desktop report.

**Report file:** `powerbi/Branch_Operations_Dashboard.pbix`

*Note: Data is synthetic. Some dashboard KPI aggregations are MVP implementations and are planned for further refinement.*

## Running the Pipeline

Create and activate a Python virtual environment, then install dependencies:

```bash
python -m venv .venv
pip install -r requirements.txt
```

Configure PostgreSQL connection settings using `.env.example` as a reference.

Create the PostgreSQL database and execute the SQL schema scripts in the `sql/` directory in the appropriate order.

Generate the synthetic datasets:

```bash
python -m src.generate_data
```

Run the ETL pipeline:

```bash
python -m src.main
```

Run the automated tests:

```bash
python -m pytest tests/ -v
```

## Automation and Reliability

GitHub Actions automatically checks Python syntax, generates synthetic test data, and executes automated tests on pushes and pull requests to the main branch.

The ETL pipeline also supports idempotent loading to reduce duplicate staging and warehouse records during reruns.

## Future Enhancements

- Refine weighted KPI calculations in Power BI
- Expand reporting visuals and drill-down analysis
- Improve date modeling and filtering
- Add scheduled ETL execution and dashboard refresh
- Extend pipeline observability and monitoring

## Project Purpose

This project was developed to demonstrate practical data engineering skills across ingestion, validation, transformation, relational data modeling, SQL analytics, automated testing, and business intelligence delivery.

**All operational records are synthetic and do not represent real financial institution or customer data.**
