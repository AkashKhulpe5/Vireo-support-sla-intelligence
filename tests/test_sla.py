import pandas as pd

from src.sla_analysis import calculate_sla


def make_tickets(channel, response_minutes):
    created_at = pd.Timestamp("2026-01-05 10:00:00", tz="UTC")

    if response_minutes is None:
        first_response_at = pd.NaT
    else:
        first_response_at = created_at + pd.Timedelta(
            minutes=response_minutes
        )

    tickets = pd.DataFrame(
        {
            "ticket_id": ["T1"],
            "channel": [channel],
            "created_at": [created_at],
            "first_response_at": [first_response_at],
            "created_at_ist": [
                created_at.tz_convert("Asia/Kolkata")
            ],
        }
    )

    # Match the production loader's UTC timestamp handling.
    for column in ["created_at", "first_response_at"]:
        tickets[column] = pd.to_datetime(
            tickets[column],
            errors="coerce",
            utc=True,
        )

    return tickets


def test_chat_response_within_sla_is_met():
    result = calculate_sla(make_tickets("chat", 10))

    assert result.loc[0, "sla_target_minutes"] == 15
    assert result.loc[0, "sla_status"] == "met"
    assert not result.loc[0, "sla_breached"]


def test_chat_response_exactly_at_sla_boundary_is_met():
    result = calculate_sla(make_tickets("chat", 15))

    assert result.loc[0, "sla_status"] == "met"
    assert not result.loc[0, "sla_breached"]


def test_chat_response_over_sla_is_breached():
    result = calculate_sla(make_tickets("chat", 16))

    assert result.loc[0, "sla_status"] == "breached"
    assert result.loc[0, "sla_breached"]


def test_channel_whitespace_and_case_are_normalized():
    result = calculate_sla(make_tickets(" CHAT ", 10))

    assert result.loc[0, "channel"] == "chat"
    assert result.loc[0, "sla_target_minutes"] == 15
    assert result.loc[0, "sla_status"] == "met"


def test_unknown_channel_is_not_counted_as_sla_breach():
    result = calculate_sla(make_tickets("messaging", 10))

    assert pd.isna(result.loc[0, "sla_target_minutes"])
    assert result.loc[0, "sla_status"] == "unknown_channel"
    assert not result.loc[0, "sla_breached"]


def test_missing_response_is_not_counted_as_sla_breach():
    result = calculate_sla(make_tickets("chat", None))

    assert pd.isna(result.loc[0, "first_response_minutes"])
    assert not result.loc[0, "sla_breached"]


def test_response_before_creation_is_not_counted_as_sla_breach():
    result = calculate_sla(make_tickets("chat", -5))

    assert result.loc[0, "first_response_minutes"] == -5
    assert not result.loc[0, "sla_breached"]