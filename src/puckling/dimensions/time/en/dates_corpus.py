"""Corpus for the supplemental English Time date rules.

Reference time: 2013-02-12T04:30:00Z (Tuesday). Examples are picked to cover
the patterns in ``dates_rules.py`` without overlapping with what the
foundation corpus already exercises.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ---- ISO-8601 timestamps with 'T' ----
    examples(
        {"value": "2013-02-15T17:30:00+00:00", "grain": "second"},
        ["2013-02-15T17:30:00", "2013-02-15t17:30:00"],
    ),
    examples(
        {"value": "2013-02-15T17:30:00+00:00", "grain": "second"},
        ["2013-02-15T17:30:00Z", "2013-02-15T17:30:00.000Z"],
    ),
    examples(
        {"value": "2013-02-15T17:30:45+00:00", "grain": "second"},
        ["2013-02-15T17:30:45"],
    ),
    examples(
        {"value": "2014-12-31T23:59:59+00:00", "grain": "second"},
        ["2014-12-31T23:59:59"],
    ),
    examples(
        {"value": "2013-02-15T17:30:00+00:00", "grain": "second"},
        ["2013-02-15 17:30:00"],
    ),
    # ---- Slash and dot dates with year ----
    examples(
        {"value": "2014-03-15T00:00:00+00:00", "grain": "day"},
        ["3/15/2014", "3-15-2014", "3.15.2014"],
    ),
    examples(
        {"value": "2014-03-15T00:00:00+00:00", "grain": "day"},
        ["2014-03-15", "2014-3-15"],
    ),
    examples(
        {"value": "2013-07-04T00:00:00+00:00", "grain": "day"},
        ["7/4/2013", "07/04/2013", "7-4-13"],
    ),
    # ---- Slash dates without year (latent year defaults to reference year) ----
    examples(
        {"value": "2013-03-15T00:00:00+00:00", "grain": "day"},
        ["3/15", "3-15"],
    ),
    examples(
        {"value": "2013-07-04T00:00:00+00:00", "grain": "day"},
        ["7/4"],
    ),
    # ---- Unambiguous DD/MM/YYYY (day > 12) ----
    examples(
        {"value": "2014-03-15T00:00:00+00:00", "grain": "day"},
        ["15/3/2014", "15-3-2014", "15.3.2014", "15/03/2014"],
    ),
    examples(
        {"value": "2013-04-30T00:00:00+00:00", "grain": "day"},
        ["30/4/2013", "30-04-2013"],
    ),
    examples(
        {"value": "1974-10-31T00:00:00+00:00", "grain": "day"},
        ["31/10/1974", "31-10-74", "31.10.1974"],
    ),
    # ---- Bare years ----
    examples(
        {"value": "2014-01-01T00:00:00+00:00", "grain": "year"},
        ["2014"],
    ),
    examples(
        {"value": "1999-01-01T00:00:00+00:00", "grain": "year"},
        ["1999"],
    ),
    examples(
        {"value": "2025-01-01T00:00:00+00:00", "grain": "year"},
        ["2025"],
    ),
    # ---- "the year <n>" ----
    examples(
        {"value": "2014-01-01T00:00:00+00:00", "grain": "year"},
        ["the year 2014"],
    ),
    examples(
        {"value": "1999-01-01T00:00:00+00:00", "grain": "year"},
        ["the year 1999"],
    ),
    examples(
        {"value": "2050-01-01T00:00:00+00:00", "grain": "year"},
        ["the year 2050"],
    ),
    # ---- Ordinal dates: "the 5th", "the 21st", "the third of march" ----
    # These are already covered by the foundation but we keep a couple of
    # smoke checks to guarantee co-existence.
    examples(
        {"value": "2013-03-05T00:00:00+00:00", "grain": "day"},
        ["the 5th"],
    ),
    examples(
        {"value": "2013-02-21T00:00:00+00:00", "grain": "day"},
        ["the 21st"],
    ),
    examples(
        {"value": "2013-03-03T00:00:00+00:00", "grain": "day"},
        ["the third of march", "the 3rd of march"],
    ),
    examples(
        {"value": "2013-03-05T00:00:00+00:00", "grain": "day"},
        ["march 5th", "march 5", "march fifth"],
    ),
    # ---- "<weekday> the <ordinal>" ----
    examples(
        {"value": "2013-08-05T00:00:00+00:00", "grain": "day"},
        ["monday the 5th", "monday the fifth"],
    ),
    examples(
        {"value": "2013-03-05T00:00:00+00:00", "grain": "day"},
        ["tuesday the 5th", "tuesday the 5"],
    ),
    examples(
        {"value": "2013-04-03T00:00:00+00:00", "grain": "day"},
        ["wednesday the third", "wednesday the 3rd"],
    ),
    examples(
        {"value": "2013-02-22T00:00:00+00:00", "grain": "day"},
        ["friday the 22nd", "friday the 22"],
    ),
    # ---- "<ordinal> <weekday>" — n-th weekday from reference month forward ----
    examples(
        {"value": "2013-03-04T00:00:00+00:00", "grain": "day"},
        ["first monday", "the first monday", "1st monday"],
    ),
    examples(
        {"value": "2013-03-11T00:00:00+00:00", "grain": "day"},
        ["second monday", "the second monday", "2nd monday"],
    ),
    examples(
        {"value": "2013-02-15T00:00:00+00:00", "grain": "day"},
        ["third friday", "the third friday", "3rd friday"],
    ),
    examples(
        {"value": "2013-02-28T00:00:00+00:00", "grain": "day"},
        ["fourth thursday", "4th thursday"],
    ),
    # ---- "<ordinal> <weekday> of <month>" ----
    examples(
        {"value": "2013-03-04T00:00:00+00:00", "grain": "day"},
        ["first monday of march", "1st monday of march"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "day"},
        ["first friday of march", "the first friday of march"],
    ),
    examples(
        {"value": "2013-02-25T00:00:00+00:00", "grain": "day"},
        ["fourth monday of february", "4th monday of february"],
    ),
    examples(
        {"value": "2013-11-28T00:00:00+00:00", "grain": "day"},
        ["fourth thursday of november", "the 4th thursday of november"],
    ),
)
