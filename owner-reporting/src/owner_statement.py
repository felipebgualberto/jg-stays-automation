"""Monthly owner statement (2-page PDF).

Page 1: the month only — one table per unit with the full payout cascade,
        a summary cascade and the calculation criteria.
Page 2: year view — month / year-to-date / 12-month projection, occupancy
        calendars and stacked monthly charts.

Usage:
    python owner_statement.py ../examples/input/2026-10.json owner-01 [out.pdf]
"""
from __future__ import annotations

import sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from cascade import r2, reconcile
from layout import (B, CELL, CONTENT_W, DARK, GRAY, H1, H2, LIGHT, LINE, MAG, NAVY, NOTE, S, UNIT_SUB, UNIT_TITLE,
                    Header, base_table_style, brl, deductions_cell, kfmt, kpi_band, load, occupancy_calendar,
                    out_path, stacked_chart, stay_cell)


def unit_table(unit: dict, pms_rate: float) -> Table:
    pct = int(unit["commission_rate"] * 100)
    hdr = ["Estadia · canal", "Noites", "Valor pago\npelo hóspede", "Descontos da\nplataforma", "Valor\ndepositado",
           f"Stays\n{pms_rate*100:.1f}%".replace(".", ","), "Taxa de\nlimpeza", "Base de\ncomissão",
           f"Comissão\n({pct}%)", "Repasse ao\nproprietário"]
    rows = [hdr]
    for c in unit["totals"].rows:
        rows.append([stay_cell(c), c.booking.nights, brl(c.booking.guest_paid), deductions_cell(c), brl(c.deposited),
                     brl(c.pms_fee), brl(c.cleaning), brl(c.base), brl(c.commission), brl(c.payout)])
    t = unit["totals"]
    rows.append(["Total", t.nights, brl(t.guest_paid), brl(t.total("platform_total")), brl(t.total("deposited")),
                 brl(t.total("pms_fee")), brl(t.total("cleaning")), brl(t.total("base")), brl(t.total("commission")),
                 brl(t.total("payout"))])
    tbl = Table(rows, colWidths=[30 * mm, 9 * mm, 18 * mm, 31 * mm] + [16.3 * mm] * 6, repeatRows=1)
    tbl.setStyle(TableStyle(base_table_style() + [("TEXTCOLOR", (-1, 1), (-1, -1), MAG)]))
    return tbl


def summary_cascade(units: list[dict]) -> Table:
    """Vertical cascade, one column per unit + total — the same order as the per-booking tables."""
    steps = [("Valor pago pelos hóspedes", lambda t: t.guest_paid, ""),
             ("(−) Descontos das plataformas", lambda t: t.total("platform_total"), "−"),
             ("= Valor depositado", lambda t: t.total("deposited"), "="),
             ("(−) Sistema Stays", lambda t: t.total("pms_fee"), "−"),
             ("(−) Taxa de limpeza", lambda t: t.total("cleaning"), "−"),
             ("(−) Comissão de gestão", lambda t: t.total("commission"), "−"),
             ("= Repasse ao proprietário", lambda t: t.total("payout"), "=")]
    rows = [[""] + [u["code"] for u in units] + ["Total"]]
    for label, f, kind in steps:
        vals = [f(u["totals"]) for u in units]
        rows.append([label] + [brl(v) for v in vals] + [brl(r2(sum(vals)))])
    w_label = 70
    w_col = (CONTENT_W - w_label) / (len(units) + 1)
    t = Table(rows, colWidths=[w_label * mm] + [w_col * mm] * (len(units) + 1))
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 8.5), ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("BACKGROUND", (0, 0), (-1, 0), DARK), ("TEXTCOLOR", (0, 0), (-1, 0), "white"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"), ("TEXTCOLOR", (0, 2), (-1, 2), GRAY), ("TEXTCOLOR", (0, 4), (-1, 6), GRAY),
        ("FONT", (0, 3), (-1, 3), "Helvetica-Bold", 8.5), ("LINEABOVE", (0, 3), (-1, 3), 0.5, LINE),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 10), ("BACKGROUND", (0, -1), (-1, -1), LIGHT),
        ("TEXTCOLOR", (1, -1), (-1, -1), MAG), ("LINEABOVE", (0, -1), (-1, -1), 0.8, DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 2.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.4),
    ]))
    return t


