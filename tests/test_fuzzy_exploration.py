"""Fuzzy exploration tests for parser behavior across dimensions.

Goal: surface rule-edge cases quickly by generating deterministic multi-entity
inputs and asserting invariant properties, plus optional parity checks against a
running Duckling Docker container (`http://localhost:18000/parse`).
"""

from __future__ import annotations

import json
import random
import urllib.error
import urllib.parse
from dataclasses import dataclass
from urllib.request import Request, urlopen

import pytest

from puckling import Options, analyze, parse
from puckling.dimensions.amount_of_money.ar.corpus import CORPUS as AR_MONEY_CORPUS
from puckling.dimensions.amount_of_money.en.corpus import CORPUS as EN_MONEY_CORPUS
from puckling.dimensions.credit_card.corpus import CORPUS as CREDIT_CARD_CORPUS
from puckling.dimensions.distance.ar.corpus import CORPUS as AR_DISTANCE_CORPUS
from puckling.dimensions.distance.en.corpus import CORPUS as EN_DISTANCE_CORPUS
from puckling.dimensions.duration.ar.corpus import CORPUS as AR_DURATION_CORPUS
from puckling.dimensions.duration.en.corpus import CORPUS as EN_DURATION_CORPUS
from puckling.dimensions.email.corpus import CORPUS as EMAIL_CORPUS
from puckling.dimensions.numeral.ar.corpus import CORPUS as AR_NUMERALS
from puckling.dimensions.numeral.en.corpus import CORPUS as EN_NUMERALS
from puckling.dimensions.ordinal.ar.corpus import CORPUS as AR_ORDINALS
from puckling.dimensions.ordinal.en.corpus import CORPUS as EN_ORDINALS
from puckling.dimensions.phone_number.ar.corpus import CORPUS as AR_PHONE_CORPUS
from puckling.dimensions.phone_number.en.corpus import CORPUS as EN_PHONE_CORPUS
from puckling.dimensions.quantity.ar.corpus import CORPUS as AR_QUANTITY_CORPUS
from puckling.dimensions.quantity.en.corpus import CORPUS as EN_QUANTITY_CORPUS
from puckling.dimensions.temperature.ar.corpus import CORPUS as AR_TEMPERATURE_CORPUS
from puckling.dimensions.temperature.en.corpus import CORPUS as EN_TEMPERATURE_CORPUS
from puckling.dimensions.time.ar.corpus import CORPUS as AR_TIME_CORPUS
from puckling.dimensions.time.en.corpus import CORPUS as EN_TIME_CORPUS
from puckling.dimensions.url.corpus import CORPUS as URL_CORPUS
from puckling.dimensions.volume.ar.corpus import CORPUS as AR_VOLUME_CORPUS
from puckling.dimensions.volume.en.corpus import CORPUS as EN_VOLUME_CORPUS


@dataclass(frozen=True, slots=True)
class FuzzyCase:
    """One deterministic corpus seed + generated text for a locale."""

    locale: str
    seed: int
    text: str


def _collect_phrases(corpus, max_examples: int = 4, phrases_per_example: int = 2) -> tuple[str, ...]:
    """Collect a compact phrase pool from a corpus while dropping duplicates."""
    selected: list[str] = []
    for ex in list(corpus)[:max_examples]:
        for phrase in ex.phrases[:phrases_per_example]:
            if phrase not in selected:
                selected.append(phrase)
    return tuple(selected)


def _entity_spans(ent: object) -> tuple[int, int]:
    if hasattr(ent, "range"):
        range_ = ent.range  # type: ignore[attr-defined]
        start = range_.start  # type: ignore[union-attr]
        end = range_.end  # type: ignore[union-attr]
        return int(start), int(end)
    start = ent.start  # type: ignore[attr-defined]
    end = ent.end  # type: ignore[attr-defined]
    return int(start), int(end)


