"""Corpus for the supplemental English Time relative + cycle rules.

Reference time: 2013-02-12T04:30:00Z (Tuesday).

Coverage matches the topic list in the unit description:
- "X days/weeks/months/years from now"
- "X days/weeks/months ago"
- "in X days/weeks/months"
- "the next X days", "the last X weeks", "the past X months"
- "X-th <weekday> of <month>"
- "the X of next/last week/month/year"
- "<n> Mondays from now"
- "every <weekday>"
- "the day after tomorrow", "day before yesterday"
- "this morning", "this afternoon", "this evening", "tonight"
- "tomorrow morning", "yesterday evening"
- "early morning", "late afternoon"

Examples use subset matching: only the keys in `expected` must match the
resolved entity's `value` dict. This keeps the corpus tolerant to optional
metadata that the resolver may attach (alternates, holiday, ...).
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ---- "X <grain> from now" / "in X <grain>" ----
    examples(
        {"value": "2013-02-15T04:00:00+00:00", "grain": "hour"},
        ["in 3 days", "3 days from now", "three days from now"],
    ),
    examples(
        {"value": "2013-02-26T00:00:00+00:00", "grain": "day"},
        ["in 2 weeks", "2 weeks from now", "two weeks from now"],
    ),
    examples(
        {"value": "2013-04-01T00:00:00+00:00", "grain": "month"},
        ["in 2 months", "2 months from now"],
    ),
    examples(
        {"value": "2018-02-01T00:00:00+00:00", "grain": "month"},
        ["in 5 years", "5 years from now"],
    ),
    examples(
        {"value": "2013-02-12T04:32:00+00:00", "grain": "second"},
        ["in 2 minutes"],
    ),
    # ---- "X <grain> ago" ----
    examples(
        {"value": "2013-01-22T00:00:00+00:00", "grain": "day"},
        ["3 weeks ago", "three weeks ago"],
    ),
    examples(
        {"value": "2012-12-01T00:00:00+00:00", "grain": "month"},
        ["2 months ago", "two months ago"],
    ),
    examples(
        {"value": "2013-02-05T04:00:00+00:00", "grain": "hour"},
        ["7 days ago"],
    ),
    examples(
        {"value": "2011-02-01T00:00:00+00:00", "grain": "month"},
        ["2 years ago", "two years ago"],
    ),
    # ---- "the next/last/past <n> <grain>" intervals ----
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-02-15T00:00:00+00:00", "grain": "day"},
        },
        ["the next 3 days", "next 3 days", "the coming 3 days"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-01-28T00:00:00+00:00", "grain": "week"},
            "to": {"value": "2013-02-11T00:00:00+00:00", "grain": "week"},
        },
        ["the last 2 weeks", "last 2 weeks", "the past 2 weeks", "past 2 weeks"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2012-11-01T00:00:00+00:00", "grain": "month"},
            "to": {"value": "2013-02-01T00:00:00+00:00", "grain": "month"},
        },
        ["the past 3 months", "past 3 months", "the last 3 months"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-11T00:00:00+00:00", "grain": "week"},
            "to": {"value": "2013-03-11T00:00:00+00:00", "grain": "week"},
        },
        ["the next 4 weeks", "next 4 weeks"],
    ),
    # ---- "<n>-th <weekday> of <month>" ----
    examples(
        {"value": "2013-10-21T00:00:00+00:00", "grain": "day"},
        ["the third monday of october", "third monday of october"],
    ),
    examples(
        {"value": "2013-09-02T00:00:00+00:00", "grain": "day"},
        ["the first monday of september", "first monday of september"],
    ),
    examples(
        {"value": "2013-11-28T00:00:00+00:00", "grain": "day"},
        ["the fourth thursday of november", "fourth thursday of november"],
    ),
    examples(
        {"value": "2013-05-12T00:00:00+00:00", "grain": "day"},
        ["the second sunday of may", "second sunday of may"],
    ),
    # ---- "the <ord> of next/last week|month|year" ----
    examples(
        {"value": "2013-03-05T00:00:00+00:00", "grain": "day"},
        ["the 5th of next month", "the fifth of next month"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "day"},
        ["the 1st of next month", "the first of next month"],
    ),
    examples(
        {"value": "2014-01-03T00:00:00+00:00", "grain": "day"},
        ["the 3rd of next year", "the third of next year"],
    ),
    examples(
        {"value": "2013-01-01T00:00:00+00:00", "grain": "day"},
        ["the 1st of last month", "the first of last month"],
    ),
    # ---- "<n> <weekday>s from now" ----
    examples(
        {"value": "2013-02-24T00:00:00+00:00", "grain": "day"},
        ["2 sundays from now", "two sundays from now"],
    ),
    examples(
        {"value": "2013-03-04T00:00:00+00:00", "grain": "day"},
        ["3 mondays from now", "three mondays from now"],
    ),
    examples(
        {"value": "2013-03-01T00:00:00+00:00", "grain": "day"},
        ["3 fridays from now"],
    ),
    examples(
        {"value": "2013-02-28T00:00:00+00:00", "grain": "day"},
        ["3 thursdays from now"],
    ),
    # ---- "every <weekday>" ----
    examples(
        {"value": "2013-02-18T00:00:00+00:00", "grain": "day"},
        ["every monday", "each monday"],
    ),
    examples(
        {"value": "2013-02-15T00:00:00+00:00", "grain": "day"},
        ["every friday"],
    ),
    examples(
        {"value": "2013-02-19T00:00:00+00:00", "grain": "day"},
        ["every tuesday"],
    ),
    # ---- "the day after tomorrow", "day before yesterday" ----
    examples(
        {"value": "2013-02-14T00:00:00+00:00", "grain": "day"},
        ["the day after tomorrow", "day after tomorrow"],
    ),
    examples(
        {"value": "2013-02-10T00:00:00+00:00", "grain": "day"},
        ["the day before yesterday", "day before yesterday"],
    ),
    # ---- Parts of day with "this/tonight" ----
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T00:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T12:00:00+00:00", "grain": "hour"},
        },
        ["this morning"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T12:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T19:00:00+00:00", "grain": "hour"},
        },
        ["this afternoon"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T18:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-13T00:00:00+00:00", "grain": "hour"},
        },
        ["this evening", "tonight"],
    ),
    # ---- "tomorrow morning", "yesterday evening" — explicit day intervals ----
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-13T00:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-13T12:00:00+00:00", "grain": "hour"},
        },
        ["tomorrow morning"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-13T12:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-13T19:00:00+00:00", "grain": "hour"},
        },
        ["tomorrow afternoon"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-13T18:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-14T00:00:00+00:00", "grain": "hour"},
        },
        ["tomorrow evening", "tomorrow night"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-11T00:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-11T12:00:00+00:00", "grain": "hour"},
        },
        ["yesterday morning"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-11T18:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T00:00:00+00:00", "grain": "hour"},
        },
        ["yesterday evening"],
    ),
    # ---- "early morning" / "late afternoon" ----
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T00:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T06:00:00+00:00", "grain": "hour"},
        },
        ["early morning"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T15:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T19:00:00+00:00", "grain": "hour"},
        },
        ["late afternoon"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T06:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T12:00:00+00:00", "grain": "hour"},
        },
        ["late morning"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T12:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T15:00:00+00:00", "grain": "hour"},
        },
        ["early afternoon"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T21:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-13T00:00:00+00:00", "grain": "hour"},
        },
        ["late evening", "late night"],
    ),
    # ---- "the <weekday> after next" ----
    examples(
        {"value": "2013-02-25T00:00:00+00:00", "grain": "day"},
        ["monday after next", "the monday after next"],
    ),
)
