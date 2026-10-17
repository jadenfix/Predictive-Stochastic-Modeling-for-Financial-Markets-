import pandas as pd
import pytest

from psm.data import audit_archived_leads, load_raw, validate_monthly_index


def test_load_drops_footnote_row_and_is_monthly():
    data = load_raw()
    assert len(data.dropped_rows) == 1
    assert "Mar price" in data.dropped_rows[0]
    idx = data.frame.index
    assert idx[0] == pd.Timestamp("1900-01-01")
    validate_monthly_index(idx)


def test_validate_rejects_gaps_and_disorder():
    with pytest.raises(ValueError):
        validate_monthly_index(pd.DatetimeIndex(["2000-01-01", "2000-03-01"]))
    with pytest.raises(ValueError):
        validate_monthly_index(pd.DatetimeIndex(["2000-02-01", "2000-01-01"]))


def test_archived_lag_columns_are_leads(raw):
    audit = audit_archived_leads(load_raw().frame).set_index("column")
    row = audit.loc["realpricelag"]
    assert row.share_future == 1.0
    assert row.share_past < 0.01