def _assert_spans_consistent(text: str, entities: list[object]) -> None:
    """Every entity must have valid indices and a body that matches `text[start:end]`."""
    for e in entities:
        start, end = _entity_spans(e)
        assert 0 <= start <= end <= len(text), f"bad span {(start, end)!r} for {e!r}"
        body = text[start:end]
        if hasattr(e, "body"):
            assert e.body == body, (  # type: ignore[attr-defined]
                f"body mismatch: body={e.body!r}, slice={body!r}"  # type: ignore[attr-defined]
            )
        else:
            # `analyze()` entities do not carry body directly.
            assert body == text[start:end]


def _assert_no_overlaps(text: str, entities: list[object]) -> None:
    spans = sorted(_entity_spans(e) for e in entities)
    for (a_start, a_end), (b_start, b_end) in zip(spans, spans[1:], strict=False):
        assert a_end <= b_start, f"overlap: {(a_start, a_end)} intersects {(b_start, b_end)}"


def _assert_parse_analyze_linkage(text: str, ctx: object, *, dims: tuple[str, ...]) -> None:
    all_options = Options()
    parsed = parse(text, ctx, all_options, dims=dims)
    analyzed = analyze(text, ctx, all_options, dims=dims)

    _assert_spans_consistent(text, parsed)
    _assert_spans_consistent(text, analyzed)
    _assert_no_overlaps(text, parsed)

    parsed_sig = {(e.dim, e.start, e.end, e.body) for e in parsed}
    analyzed_sig = {(e.dim, *_entity_spans(e), text[_entity_spans(e)[0] : _entity_spans(e)[1]]) for e in analyzed}
    assert parsed_sig <= analyzed_sig
    assert len(parsed) <= len(analyzed)


_EN_POOL = _collect_phrases(EN_MONEY_CORPUS) + _collect_phrases(EN_NUMERALS, phrases_per_example=1) + _collect_phrases(
    EN_ORDINALS
) + _collect_phrases(EN_TIME_CORPUS) + _collect_phrases(EN_DURATION_CORPUS) + _collect_phrases(EN_DISTANCE_CORPUS) + _collect_phrases(
    EN_TEMPERATURE_CORPUS
) + _collect_phrases(EN_QUANTITY_CORPUS) + _collect_phrases(EN_VOLUME_CORPUS) + _collect_phrases(
    EMAIL_CORPUS, phrases_per_example=1
) + _collect_phrases(URL_CORPUS, phrases_per_example=1) + _collect_phrases(EN_PHONE_CORPUS) + _collect_phrases(
    CREDIT_CARD_CORPUS, max_examples=3, phrases_per_example=1
)

# Explicit money-edge probes user called out: adjacent numeric/currency composites.
_EN_POOL = tuple(
    dict.fromkeys(
        (
            *_EN_POOL,
            "KWD 3",
            "3 KWD",
            "KWD 3 4",
            "3 KWD 4",
            "KWD 3 2026/02/02",
        )
    )
)

_AR_POOL = _collect_phrases(AR_MONEY_CORPUS) + _collect_phrases(AR_NUMERALS, phrases_per_example=1) + _collect_phrases(
    AR_ORDINALS
) + _collect_phrases(AR_TIME_CORPUS) + _collect_phrases(AR_DURATION_CORPUS) + _collect_phrases(AR_DISTANCE_CORPUS) + _collect_phrases(
    AR_TEMPERATURE_CORPUS
) + _collect_phrases(AR_QUANTITY_CORPUS) + _collect_phrases(AR_VOLUME_CORPUS) + _collect_phrases(
    EMAIL_CORPUS, phrases_per_example=1
) + _collect_phrases(URL_CORPUS, phrases_per_example=1) + _collect_phrases(AR_PHONE_CORPUS) + _collect_phrases(
    CREDIT_CARD_CORPUS, max_examples=3, phrases_per_example=1
)

