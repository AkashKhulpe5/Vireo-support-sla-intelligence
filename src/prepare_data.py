from pathlib import Path

import pandas as pd

from src.data_loader import load_data


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "outputs"


# ---------------------------------------------------------
# Prepare and clean ticket data
# ---------------------------------------------------------
def prepare_tickets(tickets: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize CSAT, deduplicate migrated ticket records,
    parse timestamps, and create basic quality checks.
    """

    print("\n" + "=" * 60)
    print("PREPARING TICKET DATA")
    print("=" * 60)

    data = tickets.copy()

    original_count = len(data)

    # 1. Normalize legacy CSAT zero.
    # Assignment policy: legacy 0 means no customer response.
    legacy_mask = data["source_system"].eq("legacy_fd")
    legacy_zero_mask = legacy_mask & data["csat_score"].eq(0)

    legacy_zero_count = int(legacy_zero_mask.sum())

    data.loc[legacy_zero_mask, "csat_score"] = pd.NA

    print(
        "Legacy CSAT zero values normalized to missing:",
        legacy_zero_count,
    )

    # 2. Check that duplicate ticket IDs agree on all fields
    # except source_system, after CSAT normalization.
    comparison_columns = [
        column
        for column in data.columns
        if column not in ["ticket_id", "source_system"]
    ]

    duplicate_rows = data[
        data.duplicated(subset="ticket_id", keep=False)
    ]

    conflicting_ticket_ids = []

    for ticket_id, group in duplicate_rows.groupby("ticket_id"):
        if len(group[comparison_columns].drop_duplicates()) > 1:
            conflicting_ticket_ids.append(ticket_id)

    print(
        "Duplicate ticket IDs with conflicting details:",
        len(conflicting_ticket_ids),
    )

    if conflicting_ticket_ids:
        raise ValueError(
            "Some duplicate ticket IDs have conflicting details. "
            "Review them before deduplication."
        )

    # 3. Prefer helpdesk rows where a ticket exists in both systems.
    # This is safe for the observed duplicates because their ticket
    # details match after normalizing legacy CSAT zero.
    data["_source_priority"] = data["source_system"].map({
        "helpdesk": 0,
        "legacy_fd": 1,
    }).fillna(2)

    data = data.sort_values(
        by=["ticket_id", "_source_priority"]
    )

    data = data.drop_duplicates(
        subset="ticket_id",
        keep="first",
    ).copy()

    data = data.drop(columns=["_source_priority"])

    deduplicated_count = len(data)
    removed_count = original_count - deduplicated_count

    print("Original ticket records:", original_count)
    print("Records after deduplication:", deduplicated_count)
    print("Duplicate rows removed:", removed_count)

    # 4. Parse timestamps.
    # Source files specify timestamps are UTC.
    timestamp_columns = [
        "created_at",
        "first_response_at",
        "resolved_at",
    ]

    for column in timestamp_columns:
        data[column] = pd.to_datetime(
            data[column],
            errors="coerce",
            utc=True,
        )

    # 5. Validate first response does not precede ticket creation.
    invalid_response_order = (
        data["first_response_at"] < data["created_at"]
    )

    invalid_response_order = invalid_response_order.fillna(False)

    print(
        "Tickets with first response before creation:",
        int(invalid_response_order.sum()),
    )

    # 6. Normalize CSAT values that mean no response.
    # Legacy zeros have already been converted above.
    data["csat_score"] = data["csat_score"].replace(0, pd.NA)

    print(
        "Missing CSAT after normalization:",
        int(data["csat_score"].isna().sum()),
    )

    print(
        "Remaining duplicate ticket IDs:",
        int(data["ticket_id"].duplicated().sum()),
    )

    return data


# ---------------------------------------------------------
# Main preparation pipeline
# ---------------------------------------------------------
def main():
    datasets = load_data()
    tickets = datasets["tickets"]

    cleaned_tickets = prepare_tickets(tickets)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / "cleaned_tickets.csv"

    cleaned_tickets.to_csv(output_path, index=False)

    print("\nCleaned ticket data saved to:", output_path)
    print("Final shape:", cleaned_tickets.shape)
    print("\nData preparation completed successfully.")


if __name__ == "__main__":
    main()