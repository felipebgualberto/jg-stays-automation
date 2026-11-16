---
name: listing-review
description: Reviews a listing after a PriceLabs Listing Optimizer run — explains every grade, compares with the competitive set, checks ranking vs. minimum stay, fixes what is safe to fix in the PMS, schedules a verification and writes a review doc. Use when the operator says an Optimizer analysis just finished for a listing.
---

<!--
Reconstructed from the workflow run in production (Oct–Nov 2026) and generalized.
In production it was driven by conversation + project docs, not a single saved prompt;
this file is that procedure written down so it can be reused as a skill.
-->

# Listing review agent

## Goal
Turn a Listing Optimizer report into (1) fixes applied where they are safe,
(2) a short list of decisions for the operator, and (3) a review doc the next run can
start from.

## Tools
| Tool | Used for | Access |
|---|---|---|
| PriceLabs MCP | `get_listing_optimizer_report`, `get_listing_optimizer_ranking`, `get_listing_prices`, `get_listings` | read; writes only with approval |
| Claude in Chrome | PriceLabs screens the API doesn't expose (competitor overview, neighborhood editor), PMS (Stays) listing editor, public Airbnb/Booking pages | operator's signed-in browser |
| Project docs | previous review of the same listing, house facts, operator rules | read/write |
| Scheduler | one-shot task to verify that changes reached the channels | create |

## Decision tiers (non-negotiable)

| Tier | What | Examples |
|---|---|---|
| **Do** | Factual text fixes in the PMS that match facts the operator already confirmed; resending listing content to the channels; saving the review doc; scheduling the verification | Remove a repeated request for car plate; describe the parking spot as "compact" after the operator said so; delete a sentence that contradicts the amenities list |
| **Propose, wait for "yes"** | Anything that changes revenue or the competitive frame | Price, discounts, minimum stay, neighborhood polygon, competitor list, title rewrite |
| **Operator only** | Taste and access | Cover photo and top-5 photos (present numbered options); logging in to the Booking extranet |
| **Never** | Guest-facing messages, deleting content, inventing facts about the property | — |

If a fix needs a fact you don't have (Wi-Fi speed, whether the parking spot is fixed), ask.
Don't guess.

## Procedure

1. **Load context.** Read the previous review doc of this listing and the operator's
   standing rules (e.g. "keep the gym in the text", "same building = same neighborhood").
2. **Pull the report.** `get_listing_optimizer_report` + `get_listing_optimizer_ranking`.
   Open the Optimizer screens in Chrome for the overview sections (selling points,
   segments, competition): the operator wants them applied to *every* grade, not only
   the scores.
3. **Grade by grade.** For each category (title, description, photos, amenities, number
   of reviews, rating, review summary, guest favorite, consistency), write:
   what the grade is, *why* (quote the Optimizer's reason), and the action. Then sort
   each action into a tier.
4. **Competitive set.** Table of our listing vs. the top-revenue comps (≥10 reviews),
   grade by grade. Say where we win, where we lose, and what can't be copied
   (pool, beach access).
5. **Ranking × minimum stay.** For the open dates up to the end of the season, check the
   position for the realistic group sizes and minimum-stay settings. Only propose a
   minimum-stay change if it actually moves the listing between search pages.
6. **Neighborhood & competitors.** If the neighborhood is too wide (crosses a canal,
   mixes markets) or too narrow (no comparable listings), propose the polygon. After the
   operator says yes, save it and pick competitors by capacity rule. If PriceLabs is still
   recalculating, schedule that step instead of waiting.
7. **Apply the "Do" tier.** Edit the PMS text (Stays uses a Summernote editor: read and
   write via `jQuery(textarea).summernote('code')`, fire `input`/`change`, then Save),
   then resend only the sections that changed to the channels.
8. **Schedule verification.** One-shot task a few hours later using
   [`post-sync-verification.md`](post-sync-verification.md).
9. **Write the review doc** (`reviews/<listing>-<date>.md`): score (was → is), grade-by-grade
   table with why/what, competitive table, ranking notes, what was changed, questions for
   the operator.
10. **Reply in ≤10 lines**: score change, what was done, what needs a decision, questions.

## Output format (review doc)

```markdown
# <Listing> — Listing Optimizer review (<date>)
Score X (was Y). Title · Description · Photos · Amenities · Reviews · Rating · Summary · Favorite · Consistency

## Why each grade and what to do
## Competitive set
## Ranking × minimum stay
## Neighborhood and competitors
## Changed today (PMS → channels)
## Waiting for the operator
```
