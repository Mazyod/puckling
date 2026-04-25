"""Arabic time corpus — adapted from `Duckling/Time/AR/Corpus.hs`.

Reference time: 2013-02-12T04:30:00 UTC, Tuesday. Each example carries the
expected `resolve()` dict, so tests can do a loose subset comparison.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ----- Instants --------------------------------------------------------
    examples(
        {"value": "2013-02-12T00:00:00+00:00", "grain": "day", "type": "value"},
        ["اليوم"],
    ),
    examples(
        {"value": "2013-02-13T00:00:00+00:00", "grain": "day", "type": "value"},
        ["غدا", "غداً", "بكره", "الغد"],
    ),
    examples(
        {"value": "2013-02-11T00:00:00+00:00", "grain": "day", "type": "value"},
        ["أمس", "امس", "البارحة"],
    ),
    examples(
        {"value": "2013-02-14T00:00:00+00:00", "grain": "day", "type": "value"},
        ["بعد غد", "يوم بعد غد"],
    ),
    examples(
        {"value": "2013-02-10T00:00:00+00:00", "grain": "day", "type": "value"},
        ["قبل امس", "قبل أمس"],
    ),
    # ----- Days of week (notImmediate) -------------------------------------
    examples(
        {"value": "2013-02-18T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الاثنين", "الإثنين"],
    ),
    examples(
        {"value": "2013-02-19T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الثلاثاء"],
    ),
    examples(
        {"value": "2013-02-13T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الاربعاء", "الأربعاء"],
    ),
    examples(
        {"value": "2013-02-14T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الخميس"],
    ),
    examples(
        {"value": "2013-02-15T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الجمعة"],
    ),
    examples(
        {"value": "2013-02-16T00:00:00+00:00", "grain": "day", "type": "value"},
        ["السبت"],
    ),
    examples(
        {"value": "2013-02-17T00:00:00+00:00", "grain": "day", "type": "value"},
        ["الاحد", "الأحد"],
    ),
    # ----- Day-of-month + month -------------------------------------------
    examples(
        {"value": "2013-04-04T00:00:00+00:00", "grain": "day", "type": "value"},
        ["4 ابريل", "4 أبريل", "4 من ابريل", "4 نيسان"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "day", "type": "value"},
        ["1 مارس", "1 اذار", "1 آذار"],
    ),
    # ----- HH:MM -----------------------------------------------------------
    examples(
        {"value": "2013-02-12T15:15:00+00:00", "grain": "minute", "type": "value"},
        ["15:15"],
    ),
    examples(
        {"value": "2013-02-12T12:30:00+00:00", "grain": "minute", "type": "value"},
        ["12:30"],
    ),
    examples(
        {"value": "2013-02-12T03:18:00+00:00", "grain": "minute", "type": "value"},
        ["3:18"],
    ),
    # ----- Year ------------------------------------------------------------
    examples(
        {"value": "2015-01-01T00:00:00+00:00", "grain": "year", "type": "value"},
        ["2015"],
    ),
    # ----- In/Ago days -----------------------------------------------------
    examples(
        {"value": "2013-02-15T00:00:00+00:00", "grain": "day", "type": "value"},
        ["بعد 3 ايام", "في 3 ايام", "خلال 3 ايام"],
    ),
    examples(
        {"value": "2013-02-09T00:00:00+00:00", "grain": "day", "type": "value"},
        ["قبل 3 ايام"],
    ),
    # ----- Holidays --------------------------------------------------------
    examples(
        {
            "value": "2013-08-08T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Eid al-Fitr",
        },
        ["عيد الفطر"],
    ),
    examples(
        {
            "value": "2013-10-15T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Eid al-Adha",
        },
        ["عيد الأضحى", "عيد الاضحى"],
    ),
    examples(
        {
            "value": "2013-11-04T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Islamic New Year",
        },
        ["رأس السنة الهجرية", "راس السنة الهجرية"],
    ),
)
