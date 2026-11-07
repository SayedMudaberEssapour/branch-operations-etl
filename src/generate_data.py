
"""Generate reproducible synthetic branch operations data."""

# This file has functions that generate synthetic data for branches, transactions, member visits, and staffing records.
# we have also included interntional data-quality erros.

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("data/raw")
RANDOM_SEED = 42


def generate_branches():
    """Create 10 fictional branch records."""
    random.seed(RANDOM_SEED)

    names = [
        "Arlington Central",
        "Potomac Square",
        "Capital Gateway",
        "Blue Ridge Center",
        "Chesapeake Point",
        "Fairfax Commons",
        "Alexandria Harbor",
        "Reston Plaza",
        "Springfield Center",
        "Tysons Crossing",
    ]

    regions = ["Northern", "Central", "Eastern"]
    branch_types = ["Urban", "Suburban", "Community"]

    records = []

    for i, name in enumerate(names, start=1):
        records.append({
            "branch_id": f"BR{i:03d}",
            "branch_name": name,
            "region": random.choice(regions),
            "branch_type": random.choice(branch_types),
            "open_date": (
                date(2015, 1, 1)
                + timedelta(days=random.randint(0, 3000))
            ).isoformat(),
            "active_flag": "Y",
        })

    return pd.DataFrame(records)




# This function will be generating 7,500 synthetic transactions across 10 branches and 30 days.
def generate_transactions(branches, count=7500):
    """Generate reproducible synthetic transactions."""
    rng = random.Random(RANDOM_SEED)

    transaction_types = [
        "Deposit", "Withdrawal", "Transfer",
        "Account Payment", "Cashier Check",
        "Account Maintenance"
    ]
    channels = ["Teller", "ATM", "Self-Service", "Appointment"]
    statuses = ["Completed", "Failed", "Reversed", "Pending"]

    start_date = date.today() - timedelta(days=30)
    records = []

    for i in range(1, count + 1):
        transaction_date = start_date + timedelta(
            days=rng.randint(0, 29)
        )

        timestamp = (
            pd.Timestamp(transaction_date)
            + pd.Timedelta(hours=rng.randint(8, 17))
            + pd.Timedelta(minutes=rng.randint(0, 59))
        )

        records.append({
            "transaction_id": f"TXN{i:06d}",
            "branch_id": rng.choice(branches["branch_id"].tolist()),
            "transaction_timestamp": timestamp.isoformat(),
            "transaction_type": rng.choice(transaction_types),
            "channel": rng.choice(channels),
            "amount": round(rng.uniform(10, 5000), 2),
            "processing_seconds": rng.randint(30, 900),
            "status": rng.choices(
                statuses, weights=[85, 5, 5, 5], k=1
            )[0],
        })

    return pd.DataFrame(records)


# Generating 3,000 synthetic member visits, including arrival, service start, and service end times.
def generate_member_visits(branches, count=3000):
    """Generate synthetic member visits with valid service times."""
    rng = random.Random(RANDOM_SEED + 1)

    service_types = [
        "Account Support", "New Membership",
        "Loan Support", "Card Support",
        "General Inquiry", "Fraud Support"
    ]

    outcomes = [
        "Resolved", "Escalated",
        "Follow-Up Required", "Abandoned"
    ]

    start_date = date.today() - timedelta(days=30)
    branch_ids = branches["branch_id"].tolist()
    records = []

    for i in range(1, count + 1):
        visit_date = start_date + timedelta(
            days=rng.randint(0, 29)
        )

        arrival = (
            pd.Timestamp(visit_date)
            + pd.Timedelta(hours=rng.randint(8, 16))
            + pd.Timedelta(minutes=rng.randint(0, 59))
        )

        wait_minutes = rng.randint(0, 30)
        service_minutes = rng.randint(5, 60)

        service_start = arrival + pd.Timedelta(
            minutes=wait_minutes
        )
        service_end = service_start + pd.Timedelta(
            minutes=service_minutes
        )

        records.append({
            "visit_id": f"VIS{i:06d}",
            "branch_id": rng.choice(branch_ids),
            "arrival_timestamp": arrival.isoformat(),
            "service_start_timestamp": service_start.isoformat(),
            "service_end_timestamp": service_end.isoformat(),
            "service_type": rng.choice(service_types),
            "outcome": rng.choices(
                outcomes,
                weights=[75, 10, 10, 5],
                k=1
            )[0]
        })

    return pd.DataFrame(records)



# Generating 300 staffind records (10 branches x 30 days) to measure staffind coverage and productivity.
def generate_staffing(branches):
    """Generate 30 days of synthetic staffing records."""
    rng = random.Random(RANDOM_SEED + 2)

    start_date = date.today() - timedelta(days=30)
    records = []

    for branch_id in branches["branch_id"]:
        for day in range(30):
            work_date = start_date + timedelta(days=day)

            scheduled = rng.randint(5, 15)
            actual = max(0, scheduled + rng.randint(-3, 2))
            employee_hours = actual * rng.uniform(6, 8)

            records.append({
                "branch_id": branch_id,
                "work_date": work_date.isoformat(),
                "scheduled_employees": scheduled,
                "actual_employees": actual,
                "employee_hours": round(employee_hours, 2)
            })

    return pd.DataFrame(records)



