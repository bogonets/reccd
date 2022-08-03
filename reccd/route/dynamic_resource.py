# -*- coding: utf-8 -*-

from re import Pattern
from re import compile as re_compile
from re import error as re_error
from re import escape as re_escape
from typing import Dict, Final, Optional, Tuple

from yarl import URL
from yarl import __version__ as yarl_version  # type: ignore[attr-defined]

YARL_VERSION: Final[Tuple[int, ...]] = tuple(map(int, yarl_version.split(".")[:2]))


def quote_path(value: str) -> str:
    if YARL_VERSION < (1, 6):
        value = value.replace("%", "%25")
    return URL.build(path=value, encoded=False).raw_path


def unquote_path(value: str) -> str:
    return URL.build(path=value, encoded=True).path


def requote_path(value: str) -> str:
    # Quote non-ascii characters and other characters which must be quoted,
    # but preserve existing %-sequences.
    result = quote_path(value)
    if "%" in value:
        result = result.replace("%25", "%")
    return result


ROUTE_PATTERN: Final[str] = r"(\{[_a-zA-Z][^{}]*(?:\{[^{}]*\}[^{}]*)*\})"
ROUTE_RE: Final[Pattern[str]] = re_compile(ROUTE_PATTERN)

PATH_SEP: Final[str] = re_escape("/")

DYN_PATTERN: Final[str] = r"\{(?P<var>[_a-zA-Z][_a-zA-Z0-9]*)\}"
DYN_RE: Final[Pattern[str]] = re_compile(DYN_PATTERN)

DYN_WITH_PATTERN: Final[str] = r"\{(?P<var>[_a-zA-Z][_a-zA-Z0-9]*):(?P<re>.+)\}"
DYN_WITH_RE: Final[Pattern[str]] = re_compile(DYN_WITH_PATTERN)

GOOD: Final[str] = r"[^{}/]+"


class DynamicResource:
    def __init__(self, path: str) -> None:
        pattern = ""
        formatter = ""
        for part in ROUTE_RE.split(path):
            match = DYN_RE.fullmatch(part)
            if match:
                pattern += "(?P<{}>{})".format(match.group("var"), GOOD)
                formatter += "{" + match.group("var") + "}"
                continue

            match = DYN_WITH_RE.fullmatch(part)
            if match:
                pattern += "(?P<{var}>{re})".format(**match.groupdict())
                formatter += "{" + match.group("var") + "}"
                continue

            if "{" in part or "}" in part:
                raise ValueError(f"Invalid path '{path}'['{part}']")

            part = requote_path(part)
            formatter += part
            pattern += re_escape(part)

        try:
            compiled = re_compile(pattern)
        except re_error as exc:
            raise ValueError(f"Bad pattern '{pattern}': {exc}") from None

        assert compiled.pattern.startswith(PATH_SEP)
        assert formatter.startswith("/")
        self._pattern = compiled
        self._formatter = formatter

    def match(self, path: str) -> Optional[Dict[str, str]]:
        match = self._pattern.fullmatch(path)
        if match is None:
            return None
        return {key: unquote_path(value) for key, value in match.groupdict().items()}
