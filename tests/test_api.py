"""Public API smoke tests."""

from __future__ import annotations

from importlib.metadata import version as _pkg_version

import puckling
from puckling import Context, Locale, Options, parse, supported_dimensions
from puckling.locale import Lang


def test_version_matches_package_metadata():
    """`puckling.__version__` must track the installed distribution version,
    so a stale literal in __init__.py can never drift from pyproject.toml."""
    assert puckling.__version__ == _pkg_version("puckling")


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


def test_supported_dimensions_roundtrips_into_dims_filter(reference_time):
    """`supported_dimensions()` must return DimensionName-typed values so a
    caller can feed the result straight back into `parse(..., dims=...)`
    without `cast`. This is a static-typing contract; pyright is configured
    to fail the run if the call site widens the type."""
    from typing import assert_type

    from puckling.api import DimensionName

    dims = supported_dimensions()
    assert_type(dims, tuple[DimensionName, ...])

    ctx = Context(reference_time=reference_time, locale=Locale(Lang.EN))
    parse("hello", ctx, Options(), dims=dims)
