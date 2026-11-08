
"""Extract synthetic branch operations data from CSV files."""

# here I am reading all four source CSV files into Python using pandas.


# dtype=str preserves malformed values for later validation.
# keep_default_na=False lets us explicitly detect missing fields.
# extract_all() provides one reusable extraction function for our ETL pipeline.

from pathlib import Path

import pandas as pd


RAW_DATA_DIR = Path("data/raw")

SOURCE_FILES = {
    "branches": "branches.csv",
    "transactions": "transactions.csv",
    "member_visits": "member_visits.csv",
    "staffing": "staffing.csv",
}


def extract_csv(file_path):
    """Read a CSV file while preserving raw values as strings."""
    if not file_path.exists():
        raise FileNotFoundError(f"Missing source file: {file_path}")

    return pd.read_csv(
        file_path,
        dtype=str,
        keep_default_na=False
    )


def extract_all():
    """Extract all four source datasets."""
    datasets = {}

    for name, filename in SOURCE_FILES.items():
        file_path = RAW_DATA_DIR / filename
        datasets[name] = extract_csv(file_path)

        print(f"Extracted {name}: {len(datasets[name])} rows")

    return datasets


if __name__ == "__main__":
    extract_all()
