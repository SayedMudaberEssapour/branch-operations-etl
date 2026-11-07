'''Phase 10 — Checkpoint 10.1: Create the ETL Orchestrator
Goal: Run extraction, validation, rejection exports, and warehouse loading using a single Python command.'''



"""Main orchestration entry point for the ETL pipeline."""

import logging
import sys
from datetime import datetime, timezone

from src.extract import extract_all
from src.quality import validate_all, export_rejected_records
from src.load import (
    load_staging,
    load_quality_exceptions,
    load_branch_dimension,
    load_transaction_facts,
    load_member_visit_facts,
    load_staffing_facts,
)


def run_pipeline():
    """Execute the branch operations ETL workflow."""
    start = datetime.now(timezone.utc)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    try:
        logging.info("Starting branch operations ETL")

        # 1. Extract and validate
        datasets = extract_all()
        results = validate_all(datasets)

        total_valid = sum(
            len(valid) for valid, rejected in results.values()
        )
        total_rejected = sum(
            len(rejected) for valid, rejected in results.values()
        )

        logging.info(
            "Validation complete: %s valid, %s rejected",
            total_valid,
            total_rejected
        )

        # 2. Export rejected records
        export_rejected_records(results)

        # 3. Load staging and audit exceptions
        load_staging()
        load_quality_exceptions()

        # 4. Load analytical warehouse
        load_branch_dimension()
        load_transaction_facts()
        load_member_visit_facts()
        load_staffing_facts()

        elapsed = (
            datetime.now(timezone.utc) - start
        ).total_seconds()

        logging.info(
            "ETL completed successfully in %.2f seconds",
            elapsed
        )

    except Exception:
        logging.exception("ETL pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
