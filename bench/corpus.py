"""Bilingual EN/AR corpus mirroring the NLU service's real workload.

Each sample is tagged with its locale and a coarse length bucket so the
harness can break results down. The texts are a mix of:

- "no-entity" utterances (small talk / commands) — common in chat traffic.
- single-entity utterances (one money / time / phone / url / email / ordinal /
  duration / URL).
- multi-entity / longer utterances — the higher-cost cases.
- a few known-pathological compositional phrases as canaries.

When tags collide, that's fine — the report shows the full text, and we
aggregate by locale/bucket separately.
"""

from __future__ import annotations

from dataclasses import dataclass

from puckling import Lang


@dataclass(frozen=True, slots=True)
class Sample:
    text: str
    lang: Lang
    tag: str


def _bucket(text: str) -> str:
    n = len(text.split())
    if n <= 3:
        return "short"
    if n <= 8:
        return "medium"
    return "long"


_RAW: tuple[tuple[str, Lang, str], ...] = (
    # ── English ────────────────────────────────────────────────────────────
    # No-entity / chat
    ("hello",                                                  Lang.EN, "en/no-entity/short"),
    ("can you help me",                                        Lang.EN, "en/no-entity/short"),
    ("i want to check my account",                             Lang.EN, "en/no-entity/medium"),
    ("please show recent transactions",                        Lang.EN, "en/no-entity/medium"),
    # Single entity — money
    ("transfer 50 dollars",                                    Lang.EN, "en/money/short"),
    ("pay $25.50",                                             Lang.EN, "en/money/short"),
    # Single entity — time / duration
    ("send it tomorrow at 5pm",                                Lang.EN, "en/time/medium"),
    ("schedule for next monday",                               Lang.EN, "en/time/short"),
    ("for 30 minutes",                                         Lang.EN, "en/duration/short"),
    # Single entity — phone / email / url
    ("call me at 555-1212",                                    Lang.EN, "en/phone/short"),
    ("my email is alice@example.com",                          Lang.EN, "en/email/medium"),
    ("visit https://example.com today",                        Lang.EN, "en/url/medium"),
    # Single entity — ordinal
    ("on the 5th",                                             Lang.EN, "en/ordinal/short"),
    # Multi entity / long
    ("transfer 100 KWD to account 1234567 by tomorrow 5pm",    Lang.EN, "en/multi/long"),
    ("pay 25.50 dollars to bob@example.com next monday",       Lang.EN, "en/multi/long"),
    # Saturation canary
    ("the third Monday of October 2014",                       Lang.EN, "en/sat/long"),

    # ── Arabic ─────────────────────────────────────────────────────────────
    # No-entity / chat
    ("مرحبا",                                                   Lang.AR, "ar/no-entity/short"),
    ("اريد ان اتحقق من حسابي",                                  Lang.AR, "ar/no-entity/medium"),
    ("اظهر اخر العمليات",                                       Lang.AR, "ar/no-entity/short"),
    # Single entity — money
    ("حول ٥٠ دينار",                                            Lang.AR, "ar/money/short"),
    ("ادفع ٢٥ دينار",                                           Lang.AR, "ar/money/short"),
    # Single entity — time / duration
    ("الساعة الخامسة مساء",                                     Lang.AR, "ar/time/short"),
    ("غدا الساعة الخامسة",                                      Lang.AR, "ar/time/short"),
    ("لمدة ٣٠ دقيقة",                                           Lang.AR, "ar/duration/short"),
    # Single entity — phone
    ("اتصل بي على ٢٢٢٢٣٣٣٣",                                    Lang.AR, "ar/phone/medium"),
    # Single entity — ordinal
    ("الخامس",                                                  Lang.AR, "ar/ordinal/short"),
    # Multi entity / long
    ("حول ١٠٠ دينار كويتي الى الحساب ١٢٣٤٥٦٧ غدا",              Lang.AR, "ar/multi/long"),
    # Saturation canary
    ("من 4 ابريل الى 10 ابريل",                                 Lang.AR, "ar/sat/long"),
)


CORPUS: tuple[Sample, ...] = tuple(Sample(text=t, lang=lang, tag=tag) for t, lang, tag in _RAW)


def length_bucket(sample: Sample) -> str:
    return _bucket(sample.text)
