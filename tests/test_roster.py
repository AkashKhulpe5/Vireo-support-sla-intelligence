import pandas as pd

from src.sla_analysis import match_agent_roster


def test_ticket_matches_effective_roster_assignment():
    tickets = pd.DataFrame({
        "ticket_id": ["T1"],
        "agent_id": ["A1"],
        "created_date_ist": [pd.Timestamp("2026-01-15")],
    })

    roster = pd.DataFrame({
        "agent_id": ["A1"],
        "name": ["Agent One"],
        "site": ["Bengaluru"],
        "team": ["Chat Frontline"],
        "shift": ["Morning"],
        "tier": [1],
        "from_date": [pd.Timestamp("2026-01-01")],
        "to_date": [pd.Timestamp("2026-01-31")],
    })

    result = match_agent_roster(tickets, roster)

    assert len(result) == 1
    assert result.loc[0, "name"] == "Agent One"
    assert result.loc[0, "roster_match_status"] == "matched"


def test_ticket_without_effective_roster_assignment_is_unmatched():
    tickets = pd.DataFrame({
        "ticket_id": ["T2"],
        "agent_id": ["A1"],
        "created_date_ist": [pd.Timestamp("2026-02-15")],
    })

    roster = pd.DataFrame({
        "agent_id": ["A1"],
        "name": ["Agent One"],
        "site": ["Bengaluru"],
        "team": ["Chat Frontline"],
        "shift": ["Morning"],
        "tier": [1],
        "from_date": [pd.Timestamp("2026-01-01")],
        "to_date": [pd.Timestamp("2026-01-31")],
    })

    result = match_agent_roster(tickets, roster)

    assert len(result) == 1
    assert result.loc[0, "roster_match_status"] == "unmatched"


def test_ticket_matching_multiple_effective_roster_rows_raises_error():
    tickets = pd.DataFrame({
        "ticket_id": ["T3"],
        "agent_id": ["A1"],
        "created_date_ist": [pd.Timestamp("2026-01-15")],
    })

    roster = pd.DataFrame({
        "agent_id": ["A1", "A1"],
        "name": ["Agent One", "Agent One - Duplicate"],
        "site": ["Bengaluru", "Bengaluru"],
        "team": ["Chat Frontline", "Chat Frontline"],
        "shift": ["Morning", "Morning"],
        "tier": [1, 1],
        "from_date": [
            pd.Timestamp("2026-01-01"),
            pd.Timestamp("2026-01-10"),
        ],
        "to_date": [
            pd.Timestamp("2026-01-31"),
            pd.Timestamp("2026-01-20"),
        ],
    })

    try:
        match_agent_roster(tickets, roster)
    except ValueError as error:
        assert "multiple effective roster rows" in str(error)
    else:
        raise AssertionError("Expected ambiguous roster match to raise ValueError")