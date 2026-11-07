# here we are building the data quality validation engne 

#creating our first validation rule, DQ001 - missing required identifier.


"""Data-quality validation rules."""

import pandas as pd


def validate_required_ids(df, id_column):
    """Separate records with valid and missing identifiers."""

    if id_column not in df.columns:
        raise ValueError(f"Missing column: {id_column}")

    missing_mask = (
        df[id_column].isna()
        | df[id_column].astype(str).str.strip().eq("")
    )

    valid_records = df.loc[~missing_mask].copy()
    rejected_records = df.loc[missing_mask].copy()

    rejected_records["rule_id"] = "DQ001"
    rejected_records["error_message"] = (
        f"Missing required identifier: {id_column}"
    )

    return valid_records, rejected_records





# now we implement DQ002 to detect duplicate transaction identifiers.

# Why this matters: Duplicate transaction IDs could inflate transaction volumes and distort branch performance KPIs.
def validate_duplicate_ids(df, id_column):
    """Identify records with duplicate business identifiers."""

    if id_column not in df.columns:
        raise ValueError(f"Missing column: {id_column}")

    duplicate_mask = (
        df[id_column].astype(str).str.strip().ne("")
        & df[id_column].notna()
        & df.duplicated(subset=[id_column], keep="first")
    )

    valid_records = df.loc[~duplicate_mask].copy()
    rejected_records = df.loc[duplicate_mask].copy()

    rejected_records["rule_id"] = "DQ002"
    rejected_records["error_message"] = (
        f"Duplicate identifier: {id_column}"
    )

    return valid_records, rejected_records



# Goal: Implement DQ003 — Unknown Branch Reference to detect transactions referencing branches that don't exist.


def validate_branch_references(df, branches):
    """Reject records referencing missing or unknown branches."""

    valid_branch_ids = set(
        branches["branch_id"].dropna().astype(str).str.strip()
    )

    branch_ids = df["branch_id"].fillna("").astype(str).str.strip()

    invalid_mask = ~branch_ids.isin(valid_branch_ids)

    valid_records = df.loc[~invalid_mask].copy()
    rejected_records = df.loc[invalid_mask].copy()

    rejected_records["rule_id"] = "DQ003"
    rejected_records["error_message"] = (
        "Missing or unknown branch reference"
    )

    return valid_records, rejected_records



# Goal: Implement DQ004 — Invalid Timestamp to identify missing or malformed transaction timestamps.


def validate_timestamps(df, timestamp_column):
    """Reject records containing invalid timestamps."""

    if timestamp_column not in df.columns:
        raise ValueError(f"Missing column: {timestamp_column}")

    parsed_timestamps = pd.to_datetime(
        df[timestamp_column],
        errors="coerce",
        format="ISO8601"
    )

    invalid_mask = parsed_timestamps.isna()

    valid_records = df.loc[~invalid_mask].copy()
    rejected_records = df.loc[invalid_mask].copy()

    rejected_records["rule_id"] = "DQ004"
    rejected_records["error_message"] = (
        f"Invalid or missing timestamp: {timestamp_column}"
    )

    return valid_records, rejected_records



# Goal: Implement DQ005 — Future Timestamp Detection to prevent transactions dated in the future from entering our analytical database.


def validate_future_timestamps(df, timestamp_column):
    """Reject records containing future timestamps."""

    if timestamp_column not in df.columns:
        raise ValueError(f"Missing column: {timestamp_column}")

    parsed_timestamps = pd.to_datetime(
        df[timestamp_column],
        errors="coerce",
        format="ISO8601",
        utc=True
    )

    current_time = pd.Timestamp.now(tz="UTC")

    future_mask = parsed_timestamps > current_time

    valid_records = df.loc[~future_mask].copy()
    rejected_records = df.loc[future_mask].copy()

    rejected_records["rule_id"] = "DQ005"
    rejected_records["error_message"] = (
        f"Future timestamp detected: {timestamp_column}"
    )

    return valid_records, rejected_records


# Goal: Implement DQ006 — Negative Transaction Amount to reject transactions with negative or nonnumeric amounts.


