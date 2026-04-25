"""URL corpus — locale-agnostic. Ported from `Duckling/Url/Corpus.hs`."""

from __future__ import annotations

from puckling.corpus import Example, examples


def _v(value: str, domain: str) -> dict:
    return {"value": value, "domain": domain, "type": "value"}


CORPUS: tuple[Example, ...] = (
    examples(_v("http://www.bla.com", "bla.com"), ["http://www.bla.com"]),
    examples(_v("www.bla.com:8080/path", "bla.com"), ["www.bla.com:8080/path"]),
    examples(_v("https://myserver?foo=bar", "myserver"), ["https://myserver?foo=bar"]),
    examples(_v("cnn.com/info", "cnn.com"), ["cnn.com/info"]),
    examples(
        _v("bla.com/path/path?ext=%23&foo=bla", "bla.com"),
        ["bla.com/path/path?ext=%23&foo=bla"],
    ),
    examples(_v("localhost", "localhost"), ["localhost"]),
    examples(_v("localhost:8000", "localhost"), ["localhost:8000"]),
    examples(_v("http://kimchi", "kimchi"), ["http://kimchi"]),
    examples(_v("https://500px.com:443/about", "500px.com"), ["https://500px.com:443/about"]),
    examples(_v("www2.foo-bar.net?foo=bar", "foo-bar.net"), ["www2.foo-bar.net?foo=bar"]),
    examples(
        _v("https://api.wit.ai/message?q=hi", "api.wit.ai"),
        ["https://api.wit.ai/message?q=hi"],
    ),
    examples(_v("aMaZon.co.uk/?page=home", "amazon.co.uk"), ["aMaZon.co.uk/?page=home"]),
    examples(
        _v(
            "https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#Syntax",
            "en.wikipedia.org",
        ),
        ["https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#Syntax"],
    ),
    examples(
        _v("http://example.com/data.csv#cell=4,1-6,2", "example.com"),
        ["http://example.com/data.csv#cell=4,1-6,2"],
    ),
    examples(
        _v(
            "http://example.com/bar.webm#t=40,80&xywh=160,120,320,240",
            "example.com",
        ),
        ["http://example.com/bar.webm#t=40,80&xywh=160,120,320,240"],
    ),
)


NEGATIVE_CORPUS: tuple[str, ...] = ("foo", "MYHOST", "hey:42", "25")
