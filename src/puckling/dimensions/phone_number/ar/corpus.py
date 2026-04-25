"""Arabic phone number corpus.

Duckling's PhoneNumber dimension surfaces the matched substring verbatim, so
each phrase resolves to its own literal text. The corpus exercises the common
Middle East dialing formats and Arabic-Indic digit handling.
"""

from __future__ import annotations

from puckling.corpus import Example, examples

CORPUS: tuple[Example, ...] = (
    examples(
        {"value": "+966 50 123 4567", "type": "value"},
        ["+966 50 123 4567"],
    ),
    examples(
        {"value": "+966 050 1234567", "type": "value"},
        ["+966 050 1234567"],
    ),
    examples(
        {"value": "+971 50 123 4567", "type": "value"},
        ["+971 50 123 4567"],
    ),
    examples(
        {"value": "+971-50-123-4567", "type": "value"},
        ["+971-50-123-4567"],
    ),
    examples(
        {"value": "+965 5012 3456", "type": "value"},
        ["+965 5012 3456"],
    ),
    examples(
        {"value": "(02) 1234 5678", "type": "value"},
        ["(02) 1234 5678"],
    ),
    examples(
        {"value": "٠٥٠ ١٢٣٤ ٥٦٧٨", "type": "value"},
        ["٠٥٠ ١٢٣٤ ٥٦٧٨"],
    ),
    examples(
        {"value": "٠٥٠١٢٣٤٥٦٧", "type": "value"},
        ["٠٥٠١٢٣٤٥٦٧"],
    ),
)