#THis function will introduce approximately 2% invalide records into our synthetic datasets so we can test the 15 data-quality rules.

def inject_data_quality_errors(
    transactions, visits, staffing, error_rate=0.02
):
    """Inject reproducible errors into synthetic datasets."""
    if not 0 <= error_rate <= 1:
        raise ValueError("error_rate must be between 0 and 1")

    rng = random.Random(RANDOM_SEED + 3)

    transactions = transactions.copy()
    visits = visits.copy()
    staffing = staffing.copy()

    # Transaction errors
    tx_errors = [
        ("duplicate_id", lambda i: transactions.at.__call__),
        ("missing_branch", None),
        ("unknown_branch", None),
        ("negative_amount", None),
        ("invalid_timestamp", None),
        ("future_timestamp", None),
        ("negative_processing", None),
        ("invalid_status", None),
        ("missing_id", None),
    ]

    tx_indices = rng.sample(
        list(transactions.index),
        int(len(transactions) * error_rate)
    )

    for n, i in enumerate(tx_indices):
        error_type = n % len(tx_errors)

        if error_type == 0:
            transactions.at[i, "transaction_id"] = transactions.at[
                0, "transaction_id"
            ]
        elif error_type == 1:
            transactions.at[i, "branch_id"] = None
        elif error_type == 2:
            transactions.at[i, "branch_id"] = "BR999"
        elif error_type == 3:
            transactions.at[i, "amount"] = -100
        elif error_type == 4:
            transactions.at[i, "transaction_timestamp"] = "invalid-date"
        elif error_type == 5:
            transactions.at[i, "transaction_timestamp"] = (
                pd.Timestamp.now() + pd.Timedelta(days=30)
            ).isoformat()
        elif error_type == 6:
            transactions.at[i, "processing_seconds"] = -10
        elif error_type == 7:
            transactions.at[i, "status"] = "Unknown"
        else:
            transactions.at[i, "transaction_id"] = None

    # Member visit errors
    visit_indices = rng.sample(
        list(visits.index),
        int(len(visits) * error_rate)
    )

    for n, i in enumerate(visit_indices):
        if n % 3 == 0:
            visits.at[i, "service_start_timestamp"] = (
                pd.Timestamp(
                    visits.at[i, "arrival_timestamp"]
                ) - pd.Timedelta(minutes=10)
            ).isoformat()
        elif n % 3 == 1:
            visits.at[i, "service_end_timestamp"] = (
                pd.Timestamp(
                    visits.at[i, "service_start_timestamp"]
                ) - pd.Timedelta(minutes=5)
            ).isoformat()
        else:
            visits.at[i, "service_type"] = "Invalid Service"

    # Staffing errors
    staffing_indices = rng.sample(
        list(staffing.index),
        int(len(staffing) * error_rate)
    )

    for n, i in enumerate(staffing_indices):
        if n % 2 == 0:
            staffing.at[i, "actual_employees"] = -2
        else:
            staffing.at[i, "employee_hours"] = -8

    return transactions, visits, staffing



# This function Adds inconsistent capitalization, leading/trailing spaces, and exact duplicate source records.
def inject_formatting_errors(transactions):
    """Add reproducible formatting and duplicate-record issues."""
    transactions = transactions.copy()

    # Formatting inconsistencies
    transactions.at[1, "transaction_type"] = " deposit "
    transactions.at[2, "channel"] = " teller "
    transactions.at[3, "status"] = "completed"

    # Duplicate an entire source record
    duplicate = transactions.iloc[[4]].copy()

    return pd.concat(
        [transactions, duplicate],
        ignore_index=True
    )


def main():
    """Generate all four synthetic source datasets."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    branches = generate_branches()
    transactions = generate_transactions(branches)
    visits = generate_member_visits(branches)
    staffing = generate_staffing(branches)
    transactions, visits, staffing = inject_data_quality_errors(
    transactions, visits, staffing)
    transactions = inject_formatting_errors(transactions)

    branches.to_csv(OUTPUT_DIR / "branches.csv", index=False)
    transactions.to_csv(OUTPUT_DIR / "transactions.csv", index=False)
    visits.to_csv(OUTPUT_DIR / "member_visits.csv", index=False)
    staffing.to_csv(OUTPUT_DIR / "staffing.csv", index=False)

    print(f"Generated {len(branches)} branches")
    print(f"Generated {len(transactions)} transactions")
    print(f"Generated {len(visits)} member visits")
    print(f"Generated {len(staffing)} staffing records")





if __name__ == "__main__":
    main()
