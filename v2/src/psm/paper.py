"""Compile the Typst paper against the generated outputs: ``python -m psm.paper``."""

from __future__ import annotations

from pathlib import Path

import typst

from psm.config import V2_ROOT

SOURCE = V2_ROOT / "paper" / "main.typ"
TARGET = V2_ROOT / "paper" / "Predictive_Stochastic_Modeling_v2.pdf"


def build(source: Path = SOURCE, target: Path = TARGET) -> Path:
    """Compile `source` with the v2 directory as root so it can read ../output."""
    typst.compile(str(source), output=str(target), root=str(V2_ROOT))
    return target


if __name__ == "__main__":
    print(build())