def year_kpis(data: dict, units: list[dict], payout_now: float) -> Table:
    h = data["history"]
    codes = [u["code"] for u in units]
    month_vals = {"nights": sum(u["totals"].nights for u in units),
                  "guest_paid": sum(u["totals"].guest_paid for u in units), "payout": payout_now}
    base = h["projection_base_months"]  # months with every unit operating; the current month is always included
    cols = []
    for key, name, fmt in (("nights", "Noites ocupadas", lambda v: f"{v:.0f}"),
                           ("guest_paid", "Valor pago pelos hóspedes", lambda v: brl(v, 0)),
                           ("payout", "Repasse ao proprietário", lambda v: brl(v, 0))):
        hist = sum(sum(h[key][c]) for c in codes)
        ytd = hist + month_vals[key]
        prev = [m for m in base if m in h["months"]]
        base_vals = [sum(h[key][c][h["months"].index(m)] for c in codes) for m in prev] + [month_vals[key]]
        proj = sum(base_vals) / len(base_vals) * 12
        color = "#E91E63" if key == "payout" else "#06225C"
        cell = lambda lab, v, sub, big=False: [
            Paragraph(f"<font size=7 color='#5A6372'>{lab}</font>", B),
            Paragraph(f"<font size={15 if big else 12} color='{color}'><b>{v}</b></font>", B.clone("x", leading=17)),
            Paragraph(f"<font size=6.6 color='#5A6372'>{sub}</font>", B)]
        cols.append([Paragraph(f"<b>{name}</b>", B.clone("k", fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY))]
                    + cell(f"Em {data['period']['month_name']}", fmt(month_vals[key]), " + ".join(codes), True)
                    + cell("Acumulado no ano", fmt(ytd), f"jan–{data['period']['label'][:3]}")
                    + cell("Projeção 12 meses", fmt(proj), f"média {'–'.join(base)} × 12"))
    t = Table(list(map(list, zip(*cols))), colWidths=[CONTENT_W / 3 * mm] * 3)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LINEAFTER", (0, 0), (1, -1), 2, "white"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 1),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("TOPPADDING", (0, 0), (-1, 0), 7),
                           ("BOTTOMPADDING", (0, -1), (-1, -1), 7), ("LINEBELOW", (0, 3), (-1, 3), 0.5, LINE),
                           ("LINEBELOW", (0, 6), (-1, 6), 0.5, LINE)]))
    return t


