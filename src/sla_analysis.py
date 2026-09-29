from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path("outputs")

SLA_TARGET_MINUTES = {
    "chat": 15,
    "voice": 120,
    "social": 240,
    "email": 480,
}


def load_cleaned_tickets() -> pd.DataFrame:
    path = OUTPUT_DIR / "cleaned_tickets.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: uv run python -m src.prepare_data"
        )

    tickets = pd.read_csv(path)

    tickets["created_at"] = pd.to_datetime(
        tickets["created_at"],
        errors="coerce",
        utc=True,
    )

    tickets["first_response_at"] = pd.to_datetime(
        tickets["first_response_at"],
        errors="coerce",
        utc=True,
    )

    # Source timestamps are UTC. Convert to IST for reporting.
    tickets["created_at_ist"] = tickets["created_at"].dt.tz_convert(
        "Asia/Kolkata"
    )

    tickets["first_response_at_ist"] = (
        tickets["first_response_at"].dt.tz_convert("Asia/Kolkata")
    )

    tickets["created_date_ist"] = (
        tickets["created_at_ist"].dt.date
    )

    return tickets


def load_agent_roster() -> pd.DataFrame:
    roster = pd.read_csv("data/agents.csv")

    roster["from_date"] = pd.to_datetime(
        roster["from_date"],
        errors="coerce",
    )

    roster["to_date"] = pd.to_datetime(
        roster["to_date"],
        errors="coerce",
    )

    return roster


def match_agent_roster(
    tickets: pd.DataFrame,
    roster: pd.DataFrame,
) -> pd.DataFrame:
    """
    Match each ticket to the agent roster assignment effective on
    the ticket's creation date in IST.

    from_date and to_date are inclusive.
    A missing to_date means the assignment is open-ended.
    """

    roster_columns = [
        "agent_id",
        "name",
        "site",
        "team",
        "shift",
        "tier",
        "from_date",
        "to_date",
    ]

    roster_for_join = roster[roster_columns].copy()

    merged = tickets.merge(
        roster_for_join,
        on="agent_id",
        how="left",
        indicator=True,
    )

    merged["_created_date"] = pd.to_datetime(
        merged["created_date_ist"],
        errors="coerce",
    )

    start_match = (
        merged["_created_date"].notna()
        & merged["from_date"].notna()
        & merged["_created_date"].ge(merged["from_date"])
    )

    end_match = (
        merged["to_date"].isna()
        | merged["_created_date"].le(merged["to_date"])
    )

    matched = merged[start_match & end_match].copy()

    match_counts = matched.groupby("ticket_id").size()

    ambiguous_ids = match_counts[
        match_counts > 1
    ].index.tolist()

    if ambiguous_ids:
        raise ValueError(
            "Some tickets matched multiple effective roster rows. "
            f"Example ticket IDs: {ambiguous_ids[:10]}"
        )

    matched_ticket_ids = set(matched["ticket_id"])

    unmatched = tickets[
        ~tickets["ticket_id"].isin(matched_ticket_ids)
    ].copy()

    if not unmatched.empty:
        for column in [
            "name",
            "site",
            "team",
            "shift",
            "tier",
            "from_date",
            "to_date",
        ]:
            unmatched[column] = pd.NA

        unmatched["roster_match_status"] = "unmatched"

    matched["roster_match_status"] = "matched"

    matched = matched.drop(
        columns=["_created_date", "_merge"],
        errors="ignore",
    )

    result = pd.concat(
        [matched, unmatched],
        ignore_index=True,
        sort=False,
    )

    if result["ticket_id"].nunique() != tickets["ticket_id"].nunique():
        raise ValueError(
            "Ticket count changed during roster matching. "
            "Please investigate the roster join."
        )

    return result


