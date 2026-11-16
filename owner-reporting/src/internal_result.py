"""Internal monthly result — the management company's view of the same month.

Same input file and same cascade as the owner statement, different question:
"how much did the company make?"
- Managed units: company revenue = cleaning fee + management commission.
- Company-owned units: revenue = platform payout − PMS fee (no owner split).

Usage:
    python internal_result.py ../examples/input/2026-10.json [out.pdf]
"""
from __future__ import annotations

import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from cascade import r2, reconcile
from layout import (B, CONTENT_W, DARK, GRAY, GREEN, H1, H2, LIGHT, NOTE, S, UNIT_SUB, UNIT_TITLE, Header,
                    base_table_style, brl, deductions_cell, kfmt, kpi_band, load, occupancy_calendar, out_path,
                    stacked_chart, stay_cell)


def managed_table(unit: dict) -> Table:
    pct = int(unit["commission_rate"] * 100)
    rows = [["Estadia · canal", "Noites", "Valor pago\npelo hóspede", "Descontos da\nplataforma", "Valor\ndepositado",
             "Stays", "Repasse ao\nproprietário", "Taxa de\nlimpeza", f"Comissão\n({pct}%)", "Receita\nda empresa"]]
    for c in unit["totals"].rows:
        rows.append([stay_cell(c), c.booking.nights, brl(c.booking.guest_paid), deductions_cell(c), brl(c.deposited),
                     brl(c.pms_fee), brl(c.payout), brl(c.cleaning), brl(c.commission), brl(c.company_revenue)])
    t = unit["totals"]
    rows.append(["Total", t.nights, brl(t.guest_paid), brl(t.total("platform_total")), brl(t.total("deposited")),
                 brl(t.total("pms_fee")), brl(t.total("payout")), brl(t.total("cleaning")), brl(t.total("commission")),
                 brl(t.total("company_revenue"))])
    tbl = Table(rows, colWidths=[30 * mm, 9 * mm, 18 * mm, 31 * mm] + [16.3 * mm] * 6, repeatRows=1)
    tbl.setStyle(TableStyle(base_table_style() + [("BACKGROUND", (7, 0), (-1, 0), GREEN),
                                                  ("TEXTCOLOR", (6, 1), (6, -1), GRAY),
                                                  ("TEXTCOLOR", (-1, 1), (-1, -1), GREEN)]))
    return tbl


def owned_revenue(unit: dict) -> float:
    return r2(sum(c.deposited - c.pms_fee for c in unit["totals"].rows))


def owned_table(unit: dict) -> Table:
    rows = [["Estadia · canal", "Noites", "Valor pago\npelo hóspede", "Descontos da\nplataforma", "Valor\ndepositado",
             "Stays", "Receita\nda empresa"]]
    for c in unit["totals"].rows:
        rows.append([stay_cell(c), c.booking.nights, brl(c.booking.guest_paid), deductions_cell(c), brl(c.deposited),
                     brl(c.pms_fee), brl(r2(c.deposited - c.pms_fee))])
    t = unit["totals"]
    rows.append(["Total", t.nights, brl(t.guest_paid), brl(t.total("platform_total")), brl(t.total("deposited")),
                 brl(t.total("pms_fee")), brl(owned_revenue(unit))])
    w = (CONTENT_W - 30 - 9 - 31) / 4
    tbl = Table(rows, colWidths=[30 * mm, 9 * mm, w * mm, 31 * mm] + [w * mm] * 3, repeatRows=1)
    tbl.setStyle(TableStyle(base_table_style() + [("BACKGROUND", (-1, 0), (-1, 0), GREEN),
                                                  ("TEXTCOLOR", (-1, 1), (-1, -1), GREEN)]))
    return tbl


