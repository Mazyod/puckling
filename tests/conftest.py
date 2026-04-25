"""Shared fixtures for puckling tests."""

from __future__ import annotations

import datetime as dt

import pytest

from puckling import Context, Locale
from puckling.locale import Lang

# Duckling's canonical reference time: 2013-02-12T04:30:00 UTC, Tuesday.
REFERENCE_TIME = dt.datetime(2013, 2, 12, 4, 30, 0, tzinfo=dt.UTC)


@pytest.fixture
def reference_time() -> dt.datetime:
    return REFERENCE_TIME


@pytest.fixture
def ctx_en() -> Context:
    return Context(reference_time=REFERENCE_TIME, locale=Locale(Lang.EN))


@pytest.fixture
def ctx_ar() -> Context:
    return Context(reference_time=REFERENCE_TIME, locale=Locale(Lang.AR))
