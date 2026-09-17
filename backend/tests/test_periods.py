from datetime import date

from app.shared.periods import Period, parse_period


def test_period_bounds_handle_february_in_a_leap_year() -> None:
    period = Period(2024, 2)
    assert period.start == date(2024, 2, 1)
    assert period.end == date(2024, 2, 29)


def test_shift_crosses_year_boundaries() -> None:
    assert Period(2026, 1).shift(-1) == Period(2025, 12)
    assert Period(2025, 12).shift(2) == Period(2026, 2)


def test_previous_months_excludes_the_current_month() -> None:
    assert Period(2026, 3).previous_months(3) == [
        Period(2025, 12),
        Period(2026, 1),
        Period(2026, 2),
    ]


def test_is_partial_only_for_the_running_month() -> None:
    assert Period(2026, 9).is_partial(date(2026, 9, 17))
    assert not Period(2026, 8).is_partial(date(2026, 9, 17))


def test_parse_period() -> None:
    assert parse_period("2026-09") == Period(2026, 9)
