"""Arabic clock-time corpus — supplements `time/ar/corpus.py`.

Reference time: 2013-02-12T04:30:00 UTC, Tuesday. Each example carries the
expected `resolve()` dict; tests compare values as a loose subset.

Coverage targets the supplemental ruleset in `clock_rules.py` — clock hours,
AM/PM modifiers, half/quarter past, noon, and midnight.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    # ----- "الساعة <H>" — bare o'clock --------------------------------------
    examples(
        {"value": "2013-02-12T05:00:00+00:00", "grain": "hour", "type": "value"},
        ["الساعة 5", "الساعة ٥"],
    ),
    examples(
        {"value": "2013-02-12T08:00:00+00:00", "grain": "hour", "type": "value"},
        ["الساعة 8", "الساعه 8"],
    ),
    examples(
        {"value": "2013-02-12T15:00:00+00:00", "grain": "hour", "type": "value"},
        ["الساعة 15"],
    ),
    # ----- "الساعة <word-hour>" --------------------------------------------
    examples(
        {"value": "2013-02-12T05:00:00+00:00", "grain": "hour", "type": "value"},
        ["الساعة الخامسة"],
    ),
    examples(
        {"value": "2013-02-12T03:00:00+00:00", "grain": "hour", "type": "value"},
        ["الساعة الثالثة"],
    ),
    examples(
        {"value": "2013-02-12T07:00:00+00:00", "grain": "hour", "type": "value"},
        ["الساعة السابعة"],
    ),
    examples(
        {"value": "2013-02-12T12:00:00+00:00", "grain": "hour", "type": "value"},
        ["الساعة الثانية عشرة"],
    ),
    # ----- AM (صباحا / الصبح / فجرا) ---------------------------------------
    examples(
        {"value": "2013-02-12T05:00:00+00:00", "grain": "hour", "type": "value"},
        ["5 صباحا", "٥ صباحا", "5 الصبح"],
    ),
    examples(
        {"value": "2013-02-12T03:00:00+00:00", "grain": "hour", "type": "value"},
        ["3 صباحا", "3 فجرا"],
    ),
    examples(
        {"value": "2013-02-12T00:00:00+00:00", "grain": "hour", "type": "value"},
        ["12 صباحا"],
    ),
    # ----- PM (مساء / ليلا) -------------------------------------------------
    examples(
        {"value": "2013-02-12T17:00:00+00:00", "grain": "hour", "type": "value"},
        ["5 مساء", "5 مساءا", "5 ليلا"],
    ),
    examples(
        {"value": "2013-02-12T20:00:00+00:00", "grain": "hour", "type": "value"},
        ["8 مساء"],
    ),
    examples(
        {"value": "2013-02-12T22:00:00+00:00", "grain": "hour", "type": "value"},
        ["10 ليلا"],
    ),
    # ----- Afternoon (ظهرا / بعد الظهر / عصرا) -----------------------------
    examples(
        {"value": "2013-02-12T15:00:00+00:00", "grain": "hour", "type": "value"},
        ["3 ظهرا", "3 بعد الظهر", "3 عصرا"],
    ),
    examples(
        {"value": "2013-02-12T16:00:00+00:00", "grain": "hour", "type": "value"},
        ["4 عصرا"],
    ),
    # ----- Word-hour + AM/PM -----------------------------------------------
    examples(
        {"value": "2013-02-12T05:00:00+00:00", "grain": "hour", "type": "value"},
        ["الخامسة صباحا"],
    ),
    examples(
        {"value": "2013-02-12T17:00:00+00:00", "grain": "hour", "type": "value"},
        ["الخامسة مساء"],
    ),
    examples(
        {"value": "2013-02-12T15:00:00+00:00", "grain": "hour", "type": "value"},
        ["الثالثة عصرا", "الثالثة بعد الظهر"],
    ),
    # ----- Half past / quarter past / quarter to ---------------------------
    examples(
        {"value": "2013-02-12T05:30:00+00:00", "grain": "minute", "type": "value"},
        ["الساعة 5 و نصف", "الساعة الخامسة و نصف"],
    ),
    examples(
        {"value": "2013-02-12T05:15:00+00:00", "grain": "minute", "type": "value"},
        ["الساعة 5 و ربع", "الساعة الخامسة و ربع"],
    ),
    examples(
        {"value": "2013-02-12T04:45:00+00:00", "grain": "minute", "type": "value"},
        ["الساعة 5 الا ربع", "الساعة الخامسة الا ربع", "الساعة الخامسة إلا ربع"],
    ),
    # ----- Combined word-hour + half + AM/PM (still grain=minute) ----------
    examples(
        {"value": "2013-02-12T08:30:00+00:00", "grain": "minute", "type": "value"},
        ["الساعة الثامنة و نصف"],
    ),
    examples(
        {"value": "2013-02-12T11:45:00+00:00", "grain": "minute", "type": "value"},
        ["الساعة 12 الا ربع"],
    ),
    # ----- "<clock> و <M> دقيقة" -------------------------------------------
    examples(
        {"value": "2013-02-12T05:20:00+00:00", "grain": "minute", "type": "value"},
        ["الساعة 5 و 20 دقيقة"],
    ),
    examples(
        {"value": "2013-02-12T15:15:00+00:00", "grain": "minute", "type": "value"},
        ["الساعة 15 و 15 دقيقة"],
    ),
    # ----- Noon / midnight -------------------------------------------------
    examples(
        {"value": "2013-02-12T12:00:00+00:00", "grain": "hour", "type": "value"},
        ["منتصف النهار"],
    ),
    examples(
        {"value": "2013-02-12T00:00:00+00:00", "grain": "hour", "type": "value"},
        ["منتصف الليل"],
    ),
    # ----- HH:MM with AM/PM suffix -----------------------------------------
    examples(
        {"value": "2013-02-12T03:18:00+00:00", "grain": "minute", "type": "value"},
        ["3:18 صباحا"],
    ),
    examples(
        {"value": "2013-02-12T15:20:00+00:00", "grain": "minute", "type": "value"},
        ["3:20 مساء", "3:20 عصرا"],
    ),
    examples(
        {"value": "2013-02-12T11:45:00+00:00", "grain": "minute", "type": "value"},
        ["11:45 صباحا"],
    ),
)
