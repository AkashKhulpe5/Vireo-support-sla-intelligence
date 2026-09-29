# Data and Analysis Assumptions

## Data preparation
- Duplicate ticket IDs appearing in both helpdesk and legacy data were deduplicated.
- Where duplicate records differed only in CSAT, the helpdesk record was retained.
- Legacy CSAT values of 0 were treated as missing responses, consistent with the supplied data notes.
- Ticket timestamps were interpreted using the supplied timezone and legacy timestamp rules.
- Agent roster matching used effective dates rather than assuming each agent had only one roster assignment.

## SLA calculation
- SLA performance is based on first response time compared with the channel-specific target.
- A breach occurs when the first response is later than the applicable target.
- Breach attribution follows the supplied policy/data definition.
- The analysis uses the prepared ticket-level SLA output.

## Financial estimate
- The stated policy amount of ₹350 per breached ticket was used to estimate store-credit exposure.
- Breached tickets marked resolved or closed with a resolution timestamp were counted as resolved/closed breaches.
- Breached tickets not meeting that condition were treated as potential exposure.
- Estimates are not confirmed accounting spend because no store-credit transaction ledger was reconciled.

## Comparisons and interpretation
- Breach rates are descriptive and do not establish causation.
- Channel SLA targets differ; overall channel averages should not be interpreted as directly equivalent response-performance measures.
- Comparisons should include ticket counts and relevant channel, site, team, priority, category, and shift context.
- Tier 2 work is more complex; raw ticket volume should not be used to compare Tier 2 directly with Tier 1.
- Small groups may have unstable rates and should be interpreted cautiously.

## Known limitations
- The analysis does not establish whether staffing levels were adequate.
- The analysis does not prove that shift assignment caused observed differences.
- The policy-based credit estimate has not been verified against actual credit transactions.
- Operational recommendations require follow-up review of queue volume, backlog, staffing, and handoff context.