def validate_transaction_amounts(df):
    """Reject negative, missing, or nonnumeric transaction amounts."""

    if "amount" not in df.columns:
        raise ValueError("Missing column: amount")

    amounts = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    invalid_mask = (
        amounts.isna()
        | ~amounts.notna().where(amounts.isna(), True)
        | (amounts < 0)
    )

    valid_records = df.loc[~invalid_mask].copy()
    rejected_records = df.loc[invalid_mask].copy()

    rejected_records["rule_id"] = "DQ006"
    rejected_records["error_message"] = (
        "Negative, missing, or invalid transaction amount"
    )

    return valid_records, rejected_records


# Goal: Implement DQ007 — Negative Processing Time to detect invalid transaction processing durations.

def validate_processing_time(df):
    """Reject negative, missing, or invalid processing times."""

    if "processing_seconds" not in df.columns:
        raise ValueError("Missing column: processing_seconds")

    processing = pd.to_numeric(
        df["processing_seconds"],
        errors="coerce"
    )

    invalid_mask = (
        processing.isna()
        | ~processing.map(
            lambda value: pd.notna(value) and float(value).is_integer()
        )
        | (processing < 0)
    )

    valid_records = df.loc[~invalid_mask].copy()
    rejected_records = df.loc[invalid_mask].copy()

    rejected_records["rule_id"] = "DQ007"
    rejected_records["error_message"] = (
        "Negative, missing, or invalid processing time"
    )

    return valid_records, rejected_records


#Goal: Implement DQ008 — Service Start Before Arrival to detect member visits where service begins before the customer arrives.

# Why this matters
#A member cannot begin receiving service before arriving at the branch. These errors would produce negative wait times and inaccurate 
# service KPIs.

def validate_service_start(df):
    """Reject visits where service starts before arrival."""

    required = [
        "arrival_timestamp",
        "service_start_timestamp"
    ]

    for column in required:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    arrival = pd.to_datetime(
        df["arrival_timestamp"],
        errors="coerce",
        format="ISO8601",
        utc=True
    )

    service_start = pd.to_datetime(
        df["service_start_timestamp"],
        errors="coerce",
        format="ISO8601",
        utc=True
    )

    invalid_mask = (
        arrival.notna()
        & service_start.notna()
        & (service_start < arrival)
    )

    valid_records = df.loc[~invalid_mask].copy()
    rejected_records = df.loc[invalid_mask].copy()

    rejected_records["rule_id"] = "DQ008"
    rejected_records["error_message"] = (
        "Service start time is earlier than arrival time"
    )

    return valid_records, rejected_records



# Goal: Implement DQ009 — Service End Before Start to detect visits where service ends before it begins.



def validate_service_end(df):
    """Reject visits where service ends before it starts."""

    required = [
        "service_start_timestamp",
        "service_end_timestamp"
    ]

    for column in required:
        if column not in df.columns:
            raise ValueError(f"Missing column: {column}")

    service_start = pd.to_datetime(
        df["service_start_timestamp"],
        errors="coerce",
        format="ISO8601",
        utc=True
    )

    service_end = pd.to_datetime(
        df["service_end_timestamp"],
        errors="coerce",
        format="ISO8601",
        utc=True
    )

    invalid_mask = (
        service_start.notna()
        & service_end.notna()
        & (service_end < service_start)
    )

    valid_records = df.loc[~invalid_mask].copy()
    rejected_records = df.loc[invalid_mask].copy()

    rejected_records["rule_id"] = "DQ009"
    rejected_records["error_message"] = (
        "Service end time is earlier than service start time"
    )

    return valid_records, rejected_records





#Goal: Implement DQ010 — Invalid Category to detect values that don't match our approved categories.

def validate_categories(df, column, allowed_values):
    """Reject records with unrecognized category values."""

    if column not in df.columns:
        raise ValueError(f"Missing column: {column}")

    # Normalize spaces and capitalization.
    normalized = df[column].fillna("").astype(str).str.strip().str.casefold()

    approved = {
        str(value).strip().casefold()
        for value in allowed_values
    }

    invalid_mask = ~normalized.isin(approved)

    valid_records = df.loc[~invalid_mask].copy()
    rejected_records = df.loc[invalid_mask].copy()

    rejected_records["rule_id"] = "DQ010"
    rejected_records["error_message"] = (
        f"Invalid category in column: {column}"
    )

    return valid_records, rejected_records



'''Phase 6 — Checkpoint 6.11: Validate Staffing Data
Let's combine DQ011 and DQ012 to move faster.

Goal: Detect negative staffing values and inconsistent employee hours.'''


