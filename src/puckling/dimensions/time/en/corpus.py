"""Corpus for English Time — selected examples from Duckling's `Time/EN/Corpus.hs`.

Reference time: 2013-02-12T04:30:00Z (Tuesday).

Examples are intentionally a subset focused on the headline patterns; intricate
edge cases (recurring intervals, regional dates, timezone arithmetic) are
covered upstream but live outside this initial port. See `rules.py` for
`# TODO(puckling)` markers that flag the same gaps.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ---- Instants ----
    examples(
        {"value": "2013-02-12T04:30:00+00:00", "grain": "second"},
        ["now", "right now", "just now", "at the moment"],
    ),
    examples(
        {"value": "2013-02-12T00:00:00+00:00", "grain": "day"},
        ["today", "at this time"],
    ),
    examples(
        {"value": "2013-02-13T00:00:00+00:00", "grain": "day"},
        ["tomorrow", "tomorrows"],
    ),
    examples(
        {"value": "2013-02-11T00:00:00+00:00", "grain": "day"},
        ["yesterday"],
    ),
    examples(
        {"value": "2013-02-14T00:00:00+00:00", "grain": "day"},
        ["the day after tomorrow", "day after tomorrow"],
    ),
    examples(
        {"value": "2013-02-10T00:00:00+00:00", "grain": "day"},
        ["the day before yesterday", "day before yesterday"],
    ),
    # ---- Days of the week (next future occurrence) ----
    examples(
        {"value": "2013-02-18T00:00:00+00:00", "grain": "day"},
        ["monday", "mon.", "this monday"],
    ),
    examples(
        {"value": "2013-02-19T00:00:00+00:00", "grain": "day"},
        ["tuesday"],
    ),
    examples(
        {"value": "2013-02-14T00:00:00+00:00", "grain": "day"},
        ["thursday", "thu", "thu."],
    ),
    examples(
        {"value": "2013-02-15T00:00:00+00:00", "grain": "day"},
        ["friday", "fri", "fri."],
    ),
    examples(
        {"value": "2013-02-16T00:00:00+00:00", "grain": "day"},
        ["saturday", "sat", "sat."],
    ),
    examples(
        {"value": "2013-02-17T00:00:00+00:00", "grain": "day"},
        ["sunday", "sun", "sun."],
    ),
    # ---- Next / Last weekday ----
    examples(
        {"value": "2013-02-19T00:00:00+00:00", "grain": "day"},
        ["next tuesday"],
    ),
    examples(
        {"value": "2013-02-20T00:00:00+00:00", "grain": "day"},
        ["next wednesday"],
    ),
    examples(
        {"value": "2013-02-10T00:00:00+00:00", "grain": "day"},
        ["last sunday"],
    ),
    examples(
        {"value": "2013-02-05T00:00:00+00:00", "grain": "day"},
        ["last tuesday"],
    ),
    # ---- Months ----
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "month"},
        ["next March"],
    ),
    examples(
        {"value": "2013-03-03T00:00:00+00:00", "grain": "day"},
        ["march 3", "the third of march"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "day"},
        ["the 1st of march", "first of march", "march first"],
    ),
    examples(
        {"value": "2013-02-15T00:00:00+00:00", "grain": "day"},
        [
            "the 15th of february",
            "15 of february",
            "february the 15th",
            "february 15",
            "15th february",
        ],
    ),
    examples(
        {"value": "2013-08-08T00:00:00+00:00", "grain": "day"},
        ["Aug 8"],
    ),
    examples(
        {"value": "2015-03-03T00:00:00+00:00", "grain": "day"},
        ["march 3 2015", "march 3rd 2015", "3/3/2015", "2015-3-3", "2015-03-03"],
    ),
    examples(
        {"value": "2013-07-04T00:00:00+00:00", "grain": "day"},
        ["4th of july", "4 of july"],
    ),
    examples(
        {"value": "1974-10-31T00:00:00+00:00", "grain": "day"},
        ["10/31/1974", "10-31-74", "10.31.1974"],
    ),
    examples(
        {"value": "2014-10-01T00:00:00+00:00", "grain": "month"},
        ["October 2014", "2014-10", "2014/10"],
    ),
    examples(
        {"value": "2013-02-01T00:00:00+00:00", "grain": "month"},
        ["2/2013"],
    ),
    # ---- Years ----
    examples(
        {"value": "2014-01-01T00:00:00+00:00", "grain": "year"},
        ["in 2014", "in 2014 A.D.", "in 2014 AD"],
    ),
    examples(
        {"value": "2012-01-01T00:00:00+00:00", "grain": "year"},
        ["last year", "last yr"],
    ),
    examples(
        {"value": "2013-01-01T00:00:00+00:00", "grain": "year"},
        ["this year", "current year", "this yr"],
    ),
    examples(
        {"value": "2014-01-01T00:00:00+00:00", "grain": "year"},
        ["next year", "next yr"],
    ),
    # ---- Cycles ----
    examples(
        {"value": "2013-02-11T00:00:00+00:00", "grain": "week"},
        ["this week", "current week"],
    ),
    examples(
        {"value": "2013-02-04T00:00:00+00:00", "grain": "week"},
        ["last week", "past week", "previous week"],
    ),
    examples(
        {"value": "2013-02-18T00:00:00+00:00", "grain": "week"},
        ["next week", "coming week", "upcoming week"],
    ),
    examples(
        {"value": "2013-01-01T00:00:00+00:00", "grain": "month"},
        ["last month"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "month"},
        ["next month"],
    ),
    # ---- Clock times ----
    examples(
        {"value": "2013-02-12T15:00:00+00:00", "grain": "hour"},
        ["at 3pm", "@ 3pm", "3PM", "3pm", "at 3p"],
    ),
    examples(
        {"value": "2013-02-13T03:00:00+00:00", "grain": "hour"},
        ["at 3am", "at 3 AM"],
    ),
    examples(
        {"value": "2013-02-13T03:18:00+00:00", "grain": "minute"},
        ["3:18am"],
    ),
    examples(
        {"value": "2013-02-12T15:30:00+00:00", "grain": "minute"},
        ["3:30pm", "3:30PM", "half past 3pm", "half past three pm"],
    ),
    examples(
        {"value": "2013-02-12T15:15:00+00:00", "grain": "minute"},
        ["3:15pm", "3:15PM", "quarter past 3pm", "a quarter past 3pm"],
    ),
    examples(
        {"value": "2013-02-12T11:45:00+00:00", "grain": "minute"},
        ["a quarter to noon", "11:45am", "15 to noon"],
    ),
    examples(
        {"value": "2013-02-12T12:00:00+00:00", "grain": "hour"},
        ["noon"],
    ),
    examples(
        {"value": "2013-02-13T00:00:00+00:00", "grain": "hour"},
        ["midnight"],
    ),
    examples(
        {"value": "2013-02-12T15:23:24+00:00", "grain": "second"},
        ["15:23:24"],
    ),
    # ---- Relative durations ----
    examples(
        {"value": "2013-02-12T04:32:00+00:00", "grain": "second"},
        ["in 2 minutes"],
    ),
    examples(
        {"value": "2013-02-19T04:00:00+00:00", "grain": "hour"},
        ["in 7 days"],
    ),
    examples(
        {"value": "2013-02-19T00:00:00+00:00", "grain": "day"},
        ["in 1 week", "in a week"],
    ),
    examples(
        {"value": "2013-02-05T04:00:00+00:00", "grain": "hour"},
        ["7 days ago"],
    ),
    examples(
        {"value": "2013-02-05T00:00:00+00:00", "grain": "day"},
        ["a week ago", "one week ago", "1 week ago"],
    ),
    examples(
        {"value": "2011-02-01T00:00:00+00:00", "grain": "month"},
        ["two years ago"],
    ),
    examples(
        {"value": "2013-02-24T00:00:00+00:00", "grain": "day"},
        ["2 sundays from now", "two sundays from now"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "day"},
        ["3 fridays from now", "three fridays from now"],
    ),
    # ---- Intervals ----
    examples(
        {"type": "interval", "to": {"value": "2013-02-13T00:00:00+00:00", "grain": "day"}},
        ["until tomorrow", "before tomorrow"],
    ),
    # ---- Holidays ----
    examples(
        {
            "value": "2013-12-25T00:00:00+00:00",
            "grain": "day",
            "holiday": "Christmas",
        },
        ["xmas", "christmas", "christmas day"],
    ),
    examples(
        {
            "value": "2013-12-31T00:00:00+00:00",
            "grain": "day",
            "holiday": "New Year's Eve",
        },
        ["new year's eve", "new years eve"],
    ),
    examples(
        {
            "value": "2014-01-01T00:00:00+00:00",
            "grain": "day",
            "holiday": "New Year's Day",
        },
        ["new year's day", "new years day"],
    ),
    examples(
        {
            "value": "2013-02-14T00:00:00+00:00",
            "grain": "day",
            "holiday": "Valentine's Day",
        },
        ["valentine's day", "valentine day"],
    ),
    examples(
        {
            "value": "2013-10-31T00:00:00+00:00",
            "grain": "day",
            "holiday": "Halloween",
        },
        ["halloween"],
    ),
    examples(
        {
            "value": "2013-03-31T00:00:00+00:00",
            "grain": "day",
            "holiday": "Easter Sunday",
        },
        ["easter"],
    ),
    examples(
        {
            "value": "2013-04-01T00:00:00+00:00",
            "grain": "day",
            "holiday": "Easter Monday",
        },
        ["easter mon", "easter monday"],
    ),
    examples(
        {
            "value": "2013-11-28T00:00:00+00:00",
            "grain": "day",
            "holiday": "Thanksgiving Day",
        },
        ["thanksgiving day", "thanksgiving"],
    ),
    # ---- Compound: <day> at <tod> ----
    examples(
        {"value": "2013-02-13T17:00:00+00:00", "grain": "hour"},
        ["tomorrow at 5pm"],
    ),
    examples(
        {"value": "2013-02-16T09:00:00+00:00", "grain": "hour"},
        ["at 9am on Saturday", "Saturday at 9am"],
    ),
)
