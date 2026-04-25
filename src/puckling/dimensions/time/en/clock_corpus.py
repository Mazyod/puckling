"""Corpus for the supplemental English clock-time rules.

Reference time: 2013-02-12T04:30:00Z (Tuesday).

These examples mirror the topics described in Duckling's `Time/EN/Corpus.hs`
for clock times: AM/PM, "X o'clock", half/quarter past/to, noon/midnight,
24-hour clock variants, precision modifiers, and times with seconds.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ---- AM / PM (digit) ----
    examples(
        {"value": "2013-02-12T17:00:00+00:00", "grain": "hour", "type": "value"},
        ["5pm", "5 pm", "5 PM", "5 P.M.", "5 p.m.", "5 P M", "at 5pm"],
    ),
    examples(
        {"value": "2013-02-12T05:00:00+00:00", "grain": "hour", "type": "value"},
        ["5am", "5 am", "5 AM", "5 A.M.", "5 a.m.", "at 5am"],
    ),
    examples(
        {"value": "2013-02-12T11:00:00+00:00", "grain": "hour", "type": "value"},
        ["11am", "11 a.m.", "11 AM"],
    ),
    examples(
        {"value": "2013-02-12T23:00:00+00:00", "grain": "hour", "type": "value"},
        ["11pm", "11 p.m.", "11 PM"],
    ),
    # ---- AM / PM (word) ----
    examples(
        {"value": "2013-02-12T17:00:00+00:00", "grain": "hour", "type": "value"},
        ["five PM", "five pm", "five p.m."],
    ),
    examples(
        {"value": "2013-02-12T07:00:00+00:00", "grain": "hour", "type": "value"},
        ["seven AM", "seven am", "seven a.m."],
    ),
    examples(
        {"value": "2013-02-12T14:00:00+00:00", "grain": "hour", "type": "value"},
        ["two pm", "two PM"],
    ),
    # ---- 12 PM / 12 AM edge cases ----
    examples(
        {"value": "2013-02-12T12:00:00+00:00", "grain": "hour", "type": "value"},
        ["12pm", "12 pm", "12 PM"],
    ),
    examples(
        {"value": "2013-02-13T00:00:00+00:00", "grain": "hour", "type": "value"},
        ["12am", "12 am", "12 AM"],
    ),
    # ---- "X o'clock" ----
    examples(
        {"value": "2013-02-12T05:00:00+00:00", "grain": "hour", "type": "value"},
        ["5 o'clock", "5 oclock", "five o'clock", "five oclock"],
    ),
    examples(
        {"value": "2013-02-12T08:00:00+00:00", "grain": "hour", "type": "value"},
        ["8 o'clock", "eight o'clock"],
    ),
    # ---- Half past ----
    examples(
        {"value": "2013-02-12T05:30:00+00:00", "grain": "minute", "type": "value"},
        [
            "half past 5",
            "half past five",
            "half past 5 am",
            "half past five am",
            "5:30",
            "5:30 am",
            "five thirty",
            "five thirty am",
        ],
    ),
    examples(
        {"value": "2013-02-12T17:30:00+00:00", "grain": "minute", "type": "value"},
        [
            "half past 5pm",
            "half past five pm",
            "5:30pm",
            "5:30 PM",
        ],
    ),
    # ---- Quarter past ----
    examples(
        {"value": "2013-02-12T05:15:00+00:00", "grain": "minute", "type": "value"},
        [
            "quarter past 5",
            "quarter past five",
            "a quarter past 5",
            "a quarter past five",
            "5:15",
            "5:15am",
            "five fifteen",
        ],
    ),
    examples(
        {"value": "2013-02-12T15:15:00+00:00", "grain": "minute", "type": "value"},
        [
            "quarter past 3pm",
            "quarter past three pm",
            "3:15pm",
            "3:15 PM",
        ],
    ),
    # ---- Quarter to ----
    examples(
        {"value": "2013-02-12T05:45:00+00:00", "grain": "minute", "type": "value"},
        [
            "quarter to 6",
            "quarter to six",
            "a quarter to 6",
            "a quarter to six",
            "5:45",
            "five forty five",
        ],
    ),
    examples(
        {"value": "2013-02-12T11:45:00+00:00", "grain": "minute", "type": "value"},
        [
            "quarter to noon",
            "a quarter to noon",
            "11:45am",
            "11:45 AM",
            "15 to noon",
            "fifteen to noon",
        ],
    ),
    # ---- Half (British) ----
    examples(
        {"value": "2013-02-12T05:30:00+00:00", "grain": "minute", "type": "value"},
        ["half five"],
    ),
    examples(
        {"value": "2013-02-12T07:30:00+00:00", "grain": "minute", "type": "value"},
        ["half seven", "half past seven", "half past 7", "7:30", "seven thirty"],
    ),
    # ---- "<n> minutes past/to <H>" ----
    examples(
        {"value": "2013-02-12T05:05:00+00:00", "grain": "minute", "type": "value"},
        ["5 minutes past 5", "five minutes past five"],
    ),
    examples(
        {"value": "2013-02-12T05:55:00+00:00", "grain": "minute", "type": "value"},
        [
            "5 minutes to 6",
            "five minutes to six",
            "5 min to 6",
            "5 mins to 6",
        ],
    ),
    examples(
        {"value": "2013-02-12T05:20:00+00:00", "grain": "minute", "type": "value"},
        ["twenty past 5", "twenty past five", "20 past 5"],
    ),
    examples(
        {"value": "2013-02-12T05:50:00+00:00", "grain": "minute", "type": "value"},
        ["ten to 6", "ten to six", "10 to 6"],
    ),
    # ---- Noon / Midnight ----
    examples(
        {"value": "2013-02-12T12:00:00+00:00", "grain": "hour", "type": "value"},
        ["noon", "twelve noon", "12 noon"],
    ),
    examples(
        {"value": "2013-02-13T00:00:00+00:00", "grain": "hour", "type": "value"},
        ["midnight", "twelve midnight", "12 midnight"],
    ),
    # ---- Times with seconds ----
    examples(
        {"value": "2013-02-12T15:23:24+00:00", "grain": "second", "type": "value"},
        ["15:23:24"],
    ),
    examples(
        {"value": "2013-02-12T05:30:45+00:00", "grain": "second", "type": "value"},
        ["5:30:45", "05:30:45"],
    ),
    examples(
        {"value": "2013-02-12T23:59:59+00:00", "grain": "second", "type": "value"},
        ["23:59:59"],
    ),
    # ---- 24-hour clock variants ----
    examples(
        {"value": "2013-02-12T17:30:00+00:00", "grain": "minute", "type": "value"},
        ["17:30", "17h30"],
    ),
    examples(
        {"value": "2013-02-12T17:00:00+00:00", "grain": "hour", "type": "value"},
        ["17h"],
    ),
    examples(
        {"value": "2013-02-12T17:00:00+00:00", "grain": "minute", "type": "value"},
        ["17h00", "17:00"],
    ),
    examples(
        {"value": "2013-02-12T23:59:00+00:00", "grain": "minute", "type": "value"},
        ["23:59", "23h59"],
    ),
    # ---- Precision modifiers ----
    examples(
        {"value": "2013-02-12T17:00:00+00:00", "grain": "hour", "type": "value"},
        [
            "around 5pm",
            "about 5pm",
            "approximately 5pm",
            "approx. 5pm",
            "roughly 5pm",
            "exactly 5pm",
            "precisely 5pm",
            "right at 5pm",
            "right around 5pm",
            "circa 5pm",
            "5pm sharp",
            "5pm exactly",
        ],
    ),
    examples(
        {"value": "2013-02-12T12:00:00+00:00", "grain": "hour", "type": "value"},
        ["around noon", "exactly noon", "approximately noon"],
    ),
    examples(
        {"value": "2013-02-12T05:00:00+00:00", "grain": "minute", "type": "value"},
        ["5:00 sharp", "5:00 exactly"],
    ),
    # ---- Compound: "<X> at <time>" / "<time> on <day>" ----
    examples(
        {"value": "2013-02-13T17:00:00+00:00", "grain": "hour", "type": "value"},
        ["tomorrow at 5pm", "tomorrow at exactly 5pm"],
    ),
    examples(
        {"value": "2013-02-13T17:30:00+00:00", "grain": "minute", "type": "value"},
        ["tomorrow at 5:30pm", "tomorrow at half past 5pm"],
    ),
    # ---- Word-form clock: "five thirty pm" ----
    examples(
        {"value": "2013-02-12T14:30:00+00:00", "grain": "minute", "type": "value"},
        ["two thirty pm", "2:30pm", "2:30 PM", "half past 2pm"],
    ),
    examples(
        {"value": "2013-02-12T11:45:00+00:00", "grain": "minute", "type": "value"},
        ["eleven forty five am", "11:45am"],
    ),
    # ---- "@" alias ----
    examples(
        {"value": "2013-02-12T15:00:00+00:00", "grain": "hour", "type": "value"},
        ["@ 3pm", "at 3pm", "3pm"],
    ),
)
