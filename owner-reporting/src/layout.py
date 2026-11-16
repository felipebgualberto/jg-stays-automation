"""Shared PDF building blocks (ReportLab + matplotlib).

The PDF itself is in Brazilian Portuguese: it is the document owners receive.
"""
from __future__ import annotations

import calendar
import datetime as dt
import io
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Flowable, Image, Paragraph, Table, TableStyle

from cascade import booking_from_dict, compute_unit

NAVY = colors.HexColor("#003DA5")
DARK = colors.HexColor("#06225C")
MAG = colors.HexColor("#E91E63")
GREEN = colors.HexColor("#0E8A5F")
LIGHT = colors.HexColor("#EEF2FA")
GRAY = colors.HexColor("#5A6372")
LINE = colors.HexColor("#DCE3F1")
UNIT_COLORS = {"Unit A": "#1F5FD1", "Unit B": "#E91E63", "Unit C": "#E39B12"}
CONTENT_W = 186  # mm of usable A4 width

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.edgecolor": "#E3E8F2",
    "xtick.color": "#5A6372", "ytick.color": "#5A6372", "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True,
    "axes.grid.axis": "y", "grid.color": "#E3E8F2", "grid.linewidth": 0.6, "axes.axisbelow": True,
})

S = ParagraphStyle("s", fontName="Helvetica", fontSize=9, textColor=GRAY, leading=12)
B = ParagraphStyle("b", fontName="Helvetica", fontSize=8, textColor=DARK, leading=10.5)
NOTE = ParagraphStyle("n", fontName="Helvetica", fontSize=7, textColor=GRAY, leading=9)
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, textColor=DARK, leading=17, spaceAfter=4)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY, leading=14, spaceBefore=6, spaceAfter=4)
UNIT_TITLE = ParagraphStyle("ut", fontName="Helvetica-Bold", fontSize=11, textColor=MAG, leading=14, alignment=1)
UNIT_SUB = ParagraphStyle("us", fontName="Helvetica-Bold", fontSize=9.5, textColor=NAVY, leading=12, alignment=1, spaceAfter=3)
CELL = ParagraphStyle("c", fontName="Helvetica", fontSize=7, textColor=DARK, leading=8.4)
CELL_R = ParagraphStyle("cr", parent=CELL, alignment=2)


# ---------- data loading ----------
def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rate = data["pms_fee_rate"]
    for u in data["units"]:
        u["totals"] = compute_unit([booking_from_dict(b) for b in u["bookings"]], u["commission_rate"], rate)
    return data


def brl(v: float, dec: int = 2) -> str:
    s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def kfmt(v: float) -> str:
    return f"{v/1000:.1f}k".replace(".", ",")


# ---------- header ----------
class Header(Flowable):
    def __init__(self, issuer: dict, title: str):
        super().__init__()
        self.issuer, self.title = issuer, title
        self.width, self.height = CONTENT_W * mm, 18 * mm

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        y = 8 * mm
        t = c.beginText(0, y)
        t.setFont("Helvetica-Bold", 24)
        t.setFillColor(NAVY)
        t.textOut(self.issuer["brand_a"])
        t.setFillColor(DARK)
        t.textOut(self.issuer["brand_b"])
        c.drawText(t)
        c.setFillColor(DARK)
        c.setFont("Helvetica-Bold", 14)
        c.drawRightString(self.width, y + 6, self.title)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 8.5)
        c.drawRightString(self.width, y - 5, f"{self.issuer['legal_name']} · {self.issuer['tax_id']}")
        c.setStrokeColor(LINE)
        c.setLineWidth(0.8)
        c.line(0, 0, self.width, 0)


# ---------- tables ----------
def base_table_style(header_bg=NAVY, pad=1.2):
    return [
        ("FONT", (0, 0), (-1, -1), "Helvetica", 7),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 6.4),
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, LIGHT]),
        ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 7),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, DARK),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]


def stay_cell(cascade) -> Paragraph:
    b = cascade.booking
    est = " · <font color='#B4520F'>taxa estimada*</font>" if b.estimated else ""
    return Paragraph(f"{b.stay}<br/><font size=6 color='#5A6372'>{b.channel} · {b.ref}{est}</font>", CELL)


def deductions_cell(cascade):
    items = cascade.booking.platform_deductions
    if len(items) == 1:
        return Paragraph(f"<font size=5.6 color='#5A6372'>{items[0][0]}</font>&nbsp;{brl(items[0][1]).replace(' ', '&nbsp;')}", CELL_R)
    return Paragraph("<br/>".join(f"<font size=5.6 color='#5A6372'>{n}</font>&nbsp;{brl(v).replace(' ', '&nbsp;')}"
                                  for n, v in items), CELL_R)


