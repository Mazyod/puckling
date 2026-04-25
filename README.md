# puckling

A Python port of [Facebook Duckling](https://github.com/facebook/duckling) — parses natural-language **English and Arabic** text into structured values: numbers, ordinals, dates, durations, distances, temperatures, money, emails, URLs, phone numbers, and more.

## Quick start

```bash
uv sync --all-extras
uv run pytest
```

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

## Architecture

Puckling mirrors Duckling's parsing model in idiomatic, functional Python:

- **Rules** are pure data: `Rule(name, pattern, prod)`.
- **Patterns** are tuples of `RegexItem` (regex over source text) and `PredicateItem` (predicates over existing tokens).
- **Productions** are pure functions `tuple[Token, ...] → Token | None`.
- **The engine** is a saturating fixed-point parser that applies rules iteratively until no new tokens appear.
- **Resolution** is context-aware (reference time, locale) and dimension-specific.

All public types are `@dataclass(frozen=True, slots=True)` — no mutation. Cross-dimension references go through predicates (`is_numeral`, `is_grain`, …), never imports, so each rule file stays independent.

## Engine budgets

The saturating fixed-point parser is bounded by three caps to prevent runaway
parses on pathological compositional inputs:

| `Options` field      | Default | Disable with |
|----------------------|--------:|--------------|
| `parse_timeout_ms`   | `2000`  | `None`       |
| `max_tokens`         | `10000` | n/a          |
| `max_iterations`     | `50`    | n/a          |

When any cap is hit, the engine returns the tokens it has accumulated so far
(a valid, possibly partial parse). For offline corpus runs where you want
unbounded analysis, pass `Options(parse_timeout_ms=None)`.

## Running scripts safely

Inline smoke tests should always be wrapped with the shell `timeout` so a
runaway parse can't survive the calling shell:

```bash
timeout 5 uv run python -c "
from puckling import parse, Context, Locale, Lang, Options
import datetime as dt
ctx = Context(reference_time=dt.datetime.now(dt.UTC), locale=Locale(Lang.EN))
print(parse('tomorrow at 5pm', ctx, Options()))
"
```

The engine's own budget should be enough on its own, but the shell-level
timeout is belt-and-suspenders against any future engine path that bypasses
the budget check.

## Adding a dimension or locale

To port a Duckling rule file, add:

```
src/puckling/dimensions/<dim>/<lang>/__init__.py
src/puckling/dimensions/<dim>/<lang>/rules.py     # exports RULES: tuple[Rule, ...]
src/puckling/dimensions/<dim>/<lang>/corpus.py    # exports CORPUS: tuple[Example, ...]
tests/dimensions/test_<dim>_<lang>.py
```

The registry auto-discovers any `<dim>/<lang>/rules.py` exporting `RULES`. No central registration list to update.

## Status

Foundation complete. Per-dimension rule sets are being ported in parallel from upstream Haskell sources. See `src/puckling/dimensions/*` for current coverage.

## License

Apache-2.0, mirroring upstream Duckling.
