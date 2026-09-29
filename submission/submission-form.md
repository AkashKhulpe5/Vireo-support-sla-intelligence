# Vireo Support SLA Analytics — Submission Form

## Project
**Project name:** Vireo Support SLA Intelligence  
**Candidate:** Akash Khulpe  
**Project type:** AI-assisted support SLA analytics and operational investigation

## Business problem
Analyze first-response SLA performance across support channels, sites, teams, and shifts. Estimate policy-based store-credit exposure and identify patterns that merit operational investigation.

## What I built
- Data cleaning and duplicate-ticket handling
- Date-effective agent roster matching
- Channel-specific first-response SLA calculations
- Ticket-level and weekly SLA analysis
- Streamlit dashboard with filters and visualizations
- Policy-based store-credit exposure estimate
- Automated data validation report
- Business memo and assumptions documentation

## Key findings
- Unique tickets analyzed: 11,200
- SLA breaches: 2,440
- Overall breach rate: 21.79%
- Resolved/closed breached tickets: 2,320
- Estimated policy-based credits for resolved/closed breaches: ₹8,12,000
- Open/pending breached tickets: 120
- Potential additional exposure if resolved: ₹42,000

## Validation
- Automated validation checks: 9
- Checks passed: 9
- Duplicate ticket IDs in prepared analysis: 0
- Missing creation timestamps: 0
- Missing first-response timestamps: 0
- Unmatched roster rows: 0

## Run instructions
Install dependencies using the project's documented `uv` setup, then run:

```cmd
uv run python -m src.prepare_data
uv run python -m src.sla_analysis
uv run python -m src.validation
uv run streamlit run app.py