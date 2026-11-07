#here I am loading the extracted CSV records into the four PostgreSQL staging tables.


"""Load extracted data into PostgreSQL staging tables."""
import json
from datetime import datetime, timezone

from src.quality import validate_all

from uuid import uuid4

from sqlalchemy import text

from src.database import get_engine
from src.extract import extract_all, SOURCE_FILES
from src.transform import add_staging_metadata
from src.quality import validate_branches
from src.quality import validate_transactions
import pandas as pd

import pandas as pd
from src.quality import validate_member_visits, validate_staffing
import hashlib
import json


STAGING_TABLES = {
    "branches": "stg_branches",
    "transactions": "stg_transactions",
    "member_visits": "stg_member_visits",
    "staffing": "stg_staffing",
}


def load_staging():
    """Load source datasets into PostgreSQL staging."""
    engine = get_engine()
    datasets = extract_all()
    run_id = str(uuid4())

    total_rows = sum(len(df) for df in datasets.values())
    total_loaded = 0
    total_skipped = 0

    # Use one transaction so all inserts succeed or roll back.
    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO pipeline_run_log (
                    pipeline_run_id,
                    start_time,
                    status,
                    records_extracted
                )
                VALUES (
                    :run_id,
                    CURRENT_TIMESTAMP,
                    'RUNNING',
                    :total_rows
                )
            """),
            {"run_id": run_id, "total_rows": total_rows}
        )

        for name, df in datasets.items():
            prepared = add_staging_metadata(
                df,
                SOURCE_FILES[name],
                run_id
            )
            
            # Insert only source rows not already staged.
            # The source-row unique index prevents duplicate ingestion.
            table_name = STAGING_TABLES[name]

            existing_rows = connection.execute(
                text(f"""
                    SELECT source_row_number
                    FROM {table_name}
                    WHERE source_file_name = :source_file
                """),
                {"source_file": SOURCE_FILES[name]}
            ).scalars().all()

            existing_row_numbers = set(existing_rows)

            new_rows = prepared[
                ~prepared["source_row_number"].isin(existing_row_numbers)
            ]

            if not new_rows.empty:
                new_rows.to_sql(
                    table_name,
                    con=connection,
                    if_exists="append",
                    index=False,
                    chunksize=1000
                )

            print(
                f"{table_name}: {len(new_rows)} new rows, "
                f"{len(prepared) - len(new_rows)} skipped"
            )

            total_loaded += len(new_rows)
            total_skipped += len(prepared) - len(new_rows)

            print(
                f"Loaded {len(prepared)} rows into "
                f"{STAGING_TABLES[name]}"
            )

        
            connection.execute(
                text("""
                    UPDATE pipeline_run_log
                    SET status = 'STAGED',
                        end_time = CURRENT_TIMESTAMP,
                        records_loaded = :loaded
                    WHERE pipeline_run_id = :run_id
                """),
                {
                    "run_id": run_id,
                    "loaded": total_loaded
                }
            )


    print(f"Staging completed. Run ID: {run_id}")
    print(f"Total inserted: {total_loaded}")
    print(f"Total skipped: {total_skipped}")





#Goal: Store all 217 rejected records in the data_quality_exceptions table for auditing and monitoring.


def load_quality_exceptions():
    """Validate source data and save new quality exceptions to PostgreSQL."""

    datasets = extract_all()
    results = validate_all(datasets)
    engine = get_engine()

    run_id = str(uuid4())

    total_extracted = sum(
        len(df) for df in datasets.values()
    )

    total_rejected = sum(
        len(rejected)
        for valid, rejected in results.values()
    )

    total_inserted = 0

    with engine.begin() as connection:

        # 1. Create pipeline validation run
        connection.execute(
            text("""
                INSERT INTO pipeline_run_log (
                    pipeline_run_id,
                    start_time,
                    status,
                    records_extracted,
                    records_rejected
                )
                VALUES (
                    :run_id,
                    CURRENT_TIMESTAMP,
                    'VALIDATING',
                    :extracted,
                    :rejected
                )
            """),
            {
                "run_id": run_id,
                "extracted": total_extracted,
                "rejected": total_rejected
            }
        )

        # 2. Process rejected records from every dataset
        for name, (valid, rejected) in results.items():

            if rejected.empty:
                continue

            records = []

            for _, row in rejected.iterrows():

                # Exclude validation metadata from original record
                original_record = row.drop(
                    labels=["rule_id", "error_message"],
                    errors="ignore"
                ).to_dict()

                # Convert record to consistent JSON
                record_json = json.dumps(
                    original_record,
                    sort_keys=True,
                    default=str
                )

                # Generate SHA-256 fingerprint
                record_hash = hashlib.sha256(
                    record_json.encode("utf-8")
                ).hexdigest()

                # Preserve original source row number where available
                source_row = row.get(
                    "source_row_number",
                    int(row.name) + 2
                )

                records.append({
                    "pipeline_run_id": run_id,
                    "source_file_name": SOURCE_FILES[name],
                    "source_row_number": int(source_row),
                    "record_id": str(
                        row.get(
                            "transaction_id",
                            row.get(
                                "visit_id",
                                row.get("branch_id", "")
                            )
                        )
                    ),
                    "rule_id": row["rule_id"],
                    "error_message": row["error_message"],
                    "rejected_record": record_json,
                    "source_record_hash": record_hash
                })

            # 3. Insert exceptions with duplicate protection
            result = connection.execute(
                text("""
                    INSERT INTO data_quality_exceptions (
                        pipeline_run_id,
                        source_file_name,
                        source_row_number,
                        record_id,
                        rule_id,
                        error_message,
                        rejected_record,
                        source_record_hash
                    )
                    VALUES (
                        :pipeline_run_id,
                        :source_file_name,
                        :source_row_number,
                        :record_id,
                        :rule_id,
                        :error_message,
                        CAST(:rejected_record AS JSONB),
                        :source_record_hash
                    )
                    ON CONFLICT (
                        source_file_name,
                        source_record_hash,
                        rule_id
                    )
                    WHERE source_record_hash IS NOT NULL
                    DO NOTHING
                """),
                records
            )

            inserted = result.rowcount
            total_inserted += inserted

            print(
                f"{name}: {len(rejected)} rejected, "
                f"{inserted} new exceptions inserted"
            )

        # 4. Mark validation run as completed
        connection.execute(
            text("""
                UPDATE pipeline_run_log
                SET status = 'VALIDATED',
                    end_time = CURRENT_TIMESTAMP
                WHERE pipeline_run_id = :run_id
            """),
            {"run_id": run_id}
        )

    print("\nValidation completed successfully")
    print(f"Validation run: {run_id}")
    print(f"Total extracted: {total_extracted}")
    print(f"Total rejected: {total_rejected}")
    print(f"New exceptions inserted: {total_inserted}")
    print(f"Duplicate exceptions skipped: {total_rejected - total_inserted}")




# Loading the 10 validated branches into dim_branch table.
def load_branch_dimension():
    """Load validated branches into the branch dimension."""
    datasets = extract_all()

    valid_branches, rejected = validate_branches(
        datasets["branches"]
    )

    engine = get_engine()

    with engine.begin() as connection:
        for _, row in valid_branches.iterrows():
            connection.execute(
                text("""
                    INSERT INTO dim_branch (
                        branch_id,
                        branch_name,
                        region,
                        branch_type,
                        open_date,
                        active_flag
                    )
                    VALUES (
                        :branch_id,
                        :branch_name,
                        :region,
                        :branch_type,
                        :open_date,
                        :active_flag
                    )
                    ON CONFLICT (branch_id)
                    DO UPDATE SET
                        branch_name = EXCLUDED.branch_name,
                        region = EXCLUDED.region,
                        branch_type = EXCLUDED.branch_type,
                        open_date = EXCLUDED.open_date,
                        active_flag = EXCLUDED.active_flag
                """),
                {
                    "branch_id": row["branch_id"],
                    "branch_name": row["branch_name"],
                    "region": row["region"],
                    "branch_type": row["branch_type"],
                    "open_date": row["open_date"],
                    "active_flag": row["active_flag"]
                }
            )

    print(f"Loaded {len(valid_branches)} branches")
    print(f"Rejected {len(rejected)} branches")



# This will load the 7,350 validated transactions into postgresql's fact_transactions table

def load_transaction_facts():
    """Load validated transactions into the fact table."""
    datasets = extract_all()

    valid, rejected = validate_transactions(
        datasets["transactions"],
        datasets["branches"]
    )

    # Normalize approved category values before loading.
    categories = {
        "transaction_type": [
            "Deposit", "Withdrawal", "Transfer",
            "Account Payment", "Cashier Check",
            "Account Maintenance"
        ],
        "channel": [
            "Teller", "ATM", "Self-Service", "Appointment"
        ],
        "status": [
            "Completed", "Failed", "Reversed", "Pending"
        ]
    }

    for column, allowed in categories.items():
        lookup = {value.casefold(): value for value in allowed}
        valid[column] = (
            valid[column].str.strip().str.casefold().map(lookup)
        )

    valid["transaction_timestamp"] = pd.to_datetime(
        valid["transaction_timestamp"]
    )
    valid["amount"] = pd.to_numeric(valid["amount"])
    valid["processing_seconds"] = pd.to_numeric(
        valid["processing_seconds"]
    ).astype(int)

    valid["date_key"] = valid[
        "transaction_timestamp"
    ].dt.strftime("%Y%m%d").astype(int)

    engine = get_engine()

    with engine.begin() as connection:
        branch_lookup = dict(
            connection.execute(
                text("SELECT branch_id, branch_key FROM dim_branch")
            ).all()
        )

        valid["branch_key"] = valid["branch_id"].map(
            branch_lookup
        )

        if valid["branch_key"].isna().any():
            raise ValueError(
                "Some validated branches are missing from dim_branch"
            )

        records = valid[[
            "transaction_id",
            "branch_key",
            "date_key",
            "transaction_timestamp",
            "transaction_type",
            "channel",
            "amount",
            "processing_seconds",
            "status"
        ]].to_dict("records")

        connection.execute(
            text("""
                INSERT INTO fact_transactions (
                    transaction_id, branch_key, date_key,
                    transaction_timestamp, transaction_type,
                    channel, amount, processing_seconds, status
                )
                VALUES (
                    :transaction_id, :branch_key, :date_key,
                    :transaction_timestamp, :transaction_type,
                    :channel, :amount, :processing_seconds, :status
                )
                ON CONFLICT (transaction_id) DO NOTHING
            """),
            records
        )

    print(f"Validated transactions: {len(valid)}")
    print(f"Rejected transactions: {len(rejected)}")
    print("Transaction fact load completed.")




def load_member_visit_facts():
    """Load validated member visits into the warehouse."""
    datasets = extract_all()
    valid, rejected = validate_member_visits(
        datasets["member_visits"], datasets["branches"]
    )

    valid = valid.copy()

    for column in [
        "arrival_timestamp",
        "service_start_timestamp",
        "service_end_timestamp"
    ]:
        valid[column] = pd.to_datetime(valid[column])

    valid["wait_minutes"] = (
        valid["service_start_timestamp"]
        - valid["arrival_timestamp"]
    ).dt.total_seconds() / 60

    valid["service_minutes"] = (
        valid["service_end_timestamp"]
        - valid["service_start_timestamp"]
    ).dt.total_seconds() / 60

    valid["date_key"] = (
        valid["arrival_timestamp"].dt.strftime("%Y%m%d").astype(int)
    )

    for column, allowed in {
        "service_type": [
            "Account Support", "New Membership",
            "Loan Support", "Card Support",
            "General Inquiry", "Fraud Support"
        ],
        "outcome": [
            "Resolved", "Escalated",
            "Follow-Up Required", "Abandoned"
        ]
    }.items():
        lookup = {v.casefold(): v for v in allowed}
        valid[column] = (
            valid[column].str.strip().str.casefold().map(lookup)
        )

    engine = get_engine()

    with engine.begin() as connection:
        branch_lookup = dict(
            connection.execute(
                text("SELECT branch_id, branch_key FROM dim_branch")
            ).all()
        )

        valid["branch_key"] = valid["branch_id"].map(branch_lookup)

        if valid["branch_key"].isna().any():
            raise ValueError("Missing branch dimension reference")

        columns = [
            "visit_id", "branch_key", "date_key",
            "arrival_timestamp", "service_start_timestamp",
            "service_end_timestamp", "service_type", "outcome",
            "wait_minutes", "service_minutes"
        ]

        connection.execute(
            text("""
                INSERT INTO fact_member_visits (
                    visit_id, branch_key, date_key,
                    arrival_timestamp, service_start_timestamp,
                    service_end_timestamp, service_type, outcome,
                    wait_minutes, service_minutes
                )
                VALUES (
                    :visit_id, :branch_key, :date_key,
                    :arrival_timestamp, :service_start_timestamp,
                    :service_end_timestamp, :service_type, :outcome,
                    :wait_minutes, :service_minutes
                )
                ON CONFLICT (visit_id) DO NOTHING
            """),
            valid[columns].to_dict("records")
        )

    print(f"Member visits: {len(valid)} valid, {len(rejected)} rejected")


def load_staffing_facts():
    """Load validated daily staffing records."""
    datasets = extract_all()
    valid, rejected = validate_staffing(
        datasets["staffing"], datasets["branches"]
    )

    valid = valid.copy()
    valid["date_key"] = (
        pd.to_datetime(valid["work_date"])
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    for column in [
        "scheduled_employees",
        "actual_employees",
        "employee_hours"
    ]:
        valid[column] = pd.to_numeric(valid[column])

    engine = get_engine()

    with engine.begin() as connection:
        branch_lookup = dict(
            connection.execute(
                text("SELECT branch_id, branch_key FROM dim_branch")
            ).all()
        )

        valid["branch_key"] = valid["branch_id"].map(branch_lookup)

        if valid["branch_key"].isna().any():
            raise ValueError("Missing branch dimension reference")

        columns = [
            "branch_key", "date_key",
            "scheduled_employees", "actual_employees",
            "employee_hours"
        ]

        connection.execute(
            text("""
                INSERT INTO fact_staffing (
                    branch_key, date_key,
                    scheduled_employees, actual_employees,
                    employee_hours
                )
                VALUES (
                    :branch_key, :date_key,
                    :scheduled_employees, :actual_employees,
                    :employee_hours
                )
                ON CONFLICT (branch_key, date_key)
                DO UPDATE SET
                    scheduled_employees = EXCLUDED.scheduled_employees,
                    actual_employees = EXCLUDED.actual_employees,
                    employee_hours = EXCLUDED.employee_hours
            """),
            valid[columns].to_dict("records")
        )

    print(f"Staffing: {len(valid)} valid, {len(rejected)} rejected")


if __name__ == "__main__":
    load_staging()
