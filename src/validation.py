from pathlib import Path
import json

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
TICKET_FILE = BASE_DIR / "outputs" / "ticket_sla_analysis.csv"
REPORT_FILE = BASE_DIR / "outputs" / "validation_report.json"


def main():
    if not TICKET_FILE.exists():
        raise FileNotFoundError(
            f"Required analysis file not found: {TICKET_FILE}"
        )

    df = pd.read_csv(TICKET_FILE)

    required_columns = [
        "ticket_id",
        "created_at_ist",
        "first_response_at_ist",
        "roster_match_status",
        "sla_breached",
        "sla_status",
        "status",
        "resolved_at",
    ]

    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df["sla_breached"] = (
        pd.to_numeric(df["sla_breached"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    created = pd.to_datetime(
        df["created_at_ist"], errors="coerce", utc=True
    )
    first_response = pd.to_datetime(
        df["first_response_at_ist"], errors="coerce", utc=True
    )

    resolved_at = pd.to_datetime(
        df["resolved_at"], errors="coerce", utc=True
    )

    duplicate_rows = int(df["ticket_id"].duplicated().sum())
    missing_ticket_ids = int(df["ticket_id"].isna().sum())
    missing_created = int(created.isna().sum())
    missing_first_response = int(first_response.isna().sum())

    response_before_creation = int(
        (first_response < created).fillna(False).sum()
    )

    unmatched_roster = int(
        (df["roster_match_status"] != "matched").sum()
    )

    total_tickets = int(df["ticket_id"].nunique())
    breached_tickets = int(df["sla_breached"].sum())

    resolved_or_closed = (
        df["status"].astype(str).str.lower().isin(["resolved", "closed"])
        & resolved_at.notna()
    )

    resolved_breaches = int(
        (
            (df["sla_breached"] == 1)
            & resolved_or_closed
        ).sum()
    )

    unresolved_breaches = int(
        (
            (df["sla_breached"] == 1)
            & (~resolved_or_closed)
        ).sum()
    )

    checks = {
        "ticket_ids_unique": duplicate_rows == 0,
        "ticket_ids_present": missing_ticket_ids == 0,
        "creation_timestamps_present": missing_created == 0,
        "first_response_timestamps_present": missing_first_response == 0,
        "no_first_response_before_creation": response_before_creation == 0,
        "all_tickets_roster_matched": unmatched_roster == 0,
        "breach_flags_binary": set(df["sla_breached"].unique()).issubset({0, 1}),
        "breach_count_within_ticket_count": (
            0 <= breached_tickets <= total_tickets
        ),
        "resolved_and_unresolved_breaches_reconcile": (
            resolved_breaches + unresolved_breaches == breached_tickets
        ),
    }

    report = {
        "source_file": str(TICKET_FILE.relative_to(BASE_DIR)),
        "validation_summary": {
            "total_rows": int(len(df)),
            "unique_tickets": total_tickets,
            "duplicate_ticket_rows": duplicate_rows,
            "missing_ticket_ids": missing_ticket_ids,
            "missing_creation_timestamps": missing_created,
            "missing_first_response_timestamps": missing_first_response,
            "first_response_before_creation": response_before_creation,
            "unmatched_roster_rows": unmatched_roster,
            "breached_tickets": breached_tickets,
            "resolved_or_closed_breaches": resolved_breaches,
            "unresolved_breaches": unresolved_breaches,
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print(f"\nValidation report saved to: {REPORT_FILE}")

    if not report["all_checks_passed"]:
        raise SystemExit("One or more validation checks failed.")


if __name__ == "__main__":
    main()