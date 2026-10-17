import pandas as pd
import pytest

from psm.data import load_raw


@pytest.fixture(scope="session")
def raw() -> pd.DataFrame:
    return load_raw().frame.loc[:"2023-12-01"]