# Arabic locale mostly uses Arabic words; keep English-style URL/email to check
# locale-agnostic dimensions.
_AR_POOL = tuple(dict.fromkeys(_AR_POOL))

_SEPARATORS_BY_LOCALE = {
    "en": (" ", ",", ", ", " and ", " then ", "; ", "/"),
    "ar": (" ", "،", " و ", ",", " ثم ", " و", "\n"),
}


def _generate_cases(locale: str, seed: int, *, count: int = 18) -> tuple[FuzzyCase, ...]:
    rng = random.Random(seed)
    pool = _EN_POOL if locale == "en" else _AR_POOL
    seps = _SEPARATORS_BY_LOCALE[locale]
    cases: list[FuzzyCase] = []

    for _ in range(count):
        parts_count = rng.randint(2, 6)
        parts = [rng.choice(pool) for _ in range(parts_count)]
        text = parts[0]
        for part in parts[1:]:
            text += rng.choice(seps) + part
        cases.append(FuzzyCase(locale=locale, seed=seed, text=text))
    return tuple(cases)


FUZZ_TEST_CASES = tuple(
    [case for locale in ("en", "ar") for seed in (1, 11, 111, 2026) for case in _generate_cases(locale, seed)]
)


@pytest.mark.parametrize("case", FUZZ_TEST_CASES)
def test_fuzzy_surface_invariants(case: FuzzyCase, ctx_en, ctx_ar) -> None:
    ctx = ctx_en if case.locale == "en" else ctx_ar
    _assert_parse_analyze_linkage(
        case.text,
        ctx,
        dims=(
            "amount_of_money",
            "credit_card",
            "distance",
            "duration",
            "email",
            "numeral",
            "ordinal",
            "phone_number",
            "quantity",
            "temperature",
            "time",
            "url",
            "volume",
        ),
    )


@pytest.mark.parametrize(
    "locale,text,expected_parse_bodies,expected_analyze_bodies",
    [
        (
            "en",
            "KWD 3 2026/02/02",
            {"KWD 3 2026/02"},
            {"KWD 3", "KWD 3 2026", "KWD 3 2026/02"},
        ),
        ("en", "KWD 3", {"KWD 3"}, {"KWD 3"}),
        ("en", "3 KWD", {"3 KWD"}, {"3 KWD"}),
        (
            "en",
            "KWD 3 4",
            {"KWD 3 4"},
            {"KWD 3", "KWD 3 4"},
        ),
        (
            "en",
            "3 KWD 4",
            {"3 KWD 4"},
            {"3 KWD", "KWD 4", "3 KWD 4"},
        ),
        (
            "ar",
            "3 KWD",
            {"3 KWD"},
            {"3 KWD"},
        ),
    ],
)
def test_currency_order_and_adjacency(
    locale: str,
    text: str,
    expected_parse_bodies: set[str],
    expected_analyze_bodies: set[str],
    ctx_en,
    ctx_ar,
):
    """Target explicit rule-neighbor interactions and positional variants."""
    ctx = ctx_en if locale == "en" else ctx_ar
    analyzed = analyze(text, ctx, Options(), dims=("amount_of_money",))
    entities = parse(text, ctx, Options(), dims=("amount_of_money",))
    parse_bodies = {e.body for e in entities if e.dim == "amount_of_money"}
    analyze_bodies = {text[e.range.start : e.range.end] for e in analyzed if e.dim == "amount_of_money"}
    assert parse_bodies == expected_parse_bodies
    assert expected_analyze_bodies <= analyze_bodies


def test_currency_order_ar_prefix(ctx_ar):
    # AR locale now handles `<ISO> <n>` (e.g. `aed 2,420.00`) the same way as
    # `<n> <ISO>`, matching upstream Duckling. The prefix form arises in
    # production data emitted by bank ledgers.
    out = parse("KWD 3", ctx_ar, Options(), dims=("amount_of_money",))
    assert any(e.body == "KWD 3" for e in out), (
        f"expected money 'KWD 3' for AR; got {[(e.dim, e.body) for e in out]!r}"
    )


