import pandas as pd

from src.prepare_data import prepare_tickets


def test_prepare_tickets_normalizes_legacy_zero_and_removes_duplicate():
    tickets = pd.DataFrame({
        "ticket_id": ["T1", "T1", "T2"],
        "source_system": ["helpdesk", "legacy_fd", "legacy_fd"],
        "csat_score": [None, 0, 5],
        "created_at": [
            "2026-01-01 10:00:00",
            "2026-01-01 10:00:00",
            "2026-01-02 10:00:00",
        ],
        "first_response_at": [
            "2026-01-01 10:05:00",
            "2026-01-01 10:05:00",
            "2026-01-02 10:10:00",
        ],
        "resolved_at": [
            "2026-01-01 12:00:00",
            "2026-01-01 12:00:00",
            "2026-01-02 13:00:00",
        ],
    })

    result = prepare_tickets(tickets)

    # Duplicate ticket records should be reduced to one row per ticket.
    assert len(result) == 2
    assert result["ticket_id"].is_unique

    # The helpdesk record should be preferred for duplicate ticket T1.
    t1 = result[result["ticket_id"] == "T1"].iloc[0]
    assert t1["source_system"] == "helpdesk"

    # The helpdesk record for T1 has a missing CSAT score.
    assert pd.isna(t1["csat_score"])

    # T2 has a valid CSAT score, so it should remain unchanged.
    t2 = result[result["ticket_id"] == "T2"].iloc[0]
    assert t2["csat_score"] == 5

    # All timestamp columns should be timezone-aware UTC datetimes.
    timestamp_columns = [
        "created_at",
        "first_response_at",
        "resolved_at",
    ]

    for column in timestamp_columns:
        assert isinstance(result[column].dtype, pd.DatetimeTZDtype)
        assert str(result[column].dt.tz) == "UTC"