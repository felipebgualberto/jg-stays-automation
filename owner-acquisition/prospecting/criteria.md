# Lead qualification criteria

How Claude built the owner prospect list. The criteria were set by the operator and refined
over 9 iterations. **The collection code and the lead list are not published.** They hold
personal data of real people, and the scraping only made sense inside the operator's own
browser session.

## Who is a lead

An owner of a **furnished** apartment in **Vitória or Vila Velha (ES)** who either:

| List | Signal | Why they might want a manager |
|---|---|---|
| **Short-term** | Already rents by the night (OLX "direct from owner", Facebook Marketplace private sellers, Airbnb individual hosts) | Already convinced about short-term rental; pain is operations, pricing, reviews |
| **Monthly** | Trying to rent furnished by the month | The simulator can show the short-term alternative against the rent they're asking |

## Priority

| | Rule | Approach |
|---|---|---|
| **A** | Individual owner; rating below 4.7, or the same ad reposted / stale | First. Best odds of closing |
| **B** | Individual owner with an OK operation, or a good unit offered long-term | Lead with the simulator |
| **C** | Experienced host / Superhost | Only after A and B |

## Excluded

- Semi-furnished, or furniture not stated
- Shared rooms or parking spots
- Real-estate agencies and other management companies (kept as a separate list for price and rating benchmarks only)
- Party/event houses, properties for sale
- Owners who did **not** publish a contact channel themselves
- Areas outside the operating region (Guarapari removed by the operator)
- Same owner with several ads = **one row**, with the other ad codes noted

## Compliance rules (non-negotiable)

- **Never pitch through the Airbnb chat.** It breaks Airbnb's rules and puts the
  company's account at risk. Airbnb hosts without a public channel go to an offline
  route instead: the building's front desk or the HOA manager.
- **No cross-referencing** a host's name across other sites to find a personal phone or
  e-mail (LGPD, Brazil's data protection law). Contact goes only through channels the
  owner published.
- OLX chat is allowed: the owner opened it for contact.

## Pipeline status

`To contact → Contacted → Replied → Meeting → Proposal sent → Won / Lost`

## Result

- 276 Airbnb listings screened in the first pass → 11 qualified hosts (all routed offline).
- Final list (v9): **60 owners** in two tabs of 30. Short-term: 8 A · 18 B · 4 C.
  Monthly: 12 A · 9 B · 9 C.
- Delivered as a spreadsheet (status + notes) plus a one-click links page, because the
  operator's phone couldn't open shortened OLX links.
