import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import thesis  # noqa: E402


@pytest.fixture(scope="session")
def shiller() -> thesis.ShillerData:
    return thesis.load_shiller()


@pytest.fixture(scope="session")
def panel(shiller: thesis.ShillerData) -> pd.DataFrame:
    return shiller.panel
