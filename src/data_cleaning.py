import pandas as pd

from src.data_loader import load_data


def inspect_duplicate_records(tickets):
    """
    Investigate duplicate ticket IDs before deduplication.
    Do not remove records during this diagnostic step.
    """

    print("\n" + "=" * 60)
    print("DUPLICATE TICKET INVESTIGATION")
    print("=" * 60)

    duplicated = tickets[
        tickets.duplicated(subset="ticket_id", keep=False)
    ].copy()

    duplicate_groups = duplicated.groupby("ticket_id")

    print(f"Total ticket records: {len(tickets)}")
    print(f"Rows involved in duplicate groups: {len(duplicated)}")
    print(f"Duplicate ticket IDs: {duplicate_groups.ngroups}")

    comparison_columns = [
        column
        for column in tickets.columns
        if column not in ["ticket_id", "source_system"]
    ]

    comparison_results = []

    for ticket_id, group in duplicate_groups:
        identical = (
            group[comparison_columns]
            .nunique(dropna=False)
            .eq(1)
            .all()
        )

        comparison_results.append({
            "ticket_id": ticket_id,
            "record_count": len(group),
            "sources": ", ".join(
                sorted(group["source_system"].dropna().unique())
            ),
            "identical_except_source": identical,
        })

    comparison_df = pd.DataFrame(comparison_results)

    print("\nDuplicate comparison summary:")
    print(
        comparison_df["identical_except_source"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nSample duplicate comparison:")
    print(comparison_df.head(10).to_string(index=False))

    print("\nDuplicate source combinations:")
    print(comparison_df["sources"].value_counts().to_string())

    return comparison_df


def inspect_duplicate_differences(tickets):
    """
    Identify which fields differ between duplicate ticket IDs.
    This function only reports differences; it does not modify data.
    """

    print("\n" + "=" * 60)
    print("DUPLICATE FIELD DIFFERENCES")
    print("=" * 60)

    duplicate_rows = tickets[
        tickets.duplicated(subset="ticket_id", keep=False)
    ].copy()

    comparison_columns = [
        column
        for column in tickets.columns
        if column not in ["ticket_id", "source_system"]
    ]

    differing_records = []

    for ticket_id, group in duplicate_rows.groupby("ticket_id"):

        if len(group) != 2:
            continue

        first = group.iloc[0]
        second = group.iloc[1]

        different_fields = []

        for column in comparison_columns:
            value1 = first[column]
            value2 = second[column]

            # Two missing values are considered equal.
            if pd.isna(value1) and pd.isna(value2):
                continue

            if value1 != value2:
                different_fields.append(column)

        if different_fields:
            differing_records.append({
                "ticket_id": ticket_id,
                "sources": ", ".join(
                    sorted(group["source_system"].dropna().unique())
                ),
                "different_fields": ", ".join(different_fields),
                "number_of_differences": len(different_fields),
            })

    differences_df = pd.DataFrame(
        differing_records,
        columns=[
            "ticket_id",
            "sources",
            "different_fields",
            "number_of_differences",
        ],
    )

    print(f"Duplicate pairs with differences: {len(differences_df)}")

    if differences_df.empty:
        print("No differing duplicate pairs found.")
        return differences_df

    print("\nFields most often different:")

    field_counts = (
        differences_df["different_fields"]
        .str.split(", ")
        .explode()
        .value_counts()
    )

    print(field_counts.to_string())

    print("\nSample differing duplicate pairs:")
    print(differences_df.head(15).to_string(index=False))

    return differences_df


def inspect_duplicate_csat_values(tickets):
    """
    Compare CSAT values between duplicate helpdesk and legacy records.
    This function only investigates values; it does not modify data.
    """

    print("\n" + "=" * 60)
    print("DUPLICATE CSAT VALUE INVESTIGATION")
    print("=" * 60)

    duplicate_rows = tickets[
        tickets.duplicated(subset="ticket_id", keep=False)
    ].copy()

    csat_records = []

    for ticket_id, group in duplicate_rows.groupby("ticket_id"):

        if len(group) != 2:
            continue

        helpdesk_row = group[
            group["source_system"] == "helpdesk"
        ]

        legacy_row = group[
            group["source_system"] == "legacy_fd"
        ]

        if helpdesk_row.empty or legacy_row.empty:
            continue

        helpdesk_csat = helpdesk_row.iloc[0]["csat_score"]
        legacy_csat = legacy_row.iloc[0]["csat_score"]

        csat_records.append({
            "ticket_id": ticket_id,
            "helpdesk_csat": helpdesk_csat,
            "legacy_csat": legacy_csat,
        })

    csat_df = pd.DataFrame(
        csat_records,
        columns=[
            "ticket_id",
            "helpdesk_csat",
            "legacy_csat",
        ],
    )

    print("Duplicate pairs compared:", len(csat_df))

    if csat_df.empty:
        print("No helpdesk/legacy duplicate pairs available for comparison.")
        return csat_df

    print("\nHelpdesk CSAT value counts:")
    print(
        csat_df["helpdesk_csat"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nLegacy CSAT value counts:")
    print(
        csat_df["legacy_csat"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nHelpdesk vs legacy CSAT combinations:")
    print(
        csat_df.groupby(
            ["helpdesk_csat", "legacy_csat"],
            dropna=False,
        )
        .size()
        .sort_values(ascending=False)
        .to_string()
    )

    # Compare values while treating two missing values as equal.
    both_missing = (
        csat_df["helpdesk_csat"].isna()
        & csat_df["legacy_csat"].isna()
    )

    same_value = (
        csat_df["helpdesk_csat"].eq(csat_df["legacy_csat"])
        | both_missing
    )

    differing = csat_df[~same_value]

    print("\nDuplicate pairs with different CSAT values:", len(differing))
    print("\nSample pairs where CSAT differs:")

    if differing.empty:
        print("No CSAT differences found.")
    else:
        print(differing.head(20).to_string(index=False))

    return csat_df


def inspect_timestamps(tickets):
    """
    Inspect timestamp completeness and valid ranges.
    """

    print("\n" + "=" * 60)
    print("TIMESTAMP INVESTIGATION")
    print("=" * 60)

    timestamp_columns = [
        "created_at",
        "first_response_at",
        "resolved_at",
    ]

    for column in timestamp_columns:
        parsed = pd.to_datetime(
            tickets[column],
            errors="coerce",
        )

        print(f"\n{column}")
        print("Missing or invalid values:", parsed.isna().sum())
        print("Earliest:", parsed.min())
        print("Latest:", parsed.max())


def inspect_voice_tickets(tickets):
    """
    Count voice tickets and inspect their statuses and source systems.
    """

    print("\n" + "=" * 60)
    print("VOICE TICKET INVESTIGATION")
    print("=" * 60)

    voice_tickets = tickets[
        tickets["channel"].str.lower() == "voice"
    ]

    print("Total voice ticket records:", len(voice_tickets))

    print("\nVoice ticket status:")
    print(voice_tickets["status"].value_counts().to_string())

    print("\nVoice source system:")
    print(voice_tickets["source_system"].value_counts().to_string())


def main():
    """
    Run all data-quality investigations.
    """

    datasets = load_data()
    tickets = datasets["tickets"]

    inspect_duplicate_records(tickets)
    inspect_duplicate_differences(tickets)
    inspect_duplicate_csat_values(tickets)
    inspect_timestamps(tickets)
    inspect_voice_tickets(tickets)

    print("\nData quality investigation completed.")


if __name__ == "__main__":
    main()