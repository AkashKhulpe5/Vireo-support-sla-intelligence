# Vireo Support SLA Review
**To:** Neha  
**From:** Akash Khulpe  
**Subject:** First-response SLA patterns and policy-based credit exposure  
**Analysis period:** January 1 – June 30, 2026

## Executive summary

The analysis covers 11,200 unique support tickets. There were 2,440 first-response SLA breaches, an overall breach rate of 21.79%.

Under the stated policy of ₹350 store credit for each breached ticket upon resolution, 2,320 breached tickets marked resolved or closed with a resolution timestamp imply an estimated ₹8.12 lakh in policy-based credits. Another 120 breached tickets remain open or pending, representing up to ₹42,000 in potential exposure if resolved. These amounts have not been reconciled against a store-credit transaction ledger.

## What the data shows

**1. Breach rates differ substantially by channel and shift.**  
In the Morning-versus-Day comparison, Morning breach rates were higher for chat, email, and social at both Bengaluru and Indore. For example, chat breach rates were 41.47% in Bengaluru Morning and 41.15% in Indore Morning, compared with 9.43% and 9.32% during Day. Voice showed a smaller difference: 6.40% versus 5.44% in Bengaluru, while Indore Day was 4.82% and Morning was 1.32%.

**2. The pattern merits operational investigation, not individual attribution.**  
The observed differences are descriptive. They do not establish that shift assignment caused breaches. Ticket mix, category, priority, staffing, backlog, handoffs, and channel-specific workload may contribute. Tier 2 work also has greater complexity and should not be compared with Tier 1 using raw ticket volume alone.

**3. Data checks passed.**  
The validation process confirmed 11,200 unique ticket IDs, no missing creation or first-response timestamps, no first response preceding ticket creation, complete roster matching, binary breach flags, and reconciliation of resolved/closed versus unresolved breach counts.

## Recommended next actions

1. Review Morning chat, email, and social queue volumes, staffing coverage, backlog at shift start, and handoff practices by site.
2. Examine breach rates within comparable channel, category, and priority groups, always showing ticket counts.
3. Validate the ₹350 credit estimate against actual store-credit transactions before treating it as confirmed financial spend.
4. Monitor weekly breach rates and ticket counts after any operational changes; avoid attributing outcomes to individuals without a fair, context-adjusted review.

## Limitations

This is a descriptive analysis of the provided ticket and roster data. It does not prove causality, establish staffing adequacy, or verify actual credit transactions. Historical roster matching and timestamp interpretation follow the supplied data-preparation rules.