DUCKLING_URL = "http://localhost:18000/parse"
DUCKLING_DIMS = ("amount-of-money", "duration", "email", "ordinal", "phone-number", "time", "url")
DUCKLING_DIM_TO_PUCKLING = {
    "amount-of-money": "amount_of_money",
    "duration": "duration",
    "email": "email",
    "ordinal": "ordinal",
    "phone-number": "phone_number",
    "time": "time",
    "url": "url",
}
DUCKLING_DIMS_SET = tuple(DUCKLING_DIM_TO_PUCKLING.values())
LOCALE_MAP = {"en": "en_US", "ar": "ar_SA"}


def _is_duckling_reachable() -> bool:
    try:
        body = urllib.parse.urlencode(
            {
                "text": "a",
                "locale": "en_US",
                "tz": "Asia/Kuwait",
                "dims": "[]",
            }
        ).encode("utf-8")
        with urlopen(Request(DUCKLING_URL, data=body, method="POST"), timeout=1.0):
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return False


def _query_duckling_entities(text: str, locale: str) -> list[dict]:
    body = urllib.parse.urlencode(
        {
            "text": text,
            "locale": LOCALE_MAP[locale],
            "tz": "Asia/Kuwait",
            "dims": json.dumps(list(DUCKLING_DIMS)),
        }
    ).encode("utf-8")
    req = Request(DUCKLING_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urlopen(req, timeout=2.0) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if isinstance(payload, dict):
        entities = payload.get("entities", [])
    elif isinstance(payload, list):
        entities = payload
    else:
        raise AssertionError(f"unexpected duckling payload type: {type(payload)!r} payload={payload!r}")
    assert isinstance(entities, list), f"unexpected duckling payload: {payload!r}"
    return entities


def _duckling_signature(text: str, entity: dict) -> tuple[str, int, int, str]:
    dim = entity.get("dim")
    if not isinstance(dim, str):
        raise AssertionError(f"duckling entity missing dim: {entity!r}")
    puck_dim = DUCKLING_DIM_TO_PUCKLING.get(dim)
    if puck_dim is None:
        raise AssertionError(f"unsupported duckling dim: {dim!r}")
    start = int(entity["start"])
    end = int(entity["end"])
    body = entity.get("body", text[start:end])
    assert body == text[start:end], f"duckling body mismatch: {body!r} vs {text[start:end]!r}"
    return (puck_dim, start, end, body)


@pytest.mark.parametrize("seed", (42, 2026))
def test_fuzzy_duckling_parity_smoke(seed: int, ctx_en, ctx_ar) -> None:
    """Compare parsed span-level signatures against Duckling for deterministic fuzz cases.

    The test is intentionally strict so we can quickly see where parse behavior
    diverges between implementations while still being easy to run locally.
    """
    if not _is_duckling_reachable():
        pytest.skip("Duckling docker not running on localhost:18000")

    for locale, ctx in (("en", ctx_en), ("ar", ctx_ar)):
        cases = _generate_cases(locale, seed, count=8)
        for case in cases:
            puckling_entities = parse(case.text, ctx, Options(), dims=DUCKLING_DIMS_SET)
            puckling_sig = {(e.dim, e.start, e.end, e.body) for e in puckling_entities}

            duckling_entities = _query_duckling_entities(case.text, locale)
            duckling_sig = {
                _duckling_signature(case.text, entity)
                for entity in duckling_entities
                if entity.get("dim") in DUCKLING_DIM_TO_PUCKLING
            }
            if not puckling_sig and not duckling_sig:
                continue
            assert puckling_sig == duckling_sig, (
                f"locale={locale} seed={seed} mismatch for {case.text!r}\n"
                f"puckling={sorted(puckling_sig)}\n"
                f"duckling={sorted(duckling_sig)}"
            )