def validate_staffing_counts(df):
    """DQ011: Reject negative or invalid staffing counts."""
    scheduled = pd.to_numeric(
        df["scheduled_employees"], errors="coerce"
    )
    actual = pd.to_numeric(
        df["actual_employees"], errors="coerce"
    )

    invalid = (
        scheduled.isna()
        | actual.isna()
        | (scheduled < 0)
        | (actual < 0)
        | (scheduled % 1 != 0)
        | (actual % 1 != 0)
    )

    valid = df.loc[~invalid].copy()
    rejected = df.loc[invalid].copy()

    rejected["rule_id"] = "DQ011"
    rejected["error_message"] = "Invalid staffing count"

    return valid, rejected


def validate_employee_hours(df):
    """DQ012: Reject inconsistent employee hours."""
    actual = pd.to_numeric(
        df["actual_employees"], errors="coerce"
    )
    hours = pd.to_numeric(
        df["employee_hours"], errors="coerce"
    )

    invalid = (
        actual.isna()
        | hours.isna()
        | (hours < 0)
        | ((actual == 0) & (hours != 0))
        | ((actual > 0) & (hours <= 0))
        | (hours > actual * 24)
    )

    valid = df.loc[~invalid].copy()
    rejected = df.loc[invalid].copy()

    rejected["rule_id"] = "DQ012"
    rejected["error_message"] = "Inconsistent employee hours"

    return valid, rejected



'''Progress: 12 of 15 rules complete (80%).
Phase 6 — Checkpoint 6.12: Validate Required Fields (DQ013)
Goal: Detect records with missing required fields, not just missing IDs.
Step 1 — Open src/quality.py
Add this function at the bottom:'''



def validate_required_fields(df, required_columns):
    """DQ013: Reject records with missing required fields."""

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    invalid = df[required_columns].apply(
        lambda col: (
            col.isna()
            | col.astype(str).str.strip().eq("")
        )
    ).any(axis=1)

    valid = df.loc[~invalid].copy()
    rejected = df.loc[invalid].copy()

    rejected["rule_id"] = "DQ013"
    rejected["error_message"] = "Missing required field"

    return valid, rejected





def validate_duplicate_records(df):
    """DQ014: Detect exact duplicate source records."""
    source_columns = [
        col for col in df.columns
        if col not in {
            "staging_id", "pipeline_run_id",
            "source_file_name", "source_row_number",
            "ingestion_timestamp", "record_hash"
        }
    ]

    invalid = df.duplicated(
        subset=source_columns,
        keep="first"
    )

    valid = df.loc[~invalid].copy()
    rejected = df.loc[invalid].copy()

    rejected["rule_id"] = "DQ014"
    rejected["error_message"] = "Duplicate source record"

    return valid, rejected




