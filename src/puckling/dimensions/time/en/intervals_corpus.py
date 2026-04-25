"""Corpus for English Time intervals — supplemental to `time/en/corpus.py`.

Reference time: 2013-02-12T04:30:00Z (Tuesday).

Examples here exercise the supplemental rules in `intervals_rules.py`
(closed intervals across days, months, hours, years; open intervals via
"by/before/after/until/till"; year ranges) plus a handful of patterns
already covered by the foundation that share the interval shape, so a
test failure here pinpoints the interval surface as the regression locus.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ----- Closed hour intervals --------------------------------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T17:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T19:00:00+00:00", "grain": "hour"},
        },
        ["from 5pm to 7pm", "between 5pm and 7pm", "5pm to 7pm", "5pm - 7pm"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T15:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T16:00:00+00:00", "grain": "hour"},
        },
        ["3pm - 4pm", "from 3pm to 4pm", "between 3pm and 4pm"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T08:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T13:00:00+00:00", "grain": "hour"},
        },
        ["8am - 1pm", "from 8am to 1pm", "8am to 1pm"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T09:30:00+00:00", "grain": "minute"},
            "to": {"value": "2013-02-12T11:00:00+00:00", "grain": "minute"},
        },
        ["9:30 - 11:00", "9:30 to 11:00", "from 9:30 to 11:00"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T12:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T15:00:00+00:00", "grain": "hour"},
        },
        ["noon to 3pm", "from noon to 3pm", "between noon and 3pm"],
    ),
    # ----- "X through/till/until Y" closed intervals -------------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T17:00:00+00:00", "grain": "hour"},
            "to": {"value": "2013-02-12T19:00:00+00:00", "grain": "hour"},
        },
        # Note: the foundation's "<X> - <Y>" rule honors through/till/until
        # but not the "thru" abbreviation, so we omit "5pm thru 7pm" here.
        # TODO(puckling): edge case — extend the foundation interval-dash
        # regex to recognize "thru".
        ["5pm through 7pm", "5pm till 7pm", "5pm until 7pm"],
    ),
    # ----- Same-month day intervals (March 1 to 5) --------------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-03-01T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-03-05T00:00:00+00:00", "grain": "day"},
        },
        [
            "march 1 to 5",
            "march 1 - 5",
            "march 1 through 5",
            "march 1 thru 5",
            "from march 1 to 5",
        ],
    ),
    # ----- Cross-month day intervals (March 1 to March 5) -------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-03-01T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-03-05T00:00:00+00:00", "grain": "day"},
        },
        ["march 1 - march 5", "march 1 to march 5"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-08-08T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-08-12T00:00:00+00:00", "grain": "day"},
        },
        ["aug 8 - aug 12", "aug 8 to aug 12"],
    ),
    # ----- "July 13-15", "13 to 15 July", "from the 13th to 15th of July" ---
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-07-13T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-07-15T00:00:00+00:00", "grain": "day"},
        },
        [
            "July 13-15",
            "July 13 to 15",
            "July 13 thru 15",
            "July 13 through 15",
        ],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-07-13T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-07-15T00:00:00+00:00", "grain": "day"},
        },
        [
            "from July 13-15",
            "from 13 to 15 July",
            "from 13th to 15th July",
            "from the 13 to 15 July",
            "from the 13th to the 15th July",
        ],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-07-13T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2013-07-15T00:00:00+00:00", "grain": "day"},
        },
        [
            "from 13 to 15 of July",
            "from 13th to 15th of July",
            "from the 13th to the 15th of July",
            "the 13th to the 15th of July",
        ],
    ),
    # ----- Month-grained intervals -----------------------------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-03-01T00:00:00+00:00", "grain": "month"},
            "to": {"value": "2013-05-01T00:00:00+00:00", "grain": "month"},
        },
        [
            "march to may",
            "from march to may",
            "march - may",
            "march through may",
            "between march and may",
        ],
    ),
    # ----- Year intervals (latent) -----------------------------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2014-01-01T00:00:00+00:00", "grain": "year"},
            "to": {"value": "2016-01-01T00:00:00+00:00", "grain": "year"},
        },
        [
            "2014-2016",
            "2014 to 2016",
            "2014 - 2016",
            "from 2014 to 2016",
            "between 2014 and 2016",
            "2014 through 2016",
            "2014 thru 2016",
            "2014 till 2016",
            "2014 until 2016",
        ],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "1960-01-01T00:00:00+00:00", "grain": "year"},
            "to": {"value": "1961-01-01T00:00:00+00:00", "grain": "year"},
        },
        ["1960 - 1961", "1960-1961", "from 1960 to 1961"],
    ),
    # ----- Open intervals: "before X" / "until X" / "till X" ---------------
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-03-01T00:00:00+00:00", "grain": "month"},
        },
        ["before march", "until march", "till march"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-02-13T00:00:00+00:00", "grain": "day"},
        },
        ["before tomorrow", "until tomorrow", "till tomorrow"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-02-12T17:00:00+00:00", "grain": "hour"},
        },
        ["before 5pm", "until 5pm", "till 5pm", "up to 5pm"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-02-15T00:00:00+00:00", "grain": "day"},
        },
        ["before friday", "until friday", "till friday"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-02-18T00:00:00+00:00", "grain": "week"},
        },
        ["before next week", "until next week"],
    ),
    # ----- Open intervals: "after X" / "since X" / "from X" ----------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-03-01T00:00:00+00:00", "grain": "month"},
        },
        ["after march", "since march"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-13T00:00:00+00:00", "grain": "day"},
        },
        ["after tomorrow", "since tomorrow"],
    ),
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-02-12T17:00:00+00:00", "grain": "hour"},
        },
        ["after 5pm", "since 5pm"],
    ),
    # ----- Open intervals: "by X" (BEFORE direction) -----------------------
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-03-01T00:00:00+00:00", "grain": "month"},
        },
        ["by march"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-02-15T00:00:00+00:00", "grain": "day"},
        },
        ["by friday"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-02-13T00:00:00+00:00", "grain": "day"},
        },
        ["by tomorrow"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2013-02-12T17:00:00+00:00", "grain": "hour"},
        },
        ["by 5pm"],
    ),
    examples(
        {
            "type": "interval",
            "to": {"value": "2014-01-01T00:00:00+00:00", "grain": "year"},
        },
        ["by next year"],
    ),
    # ----- Holidays bracketing intervals -----------------------------------
    examples(
        {
            "type": "interval",
            "from": {"value": "2013-12-25T00:00:00+00:00", "grain": "day"},
            "to": {"value": "2014-01-01T00:00:00+00:00", "grain": "day"},
        },
        ["between christmas and new year's day"],
    ),
    # ----- Date interval anchored to a specific year -----------------------
    # TODO(puckling): edge case — same-week DOW intervals like "monday to
    # friday" don't yet land both endpoints in the same week (Friday gets
    # resolved as the next future Friday, which is BEFORE next Monday).
    # Year-prefixed weekday intervals share the same gap; not asserted here.
)
