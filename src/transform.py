
"""Prepare extracted records for PostgreSQL staging."""

import hashlib
import json
from datetime import datetime, timezone

# -- Add tracking information to every extracted record so we know which pipeline execution and CSV row it came from


def add_staging_metadata(df, source_file, pipeline_run_id):
    """Attach audit metadata to extracted source records."""
    result = df.copy()

    # Hash only the original source columns.
    source_columns = list(df.columns)

    def create_hash(row):
        record = {
            col: row[col]
            for col in source_columns
        }
        payload = json.dumps(
            record,
            sort_keys=True,
            ensure_ascii=False
        )
        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()

    result["pipeline_run_id"] = pipeline_run_id
    result["source_file_name"] = source_file
    result["source_row_number"] = range(2, len(result) + 2)
    result["ingestion_timestamp"] = datetime.now(timezone.utc)
    result["record_hash"] = df.apply(create_hash, axis=1)

    return result
