# Post-sync verification (scheduled task template)

Changes made in the PMS (Stays) reach Airbnb and Booking asynchronously, and sometimes
not at all (expired channel token, a section not resent, Booking ignoring PMS text).
Instead of the operator checking listing pages by hand, the review agent schedules a
**one-shot task** that runs a few hours later in the operator's browser.

Each run starts a fresh session with no memory of the conversation, so the prompt has
to carry everything: what changed, where to look, what "arrived" means, and what to do
in each case.

## Template

```text
Verification agreed with the operator on <date> (see <review doc path>).

Open in the browser the public pages of:
- <Listing 1> on Airbnb: <public URL>/photos
- <Listing 1> on Booking: <public URL>
- ...

For each one, check:
- <Change 1, written as something observable — e.g. "the first photo is the living
  room with the TV off (photo id ...)", "the description says 'compact parking spot'">
- <Change 2 ...>

If it arrived: say so in one line per listing.
If it did not arrive: check the channel status in the PMS (<path>) and tell the
operator exactly what to click ("Update photos" on Airbnb / "Sync photos" on Booking).
If a page still says "updating": reschedule this same task for +4h.

Then update <review doc path> and message the operator in Portuguese, 1–3 lines.
```

## Rules learned in production

- **Write observable checks.** "Photos updated" can't be verified; "first photo id is
  `12345678`" can.
- **Booking is slower than Airbnb.** Say "not yet" instead of "failed" for the first day.
- **One task, many listings.** Batch everything that changed in the same session.
- **Reschedule, don't loop.** If PriceLabs/Booking is still recalculating, the task
  creates its own follow-up at +4h instead of waiting.
- **Close the loop in the doc.** The verification result goes into the same review doc,
  so the next Optimizer run starts from the true state.