def calculate_sla(tickets: pd.DataFrame) -> pd.DataFrame:
    data = tickets.copy()

    data["channel"] = (
        data["channel"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    data["sla_target_minutes"] = data["channel"].map(
        SLA_TARGET_MINUTES
    )

    data["first_response_minutes"] = (
        data["first_response_at"] - data["created_at"]
    ).dt.total_seconds() / 60

    data["sla_status"] = "unknown_channel"

    known_channel = data["sla_target_minutes"].notna()

    valid_response = (
        data["first_response_minutes"].notna()
        & data["first_response_minutes"].ge(0)
    )

    valid_sla = known_channel & valid_response

    data.loc[valid_sla, "sla_status"] = "met"

    breached = (
        valid_sla
        & (
            data["first_response_minutes"]
            > data["sla_target_minutes"]
        )
    )

    data.loc[breached, "sla_status"] = "breached"

    data["sla_breached"] = data["sla_status"].eq("breached")

    data["created_week_ist"] = (
        data["created_at_ist"].dt.strftime("%G-W%V")
    )

    return data


def create_summary(tickets: pd.DataFrame) -> pd.DataFrame:
    """
    Group by channel so every summary row has one consistent SLA target.
    """

    eligible = tickets[
        tickets["sla_status"].isin(["met", "breached"])
    ].copy()

    group_columns = [
        "created_week_ist",
        "channel",
        "site",
        "team",
        "tier",
        "shift",
        "agent_id",
        "name",
    ]

    summary = (
        eligible.groupby(
            group_columns,
            dropna=False,
        )
        .agg(
            ticket_count=("ticket_id", "nunique"),
            breached_tickets=("sla_breached", "sum"),
            average_response_minutes=(
                "first_response_minutes",
                "mean",
            ),
            median_response_minutes=(
                "first_response_minutes",
                "median",
            ),
            sla_target_minutes=("sla_target_minutes", "first"),
        )
        .reset_index()
    )

    summary["sla_breach_rate_pct"] = (
        summary["breached_tickets"]
        / summary["ticket_count"]
        * 100
    )

    summary["sla_met_rate_pct"] = (
        100 - summary["sla_breach_rate_pct"]
    )

    return summary.sort_values(
        by=[
            "created_week_ist",
            "channel",
            "site",
            "team",
            "shift",
            "agent_id",
        ],
        na_position="last",
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    tickets = load_cleaned_tickets()
    roster = load_agent_roster()

    print(f"Loaded cleaned tickets: {len(tickets):,}")
    print(f"Loaded roster rows: {len(roster):,}")

    tickets = match_agent_roster(tickets, roster)
    tickets = calculate_sla(tickets)

    summary = create_summary(tickets)

    ticket_output = OUTPUT_DIR / "ticket_sla_analysis.csv"
    summary_output = OUTPUT_DIR / "weekly_sla_summary.csv"

    tickets.to_csv(ticket_output, index=False)
    summary.to_csv(summary_output, index=False)

    print("\nSLA analysis completed.")
    print(f"Ticket-level output: {ticket_output}")
    print(f"Weekly summary output: {summary_output}")

    print("\nRoster match status:")
    print(
        tickets["roster_match_status"].value_counts(dropna=False)
    )

    print("\nSLA status:")
    print(tickets["sla_status"].value_counts(dropna=False))

    print("\nOverall eligible-ticket metrics:")

    eligible = tickets[
        tickets["sla_status"].isin(["met", "breached"])
    ]

    if not eligible.empty:
        total = eligible["ticket_id"].nunique()
        breached = int(eligible["sla_breached"].sum())
        breach_rate = breached / total * 100

        print(f"Eligible tickets: {total:,}")
        print(f"Breached tickets: {breached:,}")
        print(f"Breach rate: {breach_rate:.2f}%")
    else:
        print("No eligible tickets found.")

    print(f"\nFinal ticket-level shape: {tickets.shape}")
    print(f"Final summary shape: {summary.shape}")


if __name__ == "__main__":
    main()