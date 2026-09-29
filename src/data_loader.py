
from pathlib import Path

import pandas as pd


# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Dataset directory
DATA_DIR = BASE_DIR / "data"


def load_data():
    """
    Load all Vireo Audio CSV datasets.
    """

    datasets = {
        "tickets": "tickets.csv",
        "agents": "agents.csv",
        "customers": "customers.csv",
        "orders": "orders.csv",
        "products": "products.csv",
    }

    data = {}

    for name, filename in datasets.items():

        file_path = DATA_DIR / filename

        if not file_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {file_path}"
            )

        data[name] = pd.read_csv(file_path)

        print(f"Loaded {name}: {data[name].shape}")

    return data


def inspect_data(data):
    """
    Display basic information about each dataset.
    """

    for name, df in data.items():

        print("\n" + "=" * 60)
        print(f"DATASET: {name.upper()}")
        print("=" * 60)

        print("\nShape:")
        print(df.shape)

        print("\nColumns:")
        print(df.columns.tolist())

        print("\nData Types:")
        print(df.dtypes)

        print("\nMissing Values:")
        print(df.isnull().sum())

        print("\nFirst 5 Rows:")
        print(df.head())


def inspect_ticket_duplicates(tickets):
    """
    Check duplicate ticket IDs.
    """

    print("\n" + "=" * 60)
    print("TICKET DUPLICATE ANALYSIS")
    print("=" * 60)

    duplicate_count = tickets["ticket_id"].duplicated().sum()

    print(f"Total ticket records: {len(tickets)}")
    print(f"Duplicate ticket IDs: {duplicate_count}")

    duplicate_rows = tickets[
        tickets["ticket_id"].duplicated(keep=False)
    ]

    print("\nSample duplicate records:")
    print(duplicate_rows.head(10))


if __name__ == "__main__":

    print("VIREO AUDIO - DATA INSPECTION")
    print("=" * 60)

    datasets = load_data()

    inspect_data(datasets)

    inspect_ticket_duplicates(datasets["tickets"])

    print("\nData inspection completed successfully!")