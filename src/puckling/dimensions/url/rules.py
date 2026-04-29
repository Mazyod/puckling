"""URL grammar rules — locale-agnostic.

Ported from `Duckling/Url/Rules.hs`. Three rules cover:

  * generic URLs with optional protocol, www-style host, port, path, query,
    fragment;
  * `localhost` with optional protocol, port, path, query;
  * `<protocol>://<host>` URLs whose host has no dotted TLD.
"""

from __future__ import annotations

from puckling.dimensions.url.types import url
from puckling.types import RegexMatch, Rule, Token, regex

_URL_START_BOUNDARY = r"(?<![\w@./:-])"
_URL_END_BOUNDARY = r"(?![\w:@-])"
_LOCAL_URL_END_BOUNDARY = r"(?![\w:@.-])"


def _groups(tokens: tuple[Token, ...]) -> tuple[str | None, ...]:
    rm = tokens[0].value
    assert isinstance(rm, RegexMatch)
    return rm.groups


def _prod_url(tokens: tuple[Token, ...]) -> Token | None:
    # Domain is group 5 of the outer pattern (see _URL_RULE pattern below).
    domain = _groups(tokens)[4]
    if not domain:
        return None
    return Token(dim="url", value=url(tokens[0].value.text, domain.lower()))


def _prod_localhost(tokens: tuple[Token, ...]) -> Token | None:
    return Token(dim="url", value=url(tokens[0].value.text, "localhost"))


def _prod_local_url(tokens: tuple[Token, ...]) -> Token | None:
    # Domain is group 3 of the outer pattern (see _LOCAL_URL_RULE pattern below).
    domain = _groups(tokens)[2]
    if not domain:
        return None
    return Token(dim="url", value=url(tokens[0].value.text, domain))


_URL_RULE = Rule(
    name="url",
    pattern=(
        regex(
            _URL_START_BOUNDARY
            + r"((([a-zA-Z]+)://)?(w{2,3}[0-9]*\.)?(([\w_-]+\.)+[a-z]{2,4})(:(\d+))?(/[^?\s#]*)?(\?[^\s#]+)?(#[\-,*=&a-z0-9]+)?)"
            + _URL_END_BOUNDARY
        ),
    ),
    prod=_prod_url,
)

_LOCALHOST_RULE = Rule(
    name="localhost",
    pattern=(
        regex(
            _URL_START_BOUNDARY
            + r"((([a-zA-Z]+)://)?localhost(:(\d+))?(/[^?\s#]*)?(\?[^\s#]+)?)"
            + _LOCAL_URL_END_BOUNDARY
        ),
    ),
    prod=_prod_localhost,
)

_LOCAL_URL_RULE = Rule(
    name="local url",
    pattern=(
        regex(
            _URL_START_BOUNDARY
            + r"(([a-zA-Z]+)://([\w_-]+)(:(\d+))?(/[^?\s#]*)?(\?[^\s#]+)?)"
            + _LOCAL_URL_END_BOUNDARY
        ),
    ),
    prod=_prod_local_url,
)


RULES: tuple[Rule, ...] = (_URL_RULE, _LOCALHOST_RULE, _LOCAL_URL_RULE)
