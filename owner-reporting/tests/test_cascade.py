import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cascade import Booking, compute, compute_unit, reconcile  # noqa: E402
from layout import load  # noqa: E402

EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "input", "2026-10.json")


def make(paid=1000.0, deductions=(("Serv. hóspede", 140.0), ("Serv. anfitrião", 30.0)), cleaning=200.0):
    return Booking("01/10–03/10", 2, "Airbnb", "AB-0000", paid, list(deductions), cleaning)


def test_cascade_order_and_values():
    c = compute(make(), commission_rate=0.20, pms_rate=0.019)
    assert c.platform_total == 170.00
    assert c.deposited == 830.00          # 1000 − 170
    assert c.pms_fee == 19.00             # 1.9% of what the guest paid, not of the payout
    assert c.base == 611.00               # 830 − 19 − 200
    assert c.commission == 122.20         # 20% of base
    assert c.payout == 488.80             # base − commission
    assert c.company_revenue == 322.20    # cleaning + commission


def test_owned_unit_has_no_commission():
    c = compute(make(), commission_rate=0.0, pms_rate=0.019)
    assert c.commission == 0 and c.payout == c.base


def test_reconcile_flags_wrong_headline():
    unit = compute_unit([make(), make(paid=1500.0)], 0.20, 0.019)
    good = unit.total("payout")
    assert reconcile({"Unit A": unit}, good) == []
    assert reconcile({"Unit A": unit}, good + 1) != []


def test_example_month_reconciles():
    data = load(EXAMPLE)
    units = {u["code"]: u["totals"] for u in data["units"] if u["owner"]}
    headline = round(sum(t.total("payout") for t in units.values()), 2)
    assert reconcile(units, headline) == []
