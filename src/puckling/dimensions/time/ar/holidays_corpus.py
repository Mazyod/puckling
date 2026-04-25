"""Supplemental Arabic time corpus — coverage for `holidays_rules`.

Reference time: 2013-02-12T04:30:00 UTC (Tuesday). Each example asserts the
expected `resolve()` dict subset; tests do partial-key comparison so latent or
auxiliary fields in the resolved value don't cause spurious failures.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ----- Christian holidays --------------------------------------------
    examples(
        {
            "value": "2013-12-25T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Christmas",
        },
        ["عيد الميلاد", "عيد الميلاد المجيد", "كريسماس", "الكريسماس"],
    ),
    examples(
        {
            "value": "2013-03-31T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Easter Sunday",
        },
        ["عيد الفصح", "عيد فصح"],
    ),
    examples(
        {
            "value": "2014-01-01T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "New Year's Day",
        },
        ["رأس السنة الميلادية", "راس السنة الميلادية"],
    ),
    # ----- Islamic holidays not covered by the main file -----------------
    # Mawlid 2013 (24 Jan) is past; resolver picks Mawlid 2014 (13 Jan).
    examples(
        {
            "value": "2014-01-13T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Mawlid",
        },
        ["المولد النبوي", "المولد النبوي الشريف", "عيد المولد", "المولد"],
    ),
    examples(
        {
            "value": "2013-06-06T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Isra and Mi'raj",
        },
        ["الإسراء والمعراج", "الاسراء والمعراج", "ذكرى الإسراء والمعراج"],
    ),
    examples(
        {
            "value": "2013-10-14T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Day of Arafa",
        },
        ["يوم عرفة", "يوم عرفه", "وقفة عرفة"],
    ),
    examples(
        {
            "value": "2013-11-13T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Ashura",
        },
        ["عاشوراء", "يوم عاشوراء"],
    ),
    examples(
        {
            "value": "2013-07-09T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Ramadan",
        },
        ["بداية رمضان", "بداية شهر رمضان", "أول رمضان", "غرة رمضان"],
    ),
    # ----- National holidays --------------------------------------------
    # Kuwait National Day (Feb 25) is the codebase's deployment-context default;
    # other countries' "اليوم الوطني" dates collapse onto this rule.
    examples(
        {
            "value": "2013-02-25T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "National Day",
        },
        ["اليوم الوطني", "العيد الوطني"],
    ),
    examples(
        {
            "value": "2013-05-01T00:00:00+00:00",
            "grain": "day",
            "type": "value",
            "holiday": "Labour Day",
        },
        ["عيد العمال", "يوم العمال"],
    ),
    # ----- Parts of day (latent intervals) ------------------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T04:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T12:00:00+00:00", "grain": "hour"},
        },
        ["صباحا", "صباحاً", "الصباح"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T18:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-13T00:00:00+00:00", "grain": "hour"},
        },
        ["مساء", "مساءً", "المساء"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T18:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-13T00:00:00+00:00", "grain": "hour"},
        },
        ["ليلا", "ليلاً", "الليلة"],
    ),
    # ----- Relative offsets at week/month/year grain --------------------
    # Each value is grain-aligned: weeks anchor to the ISO Monday before the
    # reference (Feb 11), months to the 1st, years to Jan 1.
    examples(
        {"value": "2013-02-25T00:00:00+00:00", "grain": "week", "type": "value"},
        ["بعد اسبوعين", "في 2 اسابيع", "خلال 2 أسابيع"],
    ),
    examples(
        {"value": "2013-05-01T00:00:00+00:00", "grain": "month", "type": "value"},
        ["بعد 3 اشهر", "في 3 شهور", "خلال 3 شهور"],
    ),
    examples(
        {"value": "2015-01-01T00:00:00+00:00", "grain": "year", "type": "value"},
        ["بعد 2 سنوات", "في 2 سنوات", "خلال سنتين"],
    ),
    examples(
        {"value": "2013-01-28T00:00:00+00:00", "grain": "week", "type": "value"},
        ["قبل اسبوعين"],
    ),
    examples(
        {"value": "2012-11-01T00:00:00+00:00", "grain": "month", "type": "value"},
        ["قبل 3 اشهر"],
    ),
    examples(
        {"value": "2011-01-01T00:00:00+00:00", "grain": "year", "type": "value"},
        ["قبل 2 سنوات", "قبل سنتين"],
    ),
    # ----- "كل <weekday>" -----------------------------------------------
    examples(
        {"value": "2013-02-18T00:00:00+00:00", "grain": "day", "type": "value"},
        ["كل اثنين", "كل الاثنين"],
    ),
    examples(
        {"value": "2013-02-15T00:00:00+00:00", "grain": "day", "type": "value"},
        ["كل جمعة", "كل الجمعة"],
    ),
)
