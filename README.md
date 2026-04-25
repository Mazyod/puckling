# Puckling

[![PyPI version](https://img.shields.io/pypi/v/puckling.svg?logo=pypi&logoColor=white)](https://pypi.org/project/puckling/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Tests](https://github.com/Mazyod/puckling/actions/workflows/python-tests.yml/badge.svg)](https://github.com/Mazyod/puckling/actions/workflows/python-tests.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

_A Python port of [Facebook Duckling](https://github.com/facebook/duckling), scoped to **English and Arabic**._

<!-- TODO: replace with uploaded image URL from GitHub user-attachments -->
<!-- <img width="1423" height="551" alt="puckling-splash" src="https://github.com/user-attachments/assets/REPLACE-ME" /> -->

__Puckling__ parses natural-language English and Arabic into structured values: numbers, ordinals, dates, durations, distances, temperatures, money, emails, URLs, phone numbers, and more.

The library has minimal dependencies (`regex` for PCRE-compatible Unicode patterns).

## Installation

```sh
pip install puckling
```

## Usage

```python
import datetime as dt
from puckling import Context, Lang, Locale, Options, parse

ctx = Context(
    reference_time=dt.datetime(2013, 2, 12, 4, 30, tzinfo=dt.UTC),
    locale=Locale(Lang.EN),
)

for entity in parse("I'll meet you tomorrow at 5pm for $50", ctx, Options()):
    print(entity)
```

Switch `Locale(Lang.EN)` to `Locale(Lang.AR)` for Arabic input.

## Supported dimensions

| Dimension          | EN | AR | Notes |
|--------------------|:--:|:--:|-------|
| Numeral            | :white_check_mark: | :white_check_mark: | Cardinals, decimals, Arabic-Indic digits |
| Ordinal            | :white_check_mark: | :white_check_mark: | |
| Time               | :white_check_mark: | :white_check_mark: | Dates, clock times, holidays, intervals |
| Duration           | :white_check_mark: | :white_check_mark: | |
| Distance           | :white_check_mark: | :white_check_mark: | |
| Temperature        | :white_check_mark: | :white_check_mark: | |
| Quantity           | :white_check_mark: | :white_check_mark: | |
| Volume             | :white_check_mark: | :white_check_mark: | |
| AmountOfMoney      | :white_check_mark: | :white_check_mark: | |
| Email              | :white_check_mark: | :white_check_mark: | Locale-agnostic |
| URL                | :white_check_mark: | :white_check_mark: | Locale-agnostic |
| PhoneNumber        | :white_check_mark: | :white_check_mark: | |
| CreditCardNumber   | :white_check_mark: | :white_check_mark: | Locale-agnostic |

> Locale-agnostic dimensions (Email, URL, CreditCard) match across both `Lang.EN` and `Lang.AR` contexts.

## Architecture

Puckling mirrors Duckling's parsing model in idiomatic, functional Python:

- **Rules** are pure data: `Rule(name, pattern, prod)`.
- **Patterns** are tuples of `RegexItem` (regex over source text) and `PredicateItem` (predicates over existing tokens).
- **Productions** are pure functions `tuple[Token, ...] → Token | None`.
- **The engine** is a saturating fixed-point parser that applies rules iteratively until no new tokens appear.
- **Resolution** is context-aware (reference time, locale) and dimension-specific.

All public types are `@dataclass(frozen=True, slots=True)` — no mutation. Cross-dimension references go through predicates (`is_numeral`, `is_grain`, …), never imports, so each rule file stays independent.

## Engine budgets

The saturating fixed-point parser is bounded by three caps to prevent runaway parses on pathological compositional inputs:

| `Options` field      | Default | Disable with |
|----------------------|--------:|--------------|
| `parse_timeout_ms`   | `2000`  | `None`       |
| `max_tokens`         | `10000` | n/a          |
| `max_iterations`     | `50`    | n/a          |

When any cap is hit, the engine returns the tokens it has accumulated so far (a valid, possibly partial parse). For offline corpus runs where you want unbounded analysis, pass `Options(parse_timeout_ms=None)`.

## Running scripts safely

Inline smoke tests should always be wrapped with the shell `timeout` so a runaway parse can't survive the calling shell:

```sh
timeout 5 uv run python -c "
from puckling import parse, Context, Locale, Lang, Options
import datetime as dt
ctx = Context(reference_time=dt.datetime.now(dt.UTC), locale=Locale(Lang.EN))
print(parse('tomorrow at 5pm', ctx, Options()))
"
```

The engine's own budget should be enough on its own, but the shell-level timeout is belt-and-suspenders against any future engine path that bypasses the budget check.

## Development

- Requires Python 3.13+.
- Requires `uv` for dev dependencies.

```sh
uv sync --all-extras
uv run pytest
```

### Adding a dimension or locale

To port a Duckling rule file, add:

```
src/puckling/dimensions/<dim>/<lang>/__init__.py
src/puckling/dimensions/<dim>/<lang>/rules.py     # exports RULES: tuple[Rule, ...]
src/puckling/dimensions/<dim>/<lang>/corpus.py    # exports CORPUS: tuple[Example, ...]
tests/dimensions/test_<dim>_<lang>.py
```

The registry auto-discovers any `<dim>/<lang>/rules.py` exporting `RULES`. No central registration list to update.

## License

Apache-2.0, mirroring upstream Duckling.
