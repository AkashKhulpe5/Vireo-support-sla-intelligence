from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Vireo Support SLA Intelligence",
    page_icon="📊",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
TICKET_FILE = BASE_DIR / "outputs" / "ticket_sla_analysis.csv"

CREDIT_PER_BREACH_INR = 350


# ---------------------------------------------------------
# Data loading and preparation
# ---------------------------------------------------------
@st.cache_data
def load_data():
    if not TICKET_FILE.exists():
        raise FileNotFoundError(
            f"Could not find {TICKET_FILE}. Run the data preparation "
            "and SLA analysis scripts first."
        )

    df = pd.read_csv(TICKET_FILE)

    required_columns = [
        "ticket_id",
        "created_date_ist",
        "created_week_ist",
        "channel",
        "site",
        "team",
        "tier",
        "shift",
        "agent_id",
        "status",
        "resolved_at",
        "sla_target_minutes",
        "first_response_minutes",
        "sla_breached",
    ]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns in ticket analysis: {missing}"
        )

    df["created_date_ist"] = pd.to_datetime(
        df["created_date_ist"],
        errors="coerce",
    )

    df["sla_breached"] = (
        pd.to_numeric(df["sla_breached"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    df["first_response_minutes"] = pd.to_numeric(
        df["first_response_minutes"],
        errors="coerce",
    )

    df["sla_target_minutes"] = pd.to_numeric(
        df["sla_target_minutes"],
        errors="coerce",
    )

    df["is_resolved_or_closed"] = (
        df["status"].astype(str).str.lower().isin(["resolved", "closed"])
        & df["resolved_at"].notna()
    )

    df["credit_estimate_inr"] = (
        df["sla_breached"]
        * df["is_resolved_or_closed"]
        * CREDIT_PER_BREACH_INR
    )

    df["potential_credit_inr"] = (
        df["sla_breached"]
        * (~df["is_resolved_or_closed"])
        * CREDIT_PER_BREACH_INR
    )

    return df


try:
    data = load_data()
except Exception as exc:
    st.error(f"Unable to load dashboard data: {exc}")
    st.stop()


# ---------------------------------------------------------
# Header and context
# ---------------------------------------------------------
st.title("Vireo Support SLA Intelligence")

st.caption(
    "Operational view of first-response SLA performance, service-credit "
    "exposure, and shift/channel patterns."
)

st.info(
    "This dashboard describes observed ticket outcomes. It does not establish "
    "that a shift, site, or agent caused a breach. Interpret rates with ticket "
    "counts, channel, priority, category, team, and Tier 2 complexity in mind."
)


# ---------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------
st.sidebar.header("Filters")

valid_dates = data["created_date_ist"].dropna()

if valid_dates.empty:
    st.error("No valid IST creation dates are available.")
    st.stop()

min_date = valid_dates.min().date()
max_date = valid_dates.max().date()

selected_dates = st.sidebar.date_input(
    "Ticket creation date (IST)",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates
    end_date = selected_dates

filtered = data[
    data["created_date_ist"].dt.date.between(start_date, end_date)
].copy()


def add_multiselect_filter(frame, column, label):
    values = sorted(
        frame[column].dropna().astype(str).unique().tolist()
    )

    selected = st.sidebar.multiselect(
        label,
        values,
        default=values,
    )

    if selected:
        return frame[frame[column].astype(str).isin(selected)].copy()

    return frame.iloc[0:0].copy()


for column, label in [
    ("site", "Site"),
    ("channel", "Channel"),
    ("team", "Team"),
    ("tier", "Tier"),
    ("shift", "Shift"),
]:
    filtered = add_multiselect_filter(filtered, column, label)

if filtered.empty:
    st.warning("No tickets match the selected filters.")
    st.stop()


# ---------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------
total_tickets = filtered["ticket_id"].nunique()

breached_tickets = filtered.loc[
    filtered["sla_breached"] == 1,
    "ticket_id",
].nunique()

breach_rate = (
    breached_tickets / total_tickets * 100
    if total_tickets
    else 0
)

met_rate = 100 - breach_rate

resolved_breaches = filtered[
    (filtered["sla_breached"] == 1)
    & filtered["is_resolved_or_closed"]
]["ticket_id"].nunique()

unresolved_breaches = filtered[
    (filtered["sla_breached"] == 1)
    & (~filtered["is_resolved_or_closed"])
]["ticket_id"].nunique()

estimated_credit = resolved_breaches * CREDIT_PER_BREACH_INR
potential_credit = unresolved_breaches * CREDIT_PER_BREACH_INR

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("Tickets", f"{total_tickets:,}")
kpi2.metric("SLA breach rate", f"{breach_rate:.2f}%")
kpi3.metric("SLA met rate", f"{met_rate:.2f}%")
kpi4.metric(
    "Estimated resolved-breach credits",
    f"₹{estimated_credit:,.0f}",
)
kpi5.metric(
    "Potential open/pending exposure",
    f"₹{potential_credit:,.0f}",
)

st.caption(
    "Credit estimates apply the stated ₹350 policy amount to breached tickets. "
    "They are not verified against a store-credit transaction ledger."
)


# ---------------------------------------------------------
# Charts
# ---------------------------------------------------------
st.subheader("SLA performance over time")

weekly = (
    filtered.groupby(
        ["created_week_ist", "channel"],
        dropna=False,
    )
    .agg(
        tickets=("ticket_id", "nunique"),
        breaches=("sla_breached", "sum"),
    )
    .reset_index()
)

weekly["breach_rate_pct"] = (
    weekly["breaches"] / weekly["tickets"] * 100
).round(2)

weekly = weekly.sort_values("created_week_ist")

fig_weekly = px.line(
    weekly,
    x="created_week_ist",
    y="breach_rate_pct",
    color="channel",
    markers=True,
    hover_data=["tickets", "breaches"],
    labels={
        "created_week_ist": "Creation week (IST)",
        "breach_rate_pct": "Breach rate (%)",
        "channel": "Channel",
    },
    title="Weekly first-response SLA breach rate by channel",
)

st.plotly_chart(fig_weekly, width="stretch")


left, right = st.columns(2)

with left:
    st.subheader("Breach rate by shift")

    shift_data = (
        filtered.groupby(["shift"], dropna=False)
        .agg(
            tickets=("ticket_id", "nunique"),
            breaches=("sla_breached", "sum"),
        )
        .reset_index()
    )

    shift_data["breach_rate_pct"] = (
        shift_data["breaches"] / shift_data["tickets"] * 100
    ).round(2)

    fig_shift = px.bar(
        shift_data,
        x="shift",
        y="breach_rate_pct",
        text="breach_rate_pct",
        hover_data=["tickets", "breaches"],
        labels={
            "shift": "Shift",
            "breach_rate_pct": "Breach rate (%)",
        },
        title="Observed breach rate by shift",
    )

    st.plotly_chart(fig_shift, width="stretch")


with right:
    st.subheader("Breach rate by channel and site")

    channel_site = (
        filtered.groupby(
            ["channel", "site"],
            dropna=False,
        )
        .agg(
            tickets=("ticket_id", "nunique"),
            breaches=("sla_breached", "sum"),
        )
        .reset_index()
    )

    channel_site["breach_rate_pct"] = (
        channel_site["breaches"] / channel_site["tickets"] * 100
    ).round(2)

    fig_channel_site = px.bar(
        channel_site,
        x="channel",
        y="breach_rate_pct",
        color="site",
        barmode="group",
        hover_data=["tickets", "breaches"],
        labels={
            "channel": "Channel",
            "breach_rate_pct": "Breach rate (%)",
        },
        title="Observed breach rate by channel and site",
    )

    st.plotly_chart(fig_channel_site, width="stretch")


# ---------------------------------------------------------
# Morning vs Day comparison
# ---------------------------------------------------------
st.subheader("Morning vs Day: channel and site comparison")

shift_compare = filtered[
    filtered["shift"].isin(["Morning", "Day"])
].copy()

if shift_compare.empty:
    st.info("No Morning or Day tickets match the current filters.")
else:
    comparison = (
        shift_compare.groupby(
            ["channel", "site", "shift"],
            dropna=False,
        )
        .agg(
            tickets=("ticket_id", "nunique"),
            breaches=("sla_breached", "sum"),
        )
        .reset_index()
    )

    comparison["breach_rate_pct"] = (
        comparison["breaches"] / comparison["tickets"] * 100
    ).round(2)

    st.dataframe(
        comparison.sort_values(["channel", "site", "shift"]),
        width="stretch",
        hide_index=True,
    )


# ---------------------------------------------------------
# Detail table and caveats
# ---------------------------------------------------------
st.subheader("Ticket-level detail")

display_columns = [
    "ticket_id",
    "created_date_ist",
    "channel",
    "site",
    "team",
    "tier",
    "shift",
    "agent_id",
    "status",
    "first_response_minutes",
    "sla_target_minutes",
    "sla_breached",
]

available_display_columns = [
    column
    for column in display_columns
    if column in filtered.columns
]

st.dataframe(
    filtered[available_display_columns].sort_values(
        "created_date_ist",
        ascending=False,
    ),
    width="stretch",
    hide_index=True,
)


with st.expander("Definitions and interpretation notes"):
    st.markdown(
        """
        - **SLA breach:** first response occurred later than the channel's
          policy target.
        - **Breach rate:** breached unique tickets divided by unique tickets
          in the selected view.
        - **Estimated resolved-breach credits:** breached tickets marked
          resolved or closed with a resolution timestamp, multiplied by ₹350.
        - **Potential exposure:** breached tickets not yet resolved/closed,
          multiplied by ₹350.
        - Credit estimates are policy-based and have not been reconciled to
          a financial transaction ledger.
        - Shift/site/team differences are descriptive, not causal.
        - Tier 2 work is more complex; avoid comparing raw ticket volume
          directly with Tier 1.
        - Rates should be interpreted with their ticket counts and the
          selected date/channel/team context.
        """
    )