"""Supplemental corpus for English Time — holidays and seasons.

Reference time: 2013-02-12T04:30:00Z (Tuesday).

These examples cover the additions in `holidays_rules.py` (Memorial Day,
Columbus Day, Canadian Thanksgiving, seasons, year-relative holidays, etc.)
plus extra phrase variants for foundation holidays already wired in
`rules.py`.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ---- Fixed-date supplemental holidays ----
    examples(
        {
            "value": "2013-05-05T00:00:00+00:00",
            "grain": "day",
            "holiday": "Cinco de Mayo",
        },
        ["cinco de mayo"],
    ),
    examples(
        {
            "value": "2013-06-19T00:00:00+00:00",
            "grain": "day",
            "holiday": "Juneteenth",
        },
        ["juneteenth", "juneteenth national independence day"],
    ),
    examples(
        {
            "value": "2013-11-11T00:00:00+00:00",
            "grain": "day",
            "holiday": "Veterans Day",
        },
        ["veterans day", "veteran's day", "armistice day"],
    ),
    examples(
        {
            "value": "2013-06-14T00:00:00+00:00",
            "grain": "day",
            "holiday": "Flag Day",
        },
        ["flag day"],
    ),
    examples(
        {
            "value": "2014-02-02T00:00:00+00:00",
            "grain": "day",
            "holiday": "Groundhog Day",
        },
        ["groundhog day", "groundhog's day"],
    ),
    examples(
        {
            "value": "2013-09-11T00:00:00+00:00",
            "grain": "day",
            "holiday": "Patriot Day",
        },
        ["patriot day"],
    ),
    examples(
        {
            "value": "2013-07-14T00:00:00+00:00",
            "grain": "day",
            "holiday": "Bastille Day",
        },
        ["bastille day"],
    ),
    examples(
        {
            "value": "2013-07-01T00:00:00+00:00",
            "grain": "day",
            "holiday": "Canada Day",
        },
        ["canada day"],
    ),
    examples(
        {
            "value": "2013-11-05T00:00:00+00:00",
            "grain": "day",
            "holiday": "Guy Fawkes Day",
        },
        ["guy fawkes day", "guy fawkes night", "bonfire night"],
    ),
    examples(
        {
            "value": "2013-11-11T00:00:00+00:00",
            "grain": "day",
            "holiday": "Remembrance Day",
        },
        ["remembrance day", "poppy day"],
    ),
    # ---- Computed holidays ----
    examples(
        {
            "value": "2013-05-27T00:00:00+00:00",
            "grain": "day",
            "holiday": "Memorial Day",
        },
        ["memorial day"],
    ),
    examples(
        {
            "value": "2013-10-14T00:00:00+00:00",
            "grain": "day",
            "holiday": "Columbus Day",
        },
        ["columbus day"],
    ),
    examples(
        {
            "value": "2013-10-14T00:00:00+00:00",
            "grain": "day",
            "holiday": "Canadian Thanksgiving",
        },
        ["canadian thanksgiving", "canadian thanksgiving day"],
    ),
    examples(
        {
            "value": "2013-02-18T00:00:00+00:00",
            "grain": "day",
            "holiday": "Presidents' Day",
        },
        ["presidents day", "presidents' day", "washington's birthday"],
    ),
    # ---- Seasons (Northern Hemisphere intervals) ----
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-06-21T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-09-23T00:00:00+00:00", "grain": "day"},
        },
        ["summer"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-09-23T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-12-21T00:00:00+00:00", "grain": "day"},
        },
        ["fall", "autumn"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-12-21T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2014-03-20T00:00:00+00:00", "grain": "day"},
        },
        ["winter"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-03-20T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-06-21T00:00:00+00:00", "grain": "day"},
        },
        ["spring"],
    ),
    # ---- Year-relative holidays ----
    examples(
        {
            "value": "2015-04-05T00:00:00+00:00",
            "grain": "day",
            "holiday": "Easter Sunday",
        },
        ["easter 2015", "easter in 2015", "easter of 2015"],
    ),
    examples(
        {
            "value": "2015-12-25T00:00:00+00:00",
            "grain": "day",
            "holiday": "Christmas",
        },
        ["christmas 2015", "xmas 2015", "christmas in 2015"],
    ),
    examples(
        {
            "value": "2014-10-31T00:00:00+00:00",
            "grain": "day",
            "holiday": "Halloween",
        },
        ["halloween 2014", "halloween in 2014"],
    ),
    examples(
        {
            "value": "2016-11-24T00:00:00+00:00",
            "grain": "day",
            "holiday": "Thanksgiving Day",
        },
        ["thanksgiving 2016"],
    ),
    examples(
        {
            "value": "2014-02-14T00:00:00+00:00",
            "grain": "day",
            "holiday": "Valentine's Day",
        },
        ["valentine's day 2014", "valentine's day in 2014"],
    ),
    examples(
        {
            "value": "2015-05-25T00:00:00+00:00",
            "grain": "day",
            "holiday": "Memorial Day",
        },
        ["memorial day 2015"],
    ),
    # ---- Day before / after holiday ----
    examples(
        {"value": "2013-12-24T00:00:00+00:00", "grain": "day"},
        ["the day before christmas", "day before christmas"],
    ),
    examples(
        {"value": "2013-12-26T00:00:00+00:00", "grain": "day"},
        ["the day after christmas", "day after christmas"],
    ),
    # ---- Foundation holidays — extra phrase variants ----
    examples(
        {
            "value": "2013-12-26T00:00:00+00:00",
            "grain": "day",
            "holiday": "Boxing Day",
        },
        ["boxing day", "st stephen's day", "st. stephen's day"],
    ),
    examples(
        {
            "value": "2013-07-04T00:00:00+00:00",
            "grain": "day",
            "holiday": "Independence Day",
        },
        ["independence day"],
    ),
    examples(
        {
            "value": "2013-12-24T00:00:00+00:00",
            "grain": "day",
            "holiday": "Christmas Eve",
        },
        ["christmas eve", "xmas eve"],
    ),
    examples(
        {
            "value": "2013-04-22T00:00:00+00:00",
            "grain": "day",
            "holiday": "Earth Day",
        },
        ["earth day"],
    ),
    examples(
        {
            "value": "2013-03-29T00:00:00+00:00",
            "grain": "day",
            "holiday": "Good Friday",
        },
        ["good friday"],
    ),
    examples(
        {
            "value": "2013-03-24T00:00:00+00:00",
            "grain": "day",
            "holiday": "Palm Sunday",
        },
        ["palm sunday"],
    ),
    examples(
        {
            "value": "2013-04-01T00:00:00+00:00",
            "grain": "day",
            "holiday": "April Fools",
        },
        ["april fools", "april fool's day"],
    ),
    examples(
        {
            "value": "2013-09-02T00:00:00+00:00",
            "grain": "day",
            "holiday": "Labor Day",
        },
        ["labor day"],
    ),
    examples(
        {
            "value": "2013-05-12T00:00:00+00:00",
            "grain": "day",
            "holiday": "Mother's Day",
        },
        ["mother's day", "mothers day"],
    ),
    examples(
        {
            "value": "2013-06-16T00:00:00+00:00",
            "grain": "day",
            "holiday": "Father's Day",
        },
        ["father's day", "fathers day"],
    ),
    examples(
        {
            "value": "2014-01-20T00:00:00+00:00",
            "grain": "day",
            "holiday": "Martin Luther King's Day",
        },
        ["mlk day", "martin luther king day", "civil rights day"],
    ),
    examples(
        {
            "value": "2013-05-25T00:00:00+00:00",
            "grain": "day",
            "holiday": "Africa Day",
        },
        ["africa day", "african liberation day"],
    ),
    examples(
        {
            "value": "2013-05-01T00:00:00+00:00",
            "grain": "day",
            "holiday": "May Day",
        },
        ["may day"],
    ),
    examples(
        {
            "value": "2013-03-17T00:00:00+00:00",
            "grain": "day",
            "holiday": "St Patrick's Day",
        },
        ["st patrick's day", "saint patrick's day", "st. paddy's day"],
    ),
    examples(
        {
            "value": "2014-01-06T00:00:00+00:00",
            "grain": "day",
            "holiday": "Epiphany",
        },
        ["epiphany"],
    ),
    examples(
        {
            "value": "2013-11-01T00:00:00+00:00",
            "grain": "day",
            "holiday": "All Saints' Day",
        },
        ["all saints' day"],
    ),
)
