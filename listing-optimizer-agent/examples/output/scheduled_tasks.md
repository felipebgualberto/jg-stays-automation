# Scheduled tasks created by the agent (anonymized)

Between 21 Oct and 16 Nov 2026 the agent created **12 one-shot scheduled tasks** instead
of asking the operator to "remember to check tomorrow". Each one runs in a fresh session,
in the operator's browser, and reports back in 1–3 lines.

| Created | Runs | What it checks / does |
|---|---|---|
| 21 Oct | +2 h | 40 new photos of Unit C reached Airbnb and Booking (cover = living room) |
| 24 Oct | +4 h | New descriptions of Unit C and Unit A reached Airbnb; if yes, re-run the Optimizer on 4 listings |
| 26 Oct | +2 h | Unit A photo order on Airbnb (5 expected photo ids) and Booking main photo |
| 27 Oct | +3 h | Text + photo sets of 4 listings arrived; delete Airbnb-only legacy photos |
| 10 Nov | next morning | Cover + first photos on Airbnb and Booking match the new "highlights" for 4 listings |
| 11 Nov | next morning | Booking covers changed for 3 listings (compares first photo ids against the old ones) |
| 15 Nov | next morning | Reminder: channel homologation pending (operator login needed) |
| 15 Nov | 11:00 | Resume site work: FAQ blocks 3–5, publish Studio on the direct-booking site |
| 15 Nov | +20 days | Google Vacation Rentals status for 4 listings; if still "closed", check the listed requirements |
| 7 Nov | 16 Nov | Optimizer re-run for Unit C before the subscription window closes |
| 7 Nov | 17 Nov | Booking competitor groups unlock (30-day lock) — apply the suggested list |
| 16 Nov | 17 Nov 15:07 | Pick competitors for Unit A and Unit B · 2BR once PriceLabs finishes recalculating; reschedule +4 h if not ready |

## Example (the last one, anonymized)

```text
The operator asked on 16/11 ("do everything") for Unit A and Unit B · 2BR the same as
Unit C. Their new neighborhoods were saved on 16/11 and were recalculating. Now, in Chrome:

1) Unit A — <PriceLabs ranking URL for Unit A> → "Edit competitors" → search by id and
   tick up to 6 one-bedroom listings with capacity ≥4: <6 ids> → "Update data".
2) Unit B · 2BR — same URL with its id → up to 6 two-bedroom listings with capacity ≥6
   (it sleeps 8): <8 candidate ids> (take the first 6 with capacity ≥6; never include our
   own listings) → "Update data".

Drop anyone below the minimum capacity. If the page still says "We're updating",
reschedule for +4h. Then update reviews/unit-a-2026-11-16.md and
reviews/unit-b-2br-2026-11-16.md and message the operator in 1–2 lines.
```
