"""Public API smoke tests."""

from __future__ import annotations

from puckling import Context, Locale, Options, parse, supported_dimensions
from puckling.locale import Lang


def test_parse_returns_empty_for_unknown_text(reference_time):
    ctx = Context(reference_time=reference_time, locale=Locale(Lang.EN))
    assert parse("hello world", ctx, Options()) == []


def test_parse_accepts_dim_filter(reference_time):
    ctx = Context(reference_time=reference_time, locale=Locale(Lang.EN))
    # No dimensions implemented yet; filtered call must not error.
    assert parse("anything", ctx, Options(), dims=("numeral",)) == []


def test_supported_dimensions_lists_all_thirteen():
    dims = supported_dimensions()
    assert "numeral" in dims
    assert "ordinal" in dims
    assert "time" in dims
    assert "duration" in dims
    assert "amount_of_money" in dims
    assert "email" in dims
    assert "url" in dims
    assert "phone_number" in dims
    assert "credit_card" in dims
    assert "distance" in dims
    assert "temperature" in dims
    assert "quantity" in dims
    assert "volume" in dims


def test_locale_string_repr():
    assert str(Locale(Lang.EN)) == "EN"
    assert str(Locale(Lang.AR)) == "AR"
