"""A small regression-table generator that writes Typst and Markdown.

A table is a list of sections; each section holds rows. Coefficient rows put
the estimate (with significance stars) on one line and the standard error in
parentheses on the next. All numbers are formatted here, with one decimal
convention per row, so the Typst and Markdown versions always agree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from psm.regressions import Coef

MINUS = "−"
STAR_NOTE = "* p < 0.10, ** p < 0.05, *** p < 0.01 (two-sided)."


def fmt(x: float | None, digits: int = 3) -> str:
    """Fixed-decimal formatting with a true minus sign; blank for missing values."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return ""
    s = f"{x:,.{digits}f}"
    if s.startswith("-"):
        s = s[1:] if float(s.replace(",", "")) == 0 else MINUS + s[1:]
    return s


def fmt_p(p: float) -> str:
    """p-values to three decimals, with values below 0.001 shown as '<0.001'."""
    if not np.isfinite(p):
        return ""
    return "<0.001" if p < 0.001 else fmt(p, 3)


def fmt_int(n: int) -> str:
    return f"{n:,}"


def stars(p: float) -> str:
    if not np.isfinite(p):
        return ""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


@dataclass
class Row:
    label: str
    cells: list[str]
    kind: str = "stat"  # "coef", "se" or "stat"


@dataclass
class Section:
    title: str | None
    rows: list[Row] = field(default_factory=list)


@dataclass
class Table:
    key: str
    title: str
    columns: list[str]
    sections: list[Section]
    notes: list[str]
    groups: list[tuple[str, int]] | None = None
    stub: str = ""
    stub_width: str = "2fr"
    widths: list[str] | None = None  # data-column widths; default 1fr each
    aligns: list[str] | None = None  # data-column alignment; default center
    size: str = "8.5pt"


def coef_rows(label: str, coefs: list[Coef | None], digits: int = 3, with_stars: bool = True) -> list[Row]:
    """An estimate row with stars and a standard-error row beneath it."""
    est, se = [], []
    for c in coefs:
        if c is None:
            est.append("")
            se.append("")
            continue
        est.append(fmt(c.estimate, digits) + (stars(c.pvalue) if with_stars else ""))
        se.append(f"({fmt(c.se, digits)})" if np.isfinite(c.se) else "")
    return [Row(label, est, "coef"), Row("", se, "se")]


# ----------------------------------------------------------------------------- Typst


def _typst_escape(text: str) -> str:
    out = []
    for ch in text:
        if ch in "\\*_$#@<>`[]~":
            out.append("\\" + ch)
        else:
            out.append(ch)
    return "".join(out)


def _typst_cell(text: str, kind: str) -> str:
    body = text
    star_part = ""
    if kind == "coef":
        stripped = body.rstrip("*")
        n = len(body) - len(stripped)
        body = stripped
        if n:
            star_part = "#super[" + "\\*" * n + "]"
    body = _typst_escape(body)
    return "[" + body + star_part + "]"


def to_typst(table: Table) -> str:
    """A Typst `figure` holding the table and its notes."""
    ncol = len(table.columns)
    lines = [
        "#figure(",
        f"  caption: [{_typst_escape(table.title)}],",
        "  kind: table,",
        "  [",
        f"    #set text(size: {table.size}, hyphenate: false)",
        "    #set par(justify: false, first-line-indent: 0em)",
        "    #table(",
        f"      columns: ({table.stub_width}, " + ", ".join(table.widths or ["1fr"] * ncol) + "),",
        "      align: (left, " + ", ".join(table.aligns or ["center"] * ncol) + "),",
        "      stroke: none,",
        "      inset: (x: 3pt, y: 2.4pt),",
        "      table.hline(stroke: 0.9pt),",
        "      table.header(",
    ]
    if table.groups:
        cells = ["[]"]
        rules = []
        col = 1
        for name, span in table.groups:
            cells.append(f"table.cell(colspan: {span})[{_typst_escape(name)}]")
            rules.append(f"table.hline(start: {col}, end: {col + span}, stroke: 0.4pt)")
            col += span
        lines.append("        " + ", ".join(cells) + ",")
        lines.extend("        " + r + "," for r in rules)
    header = [f"[{_typst_escape(table.stub)}]"] + [f"[{_typst_escape(c)}]" for c in table.columns]
    lines.append("        " + ", ".join(header) + ",")
    lines.append("      ),")
    lines.append("      table.hline(stroke: 0.5pt),")
    for s_i, section in enumerate(table.sections):
        if section.title:
            if s_i > 0:
                lines.append(f"      table.cell(colspan: {ncol + 1}, inset: (y: 1.5pt))[],")
            lines.append(
                f"      table.cell(colspan: {ncol + 1}, align: left)[_{_typst_escape(section.title)}_],"
            )
        elif s_i > 0:
            lines.append("      table.hline(stroke: 0.3pt),")
        for row in section.rows:
            cells = [f"[{_typst_escape(row.label)}]"] + [_typst_cell(c, row.kind) for c in row.cells]
            lines.append("      " + ", ".join(cells) + ",")
    lines.append("      table.hline(stroke: 0.9pt),")
    lines.append("    )")
    if table.notes:
        note = " ".join(_typst_escape(n) for n in table.notes)
        lines.append(f"    #block(width: 100%, above: 0.5em)[#set text(size: 7.5pt); #set par(justify: true); #align(left)[_Notes:_ {note}]]")
    lines.append("  ],")
    lines.append(f") <tab:{table.key}>")
    return "\n".join(lines) + "\n"


# -------------------------------------------------------------------------- Markdown


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("*", "\\*")


def to_markdown(table: Table) -> str:
    """A GitHub-flavoured Markdown rendering (group names are folded into headers)."""
    headers = list(table.columns)
    if table.groups:
        expanded = []
        for name, span in table.groups:
            expanded.extend([name] * span)
        headers = [f"{g} {c}".strip() for g, c in zip(expanded, headers)]
    lines = [f"**{table.title}**", ""]
    lines.append("| " + " | ".join([_md_escape(table.stub)] + [_md_escape(h) for h in headers]) + " |")
    lines.append("|" + "---|" + "---:|" * len(headers))
    for section in table.sections:
        if section.title:
            lines.append(f"| *{_md_escape(section.title)}* |" + " |" * len(headers))
        for row in section.rows:
            lines.append("| " + " | ".join([_md_escape(row.label)] + [_md_escape(c) for c in row.cells]) + " |")
    if table.notes:
        lines.append("")
        lines.append("Notes: " + " ".join(table.notes))
    return "\n".join(lines) + "\n"


def write_table(table: Table, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{table.key}.typ").write_text(to_typst(table))
    (directory / f"{table.key}.md").write_text(to_markdown(table))
