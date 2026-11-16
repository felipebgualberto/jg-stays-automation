---
name: owner-statement
description: Generates the monthly owner statement PDF (payout cascade + year view) for a managed property owner. Use when the operator asks for the statement, the payout or "the month's report" for an owner.
---

<!--
English adaptation of the Claude skill used in production (the original is in
Portuguese and names the real owner, units and tax IDs — removed here).
-->

# Monthly owner statement

Produce the 2-page statement that goes to the owner every month, same layout and
same methodology as previous months. Deliver it finished: only stop to ask if a
number cannot be obtained.

## Input
- Reference month (default: previous month).
- Platform payout exports, when available (Airbnb → Earnings → transaction report;
  Booking → Finance → reservations statement; PMS financial report). They take
  priority over any estimate. If missing, ask once; if still missing, estimate and
  flag it.

## Steps

1. **Template.** Load the official generator (`src/owner_statement.py`) and only
   update the data file. Do not redesign layout, colors, logo or copy unless asked.

2. **Bookings of the month.** PriceLabs MCP `get_bookings_report`:
   - `date_filters`: `min_check_in_date` = day 1, `max_check_in_date` = last day
     (pull a few days earlier too, to catch stays crossing the month boundary).
   - `filters.booking_status`: `['booked','cancelled']` — cancellations are excluded
     from the math but checked.
   - Also pull next month's confirmed bookings for the "upcoming bookings" block.

3. **Per-booking cascade — in this order, showing every deduction:**

   | Line | Airbnb | Booking |
   |---|---|---|
   | Guest paid | total charged to the guest | total charged to the guest |
   | (−) platform deductions | guest service fee; host service fee | commission; payment fee |
   | **= Deposited** | payout | payout |
   | (−) PMS fee (% of **guest paid**) | | |
   | (−) Cleaning fee (kept by the manager) | | |
   | **= Commission base** | | |
   | (−) Management commission (per contract) | | |
   | **= Owner payout** | | |

   - Each deduction keeps the name the platform uses. It must close exactly:
     guest paid − deductions = deposited.
   - Without an export there is only an estimated total per booking. Show a single
     "total fee" line, mark the booking as estimated and say so in the criteria —
     never invent the split between fee items.
   - A booking belongs entirely to its **check-in** month.
   - Cleaning fee: the one in force on the booking date.
   - Property expenses: none, unless the operator says otherwise.

4. **Update the data file** (`examples/input/<yyyy-mm>.json` shape): bookings per
   unit, monthly history, projection base months, upcoming bookings.

5. **Generate and verify.**
   - Run the generator. It refuses to build if the statement does not reconcile.
   - Render both pages to images and look at them (page breaks, clipped tables,
     charts).
   - Check: paid − deductions = deposited on every booking; PMS fee = rate × paid;
     sum of payouts = summary total = headline.

6. **Deliver.** Send the PDF and answer in a few lines: total payout, what is an
   estimate and what to check against the payout exports. Save the updated
   generator/data back to the project so next month starts from it.
