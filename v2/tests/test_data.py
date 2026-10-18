"""The Shiller workbook is pinned, parsed correctly and consistent with the archived extract."""

import numpy as np
import pandas as pd
import pytest

import thesis as T


@pytest.mark.parametrize(
    "value, expected",
    [(1871.01, "1871-01"), (1871.1, "1871-10"), (1871.10, "1871-10"), (1871.12, "1871-12"), (2026.09, "2026-09")],
)
def test_fractional_dates(value, expected):
    assert T.parse_shiller_date(value) == pd.Timestamp(expected + "-01")


def test_bad_fractional_date_is_rejected():
    with pytest.raises(ValueError):
        T.parse_shiller_date(1871.13)


def test_workbook_is_the_pinned_vintage():
    assert T.sha256(T.SHILLER_FILE) == T.SHILLER_SHA256
    assert T.SHILLER_FILE.stat().st_size < 10_000_000


def test_parsed_panel(shiller):
    frame = shiller.frame
    assert frame.index[0] == pd.Timestamp("1871-01-01")
    T.validate_monthly_index(frame.index)
    assert any("CPI estimated" in note for note in shiller.footnotes)
    # The sample ends at the last month in which every core series is reported ...
    assert frame.loc[shiller.end, list(T.CORE_SERIES)].notna().all()
    assert frame.loc[shiller.end + pd.DateOffset(months=1):, ["dividend", "earnings"]].isna().all().all()
    # ... and the core series have no gaps before it.
    assert shiller.panel[list(T.CORE_SERIES)].notna().all().all()
    assert np.all(shiller.panel["price"] > 0)


def test_validate_rejects_gaps_and_disorder():
    with pytest.raises(ValueError):
        T.validate_monthly_index(pd.DatetimeIndex(["2000-01-01", "2000-03-01"]))
    with pytest.raises(ValueError):
        T.validate_monthly_index(pd.DatetimeIndex(["2000-02-01", "2000-01-01"]))


def test_archived_extract_matches_except_its_last_months(shiller):
    one45 = T.load_one45()
    assert one45.index[0] == pd.Timestamp("1900-01-01")
    summary, details = T.compare_with_one45(shiller.frame, one45)
    assert (summary.months > 1400).all()
    assert len(details) == summary.n_differ.sum()
    assert (details.month >= pd.Timestamp("2023-10-01")).all()


def test_archived_lag_columns_are_leads():
    audit = T.audit_archived_leads(T.load_one45()).set_index("column")
    row = audit.loc["realpricelag"]
    assert row.match_future == row.pairs_future
    assert row.match_past / row.pairs_past < 0.01