def kpi_band(cells: list[tuple[str, str, str]], widths_mm: list[float]) -> Table:
    """cells = [(label, value, color_hex)], first one rendered bigger."""
    labels = [Paragraph(f"<font size=7.5 color='#5A6372'>{l}</font>", B) for l, _, _ in cells]
    values = []
    for i, (_, v, col) in enumerate(cells):
        size = 17 if i == 0 else 12.5
        values.append(Paragraph(f"<font size={size} color='{col}'><b>{v}</b></font>", ParagraphStyle("v", leading=size + 5)))
    t = Table([labels, values], colWidths=[w * mm for w in widths_mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT), ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 6), ("BOTTOMPADDING", (0, -1), (-1, -1), 5),
        ("LINEAFTER", (0, 0), (-2, -1), 2, colors.white),
    ]))
    return t


# ---------- occupancy calendar ----------
def occupancy_calendar(unit: dict, period: dict, width_mm: float) -> list:
    year, month = period["year"], period["month"]
    busy = set()
    for b in unit["bookings"]:
        d = dt.date.fromisoformat(b["check_in"])
        end = dt.date.fromisoformat(b["check_out"])
        while d < end:
            if d.month == month:
                busy.add(d.day)
            d += dt.timedelta(1)
    weeks = calendar.Calendar(firstweekday=6).monthdayscalendar(year, month)
    rows = [["D", "S", "T", "Q", "Q", "S", "S"]] + [[str(x) if x else "" for x in w] for w in weeks]
    cw = width_mm / 7
    t = Table(rows, colWidths=[cw * mm] * 7, rowHeights=[4.4 * mm] + [5.4 * mm] * len(weeks))
    color = colors.HexColor(UNIT_COLORS.get(unit["code"], "#1F5FD1"))
    st = [("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 6.5), ("TEXTCOLOR", (0, 0), (-1, -1), GRAY),
          ("FONT", (0, 1), (-1, -1), "Helvetica", 7.5), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LINEBELOW", (0, 0), (-1, 0), 0.6, LINE)]
    for r, w in enumerate(weeks, 1):
        for c, x in enumerate(w):
            if not x:
                continue
            if x in busy:
                st += [("BACKGROUND", (c, r), (c, r), color), ("TEXTCOLOR", (c, r), (c, r), colors.white),
                       ("FONT", (c, r), (c, r), "Helvetica-Bold", 7.5)]
            else:
                st += [("BACKGROUND", (c, r), (c, r), LIGHT)]
    st += [("GRID", (0, 1), (-1, -1), 1.4, colors.white)]
    t.setStyle(TableStyle(st))
    days = period["days"]
    title = Paragraph(f"<b>{unit['code']}</b> <font color='#5A6372'>· {len(busy)}/{days} noites ({len(busy)/days:.0%})</font>",
                      ParagraphStyle("ct", fontName="Helvetica", fontSize=8.5, textColor=DARK, leading=11, spaceAfter=3))
    return [title, t]


# ---------- charts ----------
def stacked_chart(series: dict[str, list[float]], months: list[str], titles: list[str], fmts, width_mm: float,
                  capacity: float | None = None) -> Image:
    """series: list of dicts, one per subplot, unit -> values."""
    n = len(series)
    fig, axs = plt.subplots(n, 1, figsize=(7.3, 1.65 * n), gridspec_kw={"hspace": 0.65})
    axs = [axs] if n == 1 else axs
    for ax, s, title, fmt in zip(axs, series, titles, fmts):
        bottom = [0.0] * len(months)
        for unit, vals in s.items():
            ax.bar(range(len(months)), vals, 0.62, bottom=bottom, color=UNIT_COLORS[unit], label=unit,
                   edgecolor="white", linewidth=0.8)
            bottom = [a + b for a, b in zip(bottom, vals)]
        for xi, tot in enumerate(bottom):
            if tot:
                ax.text(xi, tot, fmt(tot), ha="center", va="bottom", fontsize=6.3, color="#06225C",
                        fontweight="bold" if xi == len(months) - 1 else "normal")
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months)
        ax.tick_params(length=0)
        ax.margins(y=0.16)
        ax.axvspan(len(months) - 1.45, len(months) - 0.55, color="#F4F6FB", zorder=0)
        ax.set_title(title, loc="left", fontsize=8.5, color="#06225C", fontweight="bold")
    if capacity:
        axs[0].axhline(capacity, color="#5A6372", lw=0.8, ls=(0, (3, 3)))
    axs[0].legend(loc="upper right", bbox_to_anchor=(1, 1.42), ncol=len(series[0]), frameon=False, fontsize=7,
                  handlelength=1, handleheight=1)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    from PIL import Image as PILImage
    w, h = PILImage.open(buf).size
    buf.seek(0)
    return Image(buf, width=width_mm * mm, height=width_mm * mm * h / w)


def out_path(default_dir: str, name: str) -> str:
    os.makedirs(default_dir, exist_ok=True)
    return os.path.join(default_dir, name)
