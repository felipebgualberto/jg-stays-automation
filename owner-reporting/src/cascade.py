"""Payout cascade for short-term rental bookings.

Every booking goes through the same ordered cascade, and every step is kept
so the owner statement can show it line by line:

    guest paid
    − platform deductions (itemized, as named by Airbnb / Booking)
    = deposited (platform payout)
    − PMS fee (% of guest paid)
    − cleaning fee (kept by the management company)
    = commission base
    − management commission (% of base)
    = owner payout

Business rules (decided by the operator, encoded here):
- A booking belongs entirely to the month of its check-in.
- The PMS fee is charged on the full booking value (what the guest paid),
  not on the platform payout.
- Cleaning is passed through to the management company before commission.
- When platform payout exports are missing, fees are estimated and the
  booking is flagged so the statement says so explicitly.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def r2(x: float) -> float:
    return round(x + 0.0, 2)


@dataclass
class Booking:
    stay: str
    nights: int
    channel: str
    ref: str
    guest_paid: float
    platform_deductions: list[tuple[str, float]]
    cleaning_fee: float
    estimated: bool = False


@dataclass
class Cascade:
    booking: Booking
    platform_total: float
    deposited: float
    pms_fee: float
    cleaning: float
    base: float
    commission: float
    payout: float

    @property
    def company_revenue(self) -> float:
        """What the management company keeps: cleaning + commission."""
        return r2(self.cleaning + self.commission)


@dataclass
class UnitTotals:
    rows: list[Cascade] = field(default_factory=list)

    def total(self, attr: str) -> float:
        return r2(sum(getattr(c, attr) for c in self.rows))

    @property
    def nights(self) -> int:
        return sum(c.booking.nights for c in self.rows)

    @property
    def guest_paid(self) -> float:
        return r2(sum(c.booking.guest_paid for c in self.rows))


def compute(b: Booking, commission_rate: float, pms_rate: float) -> Cascade:
    platform_total = r2(sum(v for _, v in b.platform_deductions))
    deposited = r2(b.guest_paid - platform_total)
    pms_fee = r2(b.guest_paid * pms_rate)
    base = r2(deposited - pms_fee - b.cleaning_fee)
    commission = r2(base * commission_rate)
    payout = r2(base - commission)
    return Cascade(b, platform_total, deposited, pms_fee, b.cleaning_fee, base, commission, payout)


def compute_unit(bookings: list[Booking], commission_rate: float, pms_rate: float) -> UnitTotals:
    return UnitTotals([compute(b, commission_rate, pms_rate) for b in bookings])


def reconcile(units: dict[str, UnitTotals], headline_payout: float) -> list[str]:
    """Return a list of problems. Empty list = the statement is consistent.

    Checks that the generator runs before writing any PDF:
    1. guest paid − deductions = deposited, for every booking;
    2. every step of the cascade closes to the cent;
    3. sum of per-booking payouts = unit totals = headline number.
    """
    problems = []
    grand = 0.0
    for code, unit in units.items():
        for c in unit.rows:
            b = c.booking
            if abs(b.guest_paid - c.platform_total - c.deposited) > 0.01:
                problems.append(f"{code} {b.ref}: paid − deductions ≠ deposited")
            if abs(c.deposited - c.pms_fee - c.cleaning - c.base) > 0.01:
                problems.append(f"{code} {b.ref}: deposited − PMS − cleaning ≠ base")
            if abs(c.base - c.commission - c.payout) > 0.01:
                problems.append(f"{code} {b.ref}: base − commission ≠ payout")
        grand += unit.total("payout")
    if abs(r2(grand) - headline_payout) > 0.01:
        problems.append(f"sum of payouts {r2(grand)} ≠ headline {headline_payout}")
    return problems


def booking_from_dict(d: dict) -> Booking:
    return Booking(
        stay=d["stay"],
        nights=d["nights"],
        channel=d["channel"],
        ref=d["ref"],
        guest_paid=d["guest_paid"],
        platform_deductions=[tuple(x) for x in d["platform_deductions"]],
        cleaning_fee=d["cleaning_fee"],
        estimated=d.get("estimated", False),
    )