def build(path: str, owner_id: str, out: str | None = None) -> str:
    data = load(path)
    p, pms = data["period"], data["pms_fee_rate"]
    owner = data["owners"][owner_id]
    units = [u for u in data["units"] if u["code"] in owner["units"]]
    payout = r2(sum(u["totals"].total("payout") for u in units))

    problems = reconcile({u["code"]: u["totals"] for u in units}, payout)
    if problems:
        raise SystemExit("Statement does not reconcile:\n- " + "\n- ".join(problems))

    nights = sum(u["totals"].nights for u in units)
    n_bookings = sum(len(u["totals"].rows) for u in units)
    any_estimated = any(c.booking.estimated for u in units for c in u["totals"].rows)

    story = [Header(data["issuer"], "Prestação de Contas"), Spacer(1, 4),
             Paragraph(f"Proprietário: <b>{owner['name']}</b> &nbsp;·&nbsp; Competência: <b>{p['label']}</b> "
                       f"&nbsp;·&nbsp; Emitido em {p['issued']}", S), Spacer(1, 5),
             kpi_band([(f"Repasse ao proprietário em {p['month_name']}", brl(payout), "#E91E63"),
                       ("Valor pago pelos hóspedes", brl(r2(sum(u['totals'].guest_paid for u in units))), "#06225C"),
                       ("Noites ocupadas", f"{nights} de {p['days'] * len(units)}", "#06225C"),
                       ("Reservas", str(n_bookings), "#06225C")], [62, 48, 46, 30])]
    for u in units:
        occ = u["totals"].nights
        story.append(KeepTogether([Spacer(1, 5), Paragraph(f"{u['code']} — {u['location']}", UNIT_TITLE),
                                   Paragraph(f"{u['description']} &nbsp;·&nbsp; <font color='#5A6372'>Ocupação em "
                                             f"{p['month_name']}: {occ}/{p['days']} noites ({occ/p['days']:.0%})</font>",
                                             UNIT_SUB), unit_table(u, pms)]))
    pms_txt = f"{pms * 100:.1f}".replace(".", ",")
    crit = ("Reservas com check-in no mês, lançadas integralmente nele. Ordem do cálculo: valor pago pelo hóspede → "
            "descontos da plataforma (como aparecem no repasse do Airbnb/Booking) → valor depositado → sistema Stays "
            f"({pms_txt}% do valor pago) → taxa de limpeza → base de comissão → comissão de gestão → repasse. "
            "Despesas do imóvel no período: nenhuma lançada.")
    if any_estimated:
        crit += (" *Taxa estimada: o relatório de repasse da plataforma ainda não estava disponível; o valor será "
                 "conferido no extrato e ajustado no mês seguinte, se houver diferença.")
    story += [KeepTogether([Paragraph("Resumo do mês", H2), summary_cascade(units)]),
              Paragraph(f"Próximas reservas confirmadas", H2), Paragraph(data["next_bookings"], B),
              Paragraph("Critérios", H2), Paragraph(crit, NOTE)]

    # ---- page 2: year view ----
    h = data["history"]
    months = h["months"] + [p["label"][:3]]
    codes = [u["code"] for u in units]
    by = lambda key, f: {c: h[key][c] + [f(next(u for u in units if u["code"] == c))] for c in codes}
    cal_w = CONTENT_W / len(units) - 4
    cals = Table([[occupancy_calendar(u, p, cal_w) for u in units]], colWidths=[CONTENT_W / len(units) * mm] * len(units))
    cals.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    charts = stacked_chart(
        [by("nights", lambda u: u["totals"].nights), by("guest_paid", lambda u: u["totals"].guest_paid),
         by("payout", lambda u: u["totals"].total("payout"))],
        months, ["Noites ocupadas por mês", "Valor pago pelos hóspedes por mês (R$)", "Repasse ao proprietário por mês (R$)"],
        [lambda v: f"{int(v)}", kfmt, kfmt], CONTENT_W, capacity=p["days"] * len(units))
    story += [PageBreak(), Paragraph(f"Evolução {p['year']} — acumulado e projeção", H1), year_kpis(data, units, payout),
              Paragraph(f"Agenda de ocupação — {p['month_name']}", H2), cals,
              Paragraph("Dia colorido = noite ocupada.", NOTE), Spacer(1, 4), charts, Spacer(1, 3),
              Paragraph("Projeção 12 meses = média dos meses com todos os imóveis em operação × 12. Estimativa: não "
                        "considera sazonalidade.", NOTE)]

    out = out or out_path("../examples/output", f"owner_statement_{owner_id}_{p['year']}-{p['month']:02d}.pdf")
    SimpleDocTemplate(out, pagesize=A4, leftMargin=12 * mm, rightMargin=12 * mm, topMargin=10 * mm,
                      bottomMargin=8 * mm, title=f"Prestação de Contas — {p['label']}").build(story)
    print(f"{out}\npayout {brl(payout)} · {n_bookings} bookings · reconciled OK")
    return out


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
