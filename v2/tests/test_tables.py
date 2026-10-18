import thesis as T


def test_number_formatting():
    assert T.fmt(-1.23456, 2) == "−1.23"
    assert T.fmt(-0.0004, 3) == "0.000"
    assert T.fmt(1234.5, 1) == "1,234.5"
    assert T.fmt_p(0.0001) == "<0.001" and T.fmt_p(0.0312) == "0.031"


def test_coefficient_rows_have_stars_and_parenthesized_errors():
    est, se = T.coef_rows("x", [T.Coef(0.5, 0.1, 0.004), T.Coef(0.2, 0.1, 0.07), T.Coef(0.1, 0.1, 0.4)])
    assert est.cells == ["0.500***", "0.200*", "0.100"]
    assert se.cells == ["(0.100)", "(0.100)", "(0.100)"]


def test_renderers_escape_and_agree():
    table = T.Table(
        key="t", title="A [test] table", columns=["h = 1", "h = 3"], groups=[("OLS", 2)],
        sections=[T.Section("Panel", T.coef_rows("Rate_1", [T.Coef(1, 0.1, 0.001), None])),
                  T.Section(None, [T.Row("N", ["10", "9"])])],
        notes=["* p < 0.10."],
    )
    typ = T.to_typst(table)
    assert "#super[\\*\\*\\*]" in typ and "Rate\\_1" in typ and "A \\[test\\] table" in typ and "<tab:t>" in typ
    md = T.to_markdown(table)
    assert "| OLS h = 1 | OLS h = 3 |" in md and "1.000\\*\\*\\*" in md


def test_cli_rejects_unknown_stage():
    import pytest

    with pytest.raises(SystemExit):
        T.main(["nonsense"])