'''Phase 6 — Checkpoint 6.13: Final Two Validation Rules
We'll complete DQ014 (Duplicate Source Records) and DQ015 (Invalid Active Flag) together.'''
def validate_active_flag(df):
    """DQ015: Reject invalid branch active flags."""
    if "active_flag" not in df.columns:
        raise ValueError("Missing column: active_flag")

    flags = (
        df["active_flag"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    invalid = ~flags.isin(["Y", "N"])

    valid = df.loc[~invalid].copy()
    rejected = df.loc[invalid].copy()

    rejected["rule_id"] = "DQ015"
    rejected["error_message"] = "Invalid active flag"

    return valid, rejected




'''Phase 7 — Checkpoint 7.1: Build the Validation Pipeline
Goal: Combine our 15 validation rules so the ETL pipeline can automatically separate valid and rejected records.'''




# Combined validation pipeline
# Keep the 15 individual DQ functions above this section.

def run_validation_checks(df, checks):
    """Run checks sequentially and collect rejected records."""
    valid = df.copy()
    rejected_batches = []

    for check in checks:
        valid, rejected = check(valid)

        if not rejected.empty:
            rejected_batches.append(rejected)

    rejected_all = (
        pd.concat(rejected_batches, ignore_index=True)
        if rejected_batches
        else pd.DataFrame()
    )

    assert len(valid) + len(rejected_all) == len(df)
    return valid, rejected_all


def validate_branches(df):
    """Validate branch master data."""
    return run_validation_checks(df, [
        lambda d: validate_required_fields(
            d, ["branch_id", "branch_name", "region",
                "branch_type", "open_date", "active_flag"]
        ),
        lambda d: validate_duplicate_ids(d, "branch_id"),
        lambda d: validate_timestamps(d, "open_date"),
        lambda d: validate_future_timestamps(d, "open_date"),
        lambda d: validate_categories(
            d, "branch_type", ["Urban", "Suburban", "Community"]
        ),
        validate_active_flag,
        validate_duplicate_records,
    ])


def validate_transactions(df, branches):
    """Validate transaction data."""
    return run_validation_checks(df, [
        lambda d: validate_required_fields(
            d, ["transaction_id", "branch_id",
                "transaction_timestamp", "transaction_type",
                "channel", "amount", "processing_seconds", "status"]
        ),
        lambda d: validate_duplicate_ids(d, "transaction_id"),
        lambda d: validate_branch_references(d, branches),
        lambda d: validate_timestamps(d, "transaction_timestamp"),
        lambda d: validate_future_timestamps(d, "transaction_timestamp"),
        validate_transaction_amounts,
        validate_processing_time,
        lambda d: validate_categories(
            d, "transaction_type",
            ["Deposit", "Withdrawal", "Transfer",
             "Account Payment", "Cashier Check", "Account Maintenance"]
        ),
        lambda d: validate_categories(
            d, "channel",
            ["Teller", "ATM", "Self-Service", "Appointment"]
        ),
        lambda d: validate_categories(
            d, "status",
            ["Completed", "Failed", "Reversed", "Pending"]
        ),
        validate_duplicate_records,
    ])


def validate_member_visits(df, branches):
    """Validate member visit data."""
    return run_validation_checks(df, [
        lambda d: validate_required_fields(
            d, ["visit_id", "branch_id", "arrival_timestamp",
                "service_start_timestamp", "service_end_timestamp",
                "service_type", "outcome"]
        ),
        lambda d: validate_duplicate_ids(d, "visit_id"),
        lambda d: validate_branch_references(d, branches),
        lambda d: validate_timestamps(d, "arrival_timestamp"),
        lambda d: validate_timestamps(d, "service_start_timestamp"),
        lambda d: validate_timestamps(d, "service_end_timestamp"),
        lambda d: validate_future_timestamps(d, "arrival_timestamp"),
        lambda d: validate_future_timestamps(d, "service_start_timestamp"),
        lambda d: validate_future_timestamps(d, "service_end_timestamp"),
        validate_service_start,
        validate_service_end,
        lambda d: validate_categories(
            d, "service_type",
            ["Account Support", "New Membership",
             "Loan Support", "Card Support",
             "General Inquiry", "Fraud Support"]
        ),
        lambda d: validate_categories(
            d, "outcome",
            ["Resolved", "Escalated",
             "Follow-Up Required", "Abandoned"]
        ),
        validate_duplicate_records,
    ])


def validate_staffing(df, branches):
    """Validate daily staffing data."""
    return run_validation_checks(df, [
        lambda d: validate_required_fields(
            d, ["branch_id", "work_date",
                "scheduled_employees", "actual_employees",
                "employee_hours"]
        ),
        lambda d: validate_branch_references(d, branches),
        lambda d: validate_timestamps(d, "work_date"),
        lambda d: validate_future_timestamps(d, "work_date"),
        validate_staffing_counts,
        validate_employee_hours,
        validate_duplicate_records,
    ])


def validate_all(datasets):
    """Validate all datasets and return valid/rejected results."""
    results = {}

    valid_branches, rejected_branches = validate_branches(
        datasets["branches"]
    )

    results["branches"] = (valid_branches, rejected_branches)

    validators = {
        "transactions": validate_transactions,
        "member_visits": validate_member_visits,
        "staffing": validate_staffing,
    }

    for name, validator in validators.items():
        valid, rejected = validator(
            datasets[name], valid_branches
        )
        results[name] = (valid, rejected)

    return results


# Before loading data into PostgreSQL's analytical tables, we'll save rejected records as CSV files for auditing.

from pathlib import Path


def export_rejected_records(results):
    """Export rejected records for auditing."""
    output_dir = Path("data/rejected")
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, (valid, rejected) in results.items():
        file_path = output_dir / f"{name}_rejected.csv"

        if not rejected.empty:
            rejected.to_csv(file_path, index=False)
            print(f"Exported {len(rejected)} rejected records: {file_path}")
        else:
            print(f"No rejected records for {name}")
