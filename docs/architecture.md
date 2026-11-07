
# Branch Operations Pipeline Architecture

## Analytical Database Design

The project uses a star schema with two dimensions and three fact tables.

### Dimension Tables

**dim_branch**
- Primary key: branch_key
- Business key: branch_id
- Grain: One row per branch

**dim_date**
- Primary key: date_key
- Grain: One row per calendar date

### Fact Tables

**fact_transactions**
- Primary key: transaction_key
- Grain: One row per unique transaction
- Foreign keys: branch_key, date_key

**fact_member_visits**
- Primary key: visit_key
- Grain: One row per unique member visit
- Foreign keys: branch_key, date_key

**fact_staffing**
- Primary key: staffing_key
- Grain: One row per branch per work date
- Foreign keys: branch_key, date_key

## Relationships

- dim_branch connects to all three fact tables using branch_key.
- dim_date connects to all three fact tables using date_key.
- Each dimension has a one-to-many relationship with its fact tables.

## Supporting Tables

**Staging**
- stg_branches
- stg_transactions
- stg_member_visits
- stg_staffing

**Pipeline Monitoring**
- pipeline_run_log

**Data Quality**
- fact_data_quality_exceptions

## Design Decisions

- Surrogate keys identify dimension and fact records.
- Business identifiers support duplicate detection.
- Staging preserves source data and ingestion metadata.
- Fact tables contain validated operational records.
- SQL views calculate business KPIs.