def build(path: str, out: str | None = None) -> str:
    data = load(path)
    p = data["period"]
    managed = [u for u in data["units"] if u["owner"]]
    owned = [u for u in data["units"] if not u["owner"]]

    problems = reconcile({u["code"]: u["totals"] for u in managed},
                         r2(sum(u["totals"].total("payout") for u in managed)))
    if problems:
        raise SystemExit("Result does not reconcile:\n- " + "\n- ".join(problems))

    commission = r2(sum(u["totals"].total("commission") for u in managed))
    cleaning = r2(sum(u["totals"].total("cleaning") for u in managed))
    own = r2(sum(owned_revenue(u) for u in owned))
    total = r2(commission + cleaning + own)
    paid = r2(sum(u["totals"].guest_paid for u in data["units"]))

    story = [Header(data["issuer"], "Resultado da Empresa"), Spacer(1, 4),
             Paragraph(f"Relatório interno &nbsp;·&nbsp; Competência: <b>{p['label']}</b> &nbsp;·&nbsp; "
                       f"Emitido em {p['issued']}", S), Spacer(1, 5),
             kpi_band([(f"Receita total em {p['month_name']}", brl(total), "#0E8A5F"),
                       ("Comissão de gestão", brl(commission), "#06225C"), ("Taxas de limpeza", brl(cleaning), "#06225C"),
                       ("Imóvel próprio", brl(own), "#06225C"), ("Valor pago pelos hóspedes", brl(paid), "#06225C")],
                      [50, 33, 33, 32, 38])]
    for u in managed:
        story.append(KeepTogether([Spacer(1, 5), Paragraph(f"{u['code']} — imóvel de terceiro", UNIT_TITLE),
                                   Paragraph(u["description"], UNIT_SUB), managed_table(u)]))
    for u in owned:
        story.append(KeepTogether([Spacer(1, 5), Paragraph(f"{u['code']} — imóvel próprio", UNIT_TITLE),
                                   Paragraph(u["description"], UNIT_SUB), owned_table(u)]))

    rows = [["Imóvel", "Reservas", "Valor pago", "Repasse ao proprietário", "Limpeza", "Comissão", "Receita"]]
    for u in managed:
        t = u["totals"]
        rows.append([u["code"], len(t.rows), brl(t.guest_paid), brl(t.total("payout")), brl(t.total("cleaning")),
                     brl(t.total("commission")), brl(t.total("company_revenue"))])
    for u in owned:
        rows.append([u["code"], len(u["totals"].rows), brl(u["totals"].guest_paid), "—", "—", "—", brl(owned_revenue(u))])
    rows.append(["Total", sum(len(u["totals"].rows) for u in data["units"]), brl(paid),
                 brl(r2(sum(u["totals"].total("payout") for u in managed))), brl(cleaning), brl(commission), brl(total)])
    summ = Table(rows, colWidths=[22 * mm, 18 * mm, 28 * mm, 38 * mm, 25 * mm, 25 * mm, 30 * mm])
    summ.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "Helvetica", 8.5), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7.8),
                              ("BACKGROUND", (0, 0), (-1, 0), DARK), ("TEXTCOLOR", (0, 0), (-1, 0), "white"),
                              ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 9.5),
                              ("BACKGROUND", (0, -1), (-1, -1), LIGHT), ("TEXTCOLOR", (-1, 1), (-1, -1), GREEN),
                              ("LINEABOVE", (0, -1), (-1, -1), 0.8, DARK)]))
    story += [KeepTogether([Paragraph("Resumo do mês", H2), summ]),
              Paragraph("Receita da empresa = limpeza + comissão nos imóveis de terceiros; valor depositado − Stays no "
                        "imóvel próprio. Valores brutos: antes de impostos, custo da equipe de limpeza e condomínio.", NOTE)]

    # ---- page 2 ----
    h = data["history"]
    months = h["months"] + [p["label"][:3]]
    rev_now = {u["code"]: u["totals"].total("company_revenue") for u in managed} | {u["code"]: owned_revenue(u) for u in owned}
    codes = [u["code"] for u in data["units"]]
    cal_w = CONTENT_W / len(codes) - 4
    cals = Table([[occupancy_calendar(u, p, cal_w) for u in data["units"]]], colWidths=[CONTENT_W / len(codes) * mm] * len(codes))
    cals.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    charts = stacked_chart(
        [{c: h["nights"][c] + [next(u for u in data["units"] if u["code"] == c)["totals"].nights] for c in codes},
         {c: h["company_revenue"][c] + [rev_now[c]] for c in codes}],
        months, ["Noites ocupadas por mês", "Receita da empresa por mês (R$)"], [lambda v: f"{int(v)}", kfmt], CONTENT_W,
        capacity=p["days"] * len(codes))
    story += [PageBreak(), Paragraph(f"Evolução {p['year']}", H1), Paragraph(f"Agenda de ocupação — {p['month_name']}", H2),
              cals, Spacer(1, 6), charts]

    out = out or out_path("../examples/output", f"internal_result_{p['year']}-{p['month']:02d}.pdf")
    SimpleDocTemplate(out, pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm, topMargin=10 * mm,
                      bottomMargin=8 * mm, title=f"Resultado — {p['label']}").build(story)
    print(f"{out}\ncompany revenue {brl(total)} · reconciled OK")
    return out


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
