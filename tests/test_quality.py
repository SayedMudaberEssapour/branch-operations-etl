
"""Automated tests for all 15 data-quality rules."""

import pandas as pd
import pytest

from src.extract import extract_all
from src import quality as q


@pytest.mark.parametrize(
    "rule,validator,records,expected",
    [
        (
            "DQ001",
            lambda d: q.validate_required_ids(d, "transaction_id"),
            {"transaction_id": ["TX1", ""]},
            1,
        ),
        (
            "DQ002",
            lambda d: q.validate_duplicate_ids(d, "transaction_id"),
            {"transaction_id": ["TX1", "TX1"]},
            1,
        ),
        (
            "DQ003",
            lambda d: q.validate_branch_references(
                d, pd.DataFrame({"branch_id": ["BR001"]})
            ),
            {"branch_id": ["BR001", "BR999"]},
            1,
        ),
        (
            "DQ004",
            lambda d: q.validate_timestamps(d, "timestamp"),
            {"timestamp": ["2026-01-01", "not-a-date"]},
            1,
        ),
        (
            "DQ005",
            lambda d: q.validate_future_timestamps(d, "timestamp"),
            {"timestamp": ["2020-01-01", "2099-01-01"]},
            1,
        ),
        (
            "DQ006",
            q.validate_transaction_amounts,
            {"amount": ["100", "-50"]},
            1,
        ),
        (
            "DQ007",
            q.validate_processing_time,
            {"processing_seconds": ["120", "-10"]},
            1,
        ),
        (
            "DQ008",
            q.validate_service_start,
            {
                "arrival_timestamp": [
                    "2026-01-01T09:00:00",
                    "2026-01-01T10:00:00",
                ],
                "service_start_timestamp": [
                    "2026-01-01T09:05:00",
                    "2026-01-01T09:55:00",
                ],
            },
            1,
        ),
        (
            "DQ009",
            q.validate_service_end,
            {
                "service_start_timestamp": [
                    "2026-01-01T09:00:00",
                    "2026-01-01T10:00:00",
                ],
                "service_end_timestamp": [
                    "2026-01-01T09:20:00",
                    "2026-01-01T09:55:00",
                ],
            },
            1,
        ),
        (
            "DQ010",
            lambda d: q.validate_categories(
                d, "status", ["Completed", "Pending"]
            ),
            {"status": ["Completed", "Unknown"]},
            1,
        ),
        (
            "DQ011",
            q.validate_staffing_counts,
            {
                "scheduled_employees": ["5", "5"],
                "actual_employees": ["4", "-2"],
            },
            1,
        ),
        (
            "DQ012",
            q.validate_employee_hours,
            {
                "actual_employees": ["4", "4"],
                "employee_hours": ["32", "-8"],
            },
            1,
        ),
        (
            "DQ013",
            lambda d: q.validate_required_fields(
                d, ["branch_id", "amount"]
            ),
            {
                "branch_id": ["BR001", "BR001"],
                "amount": ["100", ""],
            },
            1,
        ),
        (
            "DQ014",
            q.validate_duplicate_records,
            {
                "transaction_id": ["TX1", "TX1"],
                "amount": ["100", "100"],
            },
            1,
        ),
        (
            "DQ015",
            q.validate_active_flag,
            {"active_flag": ["Y", "INVALID"]},
            1,
        ),
    ],
)
def test_data_quality_rule(rule, validator, records, expected):
    df = pd.DataFrame(records)
    valid, rejected = validator(df)

    assert len(rejected) == expected
    assert len(valid) + len(rejected) == len(df)
    assert set(rejected["rule_id"]) == {rule}


def test_full_validation_pipeline():
    datasets = extract_all()
    results = q.validate_all(datasets)

    assert set(results) == {
        "branches", "transactions",
        "member_visits", "staffing"
    }

    for name, (valid, rejected) in results.items():
        assert len(valid) + len(rejected) == len(datasets[name])
        assert valid.index.is_unique

    # Confirm the intentionally corrupted data is detected.
    assert len(results["transactions"][1]) > 0
    assert len(results["member_visits"][1]) > 0
    assert len(results["staffing"][1]) > 0
