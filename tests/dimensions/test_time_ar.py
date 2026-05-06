"""Corpus tests for the Arabic time dimension."""

from __future__ import annotations

import pytest

from puckling import Options, parse
from puckling.corpus import pytest_examples
from puckling.dimensions.time.ar.corpus import CORPUS
from tests.value_helpers import value_matches


def _matches(actual: dict, expected: dict) -> bool:
    return all(k in actual and actual[k] == v for k, v in expected.items())


@pytest.mark.parametrize("phrase, expected", pytest_examples(CORPUS))
def test_corpus(phrase: str, expected: dict, ctx_ar) -> None:
    entities = parse(phrase, ctx_ar, Options(), dims=("time",))
    assert entities, f"no entity for {phrase!r}"
    assert any(value_matches(e.value, expected) for e in entities), (
        f"{phrase!r} resolved to {[e.value for e in entities]}, expected {expected}"
    )


@pytest.mark.parametrize(
    "phrase",
    [
        "غداوي",
        "اليومية",
        "الأحدية",
        "الاسبوعي",
        "abc2015",
        "20150",
        "موعد عادي بدون تاريخ",
        # Hijri-month adjectival/suffixed forms must not match the bare month.
        "رمضانك",
        "الرمضاني",
    ],
)
def test_negative_cases(phrase: str, ctx_ar) -> None:
    assert parse(phrase, ctx_ar, Options(), dims=("time",)) == []


@pytest.mark.parametrize(
    "phrase, expected_body",
    [
        # Bare Hijri months cover the most common spellings.
        ("رمضان", "رمضان"),
        ("محرم", "محرم"),
        ("صفر", "صفر"),
        ("رجب", "رجب"),
        ("شعبان", "شعبان"),
        ("شوال", "شوال"),
        ("ذو الحجه", "ذو الحجه"),
        ("ذو الحجة", "ذو الحجة"),
        ("ذي القعدة", "ذي القعدة"),
        ("ربيع الاول", "ربيع الاول"),
        ("ربيع الأول", "ربيع الأول"),
        ("ربيع الثاني", "ربيع الثاني"),
        ("ربيع الآخر", "ربيع الآخر"),
        ("جمادى الاولى", "جمادى الاولى"),
        ("جمادى الآخرة", "جمادى الآخرة"),
        ("جمادى الثانية", "جمادى الثانية"),
        # Proclitic forms (و ل ب ف ك) attach directly with no separator;
        # the inner Hijri month name should still match.
        ("برمضان", "رمضان"),
        ("ورمضان", "رمضان"),
        ("لرمضان", "رمضان"),
    ],
)
def test_hijri_months_bare_and_proclitic(
    phrase: str, expected_body: str, ctx_ar
) -> None:
    entities = parse(phrase, ctx_ar, Options(), dims=("time",))
    times = [e for e in entities if e.dim == "time"]
    assert times, f"expected a time entity for {phrase!r}; got {entities!r}"
    assert any(e.body == expected_body for e in times), (
        f"expected body {expected_body!r}, got {[e.body for e in times]!r}"
    )


@pytest.mark.parametrize(
    "phrase, expected_body",
    [
        # Head-extension: شهر <hijri-month> collapses to one time entity.
        ("شهر رمضان", "شهر رمضان"),
        ("شهر شعبان", "شهر شعبان"),
        ("شهر محرم", "شهر محرم"),
        # <hijri-month> <year> intersects to a single MONTH-grained time.
        ("رمضان 2025", "رمضان 2025"),
        ("محرم 2025", "محرم 2025"),
        # شهر <hijri-month> <year> — full composition with Tier-1 head rules.
        ("شهر رمضان 2025", "شهر رمضان 2025"),
        # Production-corpus probes — `في رمضان`, `لشهر رمضان` should surface
        # at least the Hijri-month span as a time entity.
        ("في رمضان", "رمضان"),
        ("لشهر رمضان", "شهر رمضان"),
    ],
)
def test_hijri_months_compose_with_existing_rules(
    phrase: str, expected_body: str, ctx_ar
) -> None:
    entities = parse(phrase, ctx_ar, Options(), dims=("time",))
    times = [e for e in entities if e.dim == "time"]
    assert times, f"expected a time entity for {phrase!r}; got {entities!r}"
    assert any(e.body == expected_body for e in times), (
        f"expected body {expected_body!r}, got {[e.body for e in times]!r}"
    )


@pytest.mark.parametrize(
    "phrase, expected_body",
    [
        ("قبل ساعه", "قبل ساعه"),
        ("قبل 5 سنين", "قبل 5 سنين"),
        ("بعد 3 شهور", "بعد 3 شهور"),
        ("اخر شهر", "اخر شهر"),
        ("اخر 6 اشهر", "اخر 6 اشهر"),
        ("خلال اسبوع", "خلال اسبوع"),
        ("منذ ساعتين", "منذ ساعتين"),
    ],
)
def test_temporal_prefix_plus_duration_is_a_time(
    phrase: str, expected_body: str, ctx_ar
) -> None:
    """`<prefix> + <duration>` must surface as a time entity covering the
    full phrase. Pre-fix, puckling emitted only the inner duration token,
    losing parity with duckling on ~3k AR rows.
    """
    entities = parse(phrase, ctx_ar, Options(), dims=("time", "duration"))
    times = [e for e in entities if e.dim == "time"]
    assert times, f"expected a time entity for {phrase!r}; got {entities!r}"
    assert any(e.body == expected_body for e in times), (
        f"expected body {expected_body!r}, got {[e.body for e in times]!r}"
    )


