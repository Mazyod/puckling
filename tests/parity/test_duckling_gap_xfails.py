"""Strict xfail tests documenting known Duckling parity gaps.

These cases are a small debt ledger, not a generated mirror of Duckling's full
corpus.  Every case points at the upstream rule/corpus family that currently
has no equivalent, partial behavior, or a different resolved value shape in
Puckling.  The xfails are strict: once a case starts passing, pytest reports an
XPASS failure so the row can be promoted into the normal corpus suite.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass
from typing import Any

import pytest

from puckling import Context, DimensionName, Lang, Locale, Options, Region, parse
from puckling.dimensions.time.types import TimeValue
from tests.value_helpers import value_matches

REFERENCE_TIME = dt.datetime(2013, 2, 12, 4, 30, 0, tzinfo=dt.UTC)
OPTIONS = Options(with_latent=True, parse_timeout_ms=None)


@dataclass(frozen=True, slots=True)
class DucklingGapCase:
    text: str
    lang: Lang
    dims: tuple[DimensionName, ...]
    expected_body: str
    expected_value: dict[str, Any] | None
    upstream: str
    region: Region | None = None


def _ctx(lang: Lang, region: Region | None = None) -> Context:
    return Context(reference_time=REFERENCE_TIME, locale=Locale(lang, region))


def _xfail(case: DucklingGapCase) -> Any:
    return pytest.param(
        case,
        id=f"{case.lang.value.lower()}:{case.dims[0]}:{case.text}",
        marks=pytest.mark.xfail(strict=True, reason=f"Upstream parity gap: {case.upstream}"),
    )


def _has_expected_entity(case: DucklingGapCase) -> bool:
    entities = parse(case.text, _ctx(case.lang, case.region), OPTIONS, dims=case.dims)
    for entity in entities:
        if entity.body != case.expected_body:
            continue
        if case.expected_value is None or value_matches(entity.value, case.expected_value):
            return True
    return False


PARSE_GAPS: tuple[DucklingGapCase, ...] = (
    # EN regional date overlays. Puckling currently ignores Region and applies
    # one generic EN date policy.
    DucklingGapCase(
        text="03/04/2013",
        lang=Lang.EN,
        region=Region.GB,
        dims=("time",),
        expected_body="03/04/2013",
        expected_value={"type": "value", "value": "2013-04-03T00:00:00+00:00", "grain": "day"},
        upstream="Duckling/Time/EN/GB/Rules.hs:44 dd/mm/yyyy",
    ),
    DucklingGapCase(
        text="04/03/2013",
        lang=Lang.EN,
        region=Region.AU,
        dims=("time",),
        expected_body="04/03/2013",
        expected_value={"type": "value", "value": "2013-03-04T00:00:00+00:00", "grain": "day"},
        upstream="Duckling/Time/EN/AU/Rules.hs dd/mm/yyyy",
    ),
    # EN timezone parsing. Current Puckling parses the date/time prefix and
    # leaves the timezone suffix outside the match.
    DucklingGapCase(
        text="tomorrow at 5pm PST",
        lang=Lang.EN,
        region=Region.US,
        dims=("time",),
        expected_body="tomorrow at 5pm PST",
        expected_value={"type": "value", "grain": "hour"},
        upstream="Duckling/Time/EN/Rules.hs:2584 ruleTimezone",
    ),
    DucklingGapCase(
        text="May 5 2013 at 12:00 (GMT)",
        lang=Lang.EN,
        region=Region.US,
        dims=("time",),
        expected_body="May 5 2013 at 12:00 (GMT)",
        expected_value={"type": "value", "grain": "minute"},
        upstream="Duckling/Time/EN/Rules.hs:2598 ruleTimezoneBracket",
    ),
    # EN holiday/computed intervals from the large upstream holiday table.
    DucklingGapCase(
        text="Ramadan",
        lang=Lang.EN,
        dims=("time",),
        expected_body="Ramadan",
        expected_value={"type": "interval", "holiday": "Ramadan"},
        upstream="Duckling/Time/EN/Rules.hs:2112 Ramadan interval holiday",
    ),
    DucklingGapCase(
        text="Hanukkah 2013",
        lang=Lang.EN,
        dims=("time",),
        expected_body="Hanukkah 2013",
        expected_value={"holiday": "Hanukkah"},
        upstream="Duckling/Time/EN/Rules.hs holiday table",
    ),
    DucklingGapCase(
        text="Chinese New Year 2014",
        lang=Lang.EN,
        dims=("time",),
        expected_body="Chinese New Year 2014",
        expected_value={"holiday": "Chinese New Year"},
        upstream="Duckling/Time/EN/Rules.hs holiday table",
    ),
    DucklingGapCase(
        text="Earth Hour 2013",
        lang=Lang.EN,
        dims=("time",),
        expected_body="Earth Hour 2013",
        expected_value={"holiday": "Earth Hour"},
        upstream="Duckling/Time/EN/Rules.hs holiday table",
    ),
    # AR time rules: richer clock forms, interval composition, timezone, and
    # Arabic holiday labels/intervals are upstream but not equivalent locally.
    DucklingGapCase(
        text="رمضان",
        lang=Lang.AR,
        dims=("time",),
        expected_body="رمضان",
        expected_value={"type": "interval", "holiday": "رمضان"},
        upstream="Duckling/Time/AR/Rules.hs:1702 Ramadan interval holiday",
    ),
    DucklingGapCase(
        text="عيد الفطر",
        lang=Lang.AR,
        dims=("time",),
        expected_body="عيد الفطر",
        expected_value={"type": "value", "holiday": "عيد الفطر"},
        upstream="Duckling/Time/AR/Rules.hs holiday table uses Arabic labels",
    ),
    DucklingGapCase(
        text="الساعة الثالثة وثلث",
        lang=Lang.AR,
        dims=("time",),
        expected_body="الساعة الثالثة وثلث",
        expected_value={"type": "value", "grain": "minute"},
        upstream="Duckling/Time/AR/Rules.hs:637 third-hour clock rule",
    ),
    DucklingGapCase(
        text="الساعة الثالثة الا ثلث",
        lang=Lang.AR,
        dims=("time",),
        expected_body="الساعة الثالثة الا ثلث",
        expected_value={"type": "value", "grain": "minute"},
        upstream="Duckling/Time/AR/Rules.hs:663 except-third clock rule",
    ),
    DucklingGapCase(
        text="بين الساعة ٣ و الساعة ٥",
        lang=Lang.AR,
        dims=("time",),
        expected_body="بين الساعة ٣ و الساعة ٥",
        expected_value={"type": "interval"},
        upstream="Duckling/Time/AR/Rules.hs:1180 between time-of-day interval",
    ),
    DucklingGapCase(
        text="غدا الساعة ٥ GMT",
        lang=Lang.AR,
        dims=("time",),
        expected_body="غدا الساعة ٥ GMT",
        expected_value={"type": "value", "grain": "hour"},
        upstream="Duckling/Time/AR/Rules.hs:1673 ruleTimezone",
    ),
    # AmountOfMoney interval/open-interval/precision and currency vocabulary.
    DucklingGapCase(
        text="between 10 and 20 dollars",
        lang=Lang.EN,
        dims=("amount_of_money",),
        expected_body="between 10 and 20 dollars",
        expected_value={
            "type": "interval",
            "from": {"value": 10, "unit": "USD"},
            "to": {"value": 20, "unit": "USD"},
        },
        upstream="Duckling/AmountOfMoney/EN/Rules.hs:294 interval rules",
    ),
    DucklingGapCase(
        text="about $10-$20",
        lang=Lang.EN,
        dims=("amount_of_money",),
        expected_body="about $10-$20",
        expected_value={
            "type": "interval",
            "from": {"value": 10, "unit": "USD"},
            "to": {"value": 20, "unit": "USD"},
        },
        upstream="Duckling/AmountOfMoney/EN/Rules.hs:282 precision + dash interval",
    ),
    DucklingGapCase(
        text="less than $20",
        lang=Lang.EN,
        dims=("amount_of_money",),
        expected_body="less than $20",
        expected_value={"type": "interval", "to": {"value": 20, "unit": "USD"}},
        upstream="Duckling/AmountOfMoney/EN/Rules.hs:372 max/open interval",
    ),
    DucklingGapCase(
        text="42 bucks",
        lang=Lang.EN,
        dims=("amount_of_money",),
        expected_body="42 bucks",
        expected_value={"type": "value", "value": 42},
        upstream="Duckling/AmountOfMoney/EN/Rules.hs:160 bucks",
    ),
    DucklingGapCase(
        text="42 Lebanese Pounds",
        lang=Lang.EN,
        dims=("amount_of_money",),
        expected_body="42 Lebanese Pounds",
        expected_value={"type": "value", "value": 42, "unit": "LBP"},
        upstream="Duckling/AmountOfMoney/EN/Corpus.hs:147 LBP examples",
    ),
    DucklingGapCase(
        text="ringgit 42",
        lang=Lang.EN,
        dims=("amount_of_money",),
        expected_body="ringgit 42",
        expected_value={"type": "value", "value": 42, "unit": "MYR"},
        upstream="Duckling/AmountOfMoney/EN/Rules.hs:124 ringgit",
    ),
    DucklingGapCase(
        text="من 10 الى 20 دولار",
        lang=Lang.AR,
        dims=("amount_of_money",),
        expected_body="من 10 الى 20 دولار",
        expected_value={
            "type": "interval",
            "from": {"value": 10, "unit": "USD"},
            "to": {"value": 20, "unit": "USD"},
        },
        upstream="Duckling/AmountOfMoney/AR/Rules.hs:270 interval rules",
    ),
    DucklingGapCase(
        text="اقل من 7 يورو",
        lang=Lang.AR,
        dims=("amount_of_money",),
        expected_body="اقل من 7 يورو",
        expected_value={"type": "interval", "to": {"value": 7, "unit": "EUR"}},
        upstream="Duckling/AmountOfMoney/AR/Rules.hs:342 max/open interval",
    ),
    DucklingGapCase(
        text="اكثر من ثلاثة دولار و42 سينت",
        lang=Lang.AR,
        dims=("amount_of_money",),
        expected_body="اكثر من ثلاثة دولار و42 سينت",
        expected_value={"type": "interval", "from": {"value": 3.42, "unit": "USD"}},
        upstream="Duckling/AmountOfMoney/AR/Rules.hs:370 min/open interval",
    ),
    # EN spoken email and phone canonicalization/extension behavior.
    DucklingGapCase(
        text="alice at exAmple.io",
        lang=Lang.EN,
        dims=("email",),
        expected_body="alice at exAmple.io",
        expected_value={"type": "value", "value": "alice@exAmple.io"},
        upstream="Duckling/Email/EN/Rules.hs:28 spoken at/dot email",
    ),
    DucklingGapCase(
        text="asdf+ab dot c at gmail dot com",
        lang=Lang.EN,
        dims=("email",),
        expected_body="asdf+ab dot c at gmail dot com",
        expected_value={"type": "value", "value": "asdf+ab.c@gmail.com"},
        upstream="Duckling/Email/EN/Corpus.hs:54 spoken email example",
    ),
    DucklingGapCase(
        text="(650)-701-8887 ext 897",
        lang=Lang.EN,
        dims=("phone_number",),
        expected_body="(650)-701-8887 ext 897",
        expected_value={"type": "value", "value": "6507018887 ext 897"},
        upstream="Duckling/PhoneNumber/Rules.hs:35 extension parsing",
    ),
    DucklingGapCase(
        text="4.8.6.6.8.2.7",
        lang=Lang.EN,
        dims=("phone_number",),
        expected_body="4.8.6.6.8.2.7",
        expected_value={"type": "value", "value": "4866827"},
        upstream="Duckling/PhoneNumber/Corpus.hs:58 dotted single-digit example",
    ),
    # Physical quantity interval/open-interval value families.
    DucklingGapCase(
        text="between 3 and 5 miles",
        lang=Lang.EN,
        dims=("distance",),
        expected_body="between 3 and 5 miles",
        expected_value={
            "type": "interval",
            "from": {"value": 3, "unit": "mile"},
            "to": {"value": 5, "unit": "mile"},
        },
        upstream="Duckling/Distance/EN/Rules.hs:71 interval rules",
    ),
    DucklingGapCase(
        text="under 3 miles",
        lang=Lang.EN,
        dims=("distance",),
        expected_body="under 3 miles",
        expected_value={"type": "interval", "to": {"value": 3, "unit": "mile"}},
        upstream="Duckling/Distance/EN/Rules.hs:143 max/open interval",
    ),
    DucklingGapCase(
        text="between 2 and 3 grams",
        lang=Lang.EN,
        dims=("quantity",),
        expected_body="between 2 and 3 grams",
        expected_value={
            "type": "interval",
            "from": {"value": 2, "unit": "gram"},
            "to": {"value": 3, "unit": "gram"},
        },
        upstream="Duckling/Quantity/EN/Rules.hs:116 interval rules",
    ),
    DucklingGapCase(
        text="more than 4 ounces",
        lang=Lang.EN,
        dims=("quantity",),
        expected_body="more than 4 ounces",
        expected_value={"type": "interval", "from": {"value": 4, "unit": "ounce"}},
        upstream="Duckling/Quantity/EN/Rules.hs:216 min/open interval",
    ),
    DucklingGapCase(
        text="between 2 and 3 gallons",
        lang=Lang.EN,
        dims=("volume",),
        expected_body="between 2 and 3 gallons",
        expected_value={
            "type": "interval",
            "from": {"value": 2, "unit": "gallon"},
            "to": {"value": 3, "unit": "gallon"},
        },
        upstream="Duckling/Volume/EN/Rules.hs:87 interval rules",
    ),
    DucklingGapCase(
        text="more than 2 liters",
        lang=Lang.EN,
        dims=("volume",),
        expected_body="more than 2 liters",
        expected_value={"type": "interval", "from": {"value": 2, "unit": "litre"}},
        upstream="Duckling/Volume/EN/Rules.hs:144 min/open interval",
    ),
)


@pytest.mark.parametrize("case", [_xfail(case) for case in PARSE_GAPS])
def test_documented_duckling_parse_gap(case: DucklingGapCase) -> None:
    assert _has_expected_entity(case)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Upstream has standalone TimeGrain rules in Duckling/TimeGrain/{EN,AR}/Rules.hs; "
        "Puckling currently models grains as time helpers only."
    ),
)
def test_time_grain_dimension_is_exposed_like_upstream() -> None:
    from puckling import supported_dimensions

    assert "time_grain" in supported_dimensions()


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Duckling/Ordinal/Types.hs:34 resolves ordinals with type=value; "
        "Puckling's legacy dump reports type=ordinal."
    ),
)
def test_ordinal_resolved_value_shape_matches_upstream() -> None:
    entities = parse("first", _ctx(Lang.EN), OPTIONS, dims=("ordinal",))

    assert any(value_matches(entity.value, {"type": "value", "value": 1}) for entity in entities)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Duckling/Ordinal/EN/Rules.hs:94 accepts any ordinal suffix after digits; "
        "Puckling validates suffix agreement and rejects 1nd."
    ),
)
def test_english_ordinal_suffix_leniency_matches_upstream() -> None:
    entities = parse("1nd", _ctx(Lang.EN), OPTIONS, dims=("ordinal",))

    assert any(value_matches(entity.value, {"type": "value", "value": 1}) for entity in entities)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Duckling/Numeral/Types.hs:41 resolves numerals to value only; "
        "Puckling surfaces composition fields like grain and multipliable."
    ),
)
def test_numeral_resolved_value_shape_hides_internal_fields_like_upstream() -> None:
    entities = parse("hundred", _ctx(Lang.EN), OPTIONS, dims=("numeral",))
    assert entities

    value = entities[0].value
    assert asdict(value) == {"value": 100}


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Duckling/Time/EN/Rules.hs uses TimeZoneData on timezone parses; "
        "Puckling TimeValue has no timezone-preserving resolved field yet."
    ),
)
def test_time_timezone_metadata_is_preserved_like_upstream() -> None:
    entities = parse("tomorrow at 5pm PST", _ctx(Lang.EN, Region.US), OPTIONS, dims=("time",))
    assert entities

    time_value = entities[0].value
    assert isinstance(time_value, TimeValue)
    timezone_attr = "timezone"
    assert getattr(time_value, timezone_attr) == "PST"
