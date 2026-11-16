# Case study: running a rental management company on AI workflows

## Problem

JG Stays is a small short-term rental manager in Vitória, Brazil, with 4 live listings, a
target of 10–15, and a 20% fee on revenue. Margins only work if adding one more property
doesn't add one more person. Three kinds of work were growing with every unit:

1. **Owner reporting.** Every month each owner gets an exact payout. The math cascades
   through platform fees, the PMS fee, cleaning and commission, and the data lives in
   three places. One wrong cent costs an owner's trust.
2. **Listing quality.** PriceLabs grades each listing in 9 categories. Fixing them means
   editing in the PMS, waiting for the sync to Airbnb and Booking, and checking that it
   arrived. That last step kept getting skipped, and unsynced fixes were silently lost.
3. **Growth.** Owners ask "how much would my place make?", and nobody had a fast,
   defensible answer or a list of who to ask.

## Solution

One principle across all three: **Claude does the gathering, the math and the busywork.
The operator keeps the decisions that cost money or need taste. Every output has a
built-in check before anyone relies on it.**

| | What was built | The check that makes it trustworthy |
|---|---|---|
| Owner reporting | A Claude skill pulls bookings through the PriceLabs MCP. A Python generator applies the payout cascade and renders a 2-page PDF for the owner and an internal one for the company | `reconcile()` refuses to render if any step doesn't close to the cent. Estimated fees are flagged on the PDF itself |
| Listing Optimizer agent | An agent procedure: read the report and screens, diagnose each grade, apply safe text fixes in the PMS, propose revenue changes, write a review doc | The agent **schedules its own verification** in a fresh session hours later, against observable checks (photo ids, exact sentences) |
| Owner acquisition | A single-file revenue simulator on PriceLabs market data with the same cascade as the statement; written lead criteria and outreach templates | Same math as the real statement. Compliance rules written into the criteria (no Airbnb-chat pitching, LGPD) |

## Result

- **Listing scores (29 Oct → 16 Nov 2026):** Unit A 8.7 → 9.4 · Unit B 2BR 8.9 → 9.2 ·
  Unit B Studio 8.7 → 8.9 · Unit C 8.6 → 9.2. All 4 listings on page 1 of Airbnb search;
  the strongest competitors in each set score 6.4–9.1.
- **12 scheduled tasks** in 4 weeks replaced "remember to check tomorrow".
- **Owner statements** generated monthly since Sep 2026, each reconciled before sending.
  Estimated platform fees are always labeled as estimates.
- **60 qualified owner leads** from 276+ screened listings, in two prioritized lists.
- **Time saved:** `TBD` h/month (operator's estimates, see the root README).

## Lessons

1. **"Done" is when it's verified where the customer sees it.** Saved in the PMS is not
   live on Airbnb. Self-scheduled verification turned out to be the most valuable piece
   of the agent, and the simplest.
2. **Put the check before the artifact.** A PDF that can't be generated with wrong math
   beats a PDF someone has to re-add by hand.
3. **Decision tiers beat blanket confirmations.** If the agent asks about everything,
   the operator stops reading and just clicks yes. Asking only about money and taste
   keeps the yes meaningful.
4. **Be honest about missing data.** PriceLabs doesn't return platform fees. The fix was
   to label the estimate in the PDF, not to hide it, and to make the payout exports the
   source of truth when they exist.
5. **Not everything should be code.** Some steps run best as an AI-assisted workflow:
   UI-only data, platform rules, one-off research. Packaging them as a skill or procedure
   with clear guardrails was enough. Where determinism matters (money), it is code with tests.
6. **Platform rules are product constraints.** "Don't pitch in the Airbnb chat" and LGPD
   shaped the prospecting design as much as any technical choice did.

## What's next

- Package the booking-analytics work (channel mix, lead-time curve → last-minute pricing
  method) as v2.
- Draft-only guest-messaging copilot for WhatsApp, the largest manual workload left.
- Ingest payout exports automatically so platform fees are never estimated.