@pytest.mark.parametrize(
    "phrase, expected_body",
    [
        ("ب2025", "2025"),
        ("ل2025", "2025"),
        ("و2025", "2025"),
        ("عملياتي ب2025", "2025"),
    ],
)
def test_proclitic_glued_year(phrase: str, expected_body: str, ctx_ar) -> None:
    """Proclitic letter glued before a 4-digit year must surface the year as
    a time entity.
    """
    entities = parse(phrase, ctx_ar, Options(), dims=("time",))
    times = [e for e in entities if e.dim == "time"]
    assert times, f"expected a time entity for {phrase!r}; got {entities!r}"
    assert any(e.body == expected_body for e in times), (
        f"expected body {expected_body!r}, got {[e.body for e in times]!r}"
    )


@pytest.mark.parametrize(
    "phrase, expected_body",
    [
        # شهر extends through following month name.
        ("شهر يوليو", "شهر يوليو"),
        ("شهر مارس", "شهر مارس"),
        # شهر <month> <year> intersects to a single MONTH-grained time.
        ("شهر يوليو 2025", "شهر يوليو 2025"),
        # <month> <year> alone (without head) also intersects.
        ("يوليو 2025", "يوليو 2025"),
        # شهر + numeric month code (1..12).
        ("شهر 12", "شهر 12"),
        ("شهر 1", "شهر 1"),
        ("شهر 1 2026", "شهر 1 2026"),
        # يوم extends through following weekday.
        ("يوم الجمعه", "يوم الجمعه"),
        ("يوم الاحد", "يوم الاحد"),
    ],
)
def test_month_day_head_extension(
    phrase: str, expected_body: str, ctx_ar
) -> None:
    """`شهر <month-name|year|1-12>` and `يوم <weekday>` must surface as a
    single time entity covering the head + tail. Pre-fix, the head token
    fragmented away as a bare duration (or, after Tier-1 #2 made bare
    durations latent, simply vanished), shedding the `شهر` / `يوم` head.
    """
    entities = parse(phrase, ctx_ar, Options(), dims=("time", "duration"))
    times = [e for e in entities if e.dim == "time"]
    assert times, f"expected a time entity for {phrase!r}; got {entities!r}"
    assert any(e.body == expected_body for e in times), (
        f"expected body {expected_body!r}, got {[e.body for e in times]!r}"
    )


@pytest.mark.parametrize(
    "phrase, expected_body",
    [
        # اليوم + day-period words: each day-period suffix attaches to
        # the preceding day-grained instant as a single time entity.
        ("اليوم الصبح", "اليوم الصبح"),
        ("اليوم الفجر", "اليوم الفجر"),
        ("اليوم الظهر", "اليوم الظهر"),
        ("اليوم العصر", "اليوم العصر"),
        ("اليوم المغرب", "اليوم المغرب"),
        ("اليوم المساء", "اليوم المساء"),
        ("اليوم الليل", "اليوم الليل"),
        # Other day-grained instants compose the same way.
        ("بكره الصبح", "بكره الصبح"),
        ("بكرة الفجر", "بكرة الفجر"),
        ("امس الصبح", "امس الصبح"),
        ("غدا الظهر", "غدا الظهر"),
        # Tanwiin/alif suffix forms also attach.
        ("اليوم صباحا", "اليوم صباحا"),
        ("اليوم ظهرا", "اليوم ظهرا"),
        ("اليوم ليلا", "اليوم ليلا"),
    ],
)
def test_day_instant_plus_day_period(
    phrase: str, expected_body: str, ctx_ar
) -> None:
    """`<day-instant> <day-period>` must surface as a single time entity
    covering the whole phrase, mirroring duckling's unification.
    """
    entities = parse(phrase, ctx_ar, Options(), dims=("time",))
    times = [e for e in entities if e.dim == "time"]
    assert times, f"expected a time entity for {phrase!r}; got {entities!r}"
    assert any(e.body == expected_body for e in times), (
        f"expected body {expected_body!r}, got {[e.body for e in times]!r}"
    )


@pytest.mark.parametrize(
    "phrase",
    [
        # Bare day-period words after a non-time word must NOT fire the
        # composition rule. `صلاة الفجر` ("dawn prayer") is not a time.
        "صلاة الفجر",
        "صلاة الظهر",
        "صلاة المغرب",
        "صلاة العصر",
    ],
)
def test_day_period_does_not_fire_without_day_instant(
    phrase: str, ctx_ar
) -> None:
    entities = parse(phrase, ctx_ar, Options(), dims=("time",))
    times = [e for e in entities if e.dim == "time"]
    assert not any(phrase in e.body for e in times), (
        f"expected no full-phrase time entity for {phrase!r}; got {[e.body for e in times]!r}"
    )
