import re

import pytest


def _div_ceil(a: int, b: int) -> int:
    return (a + b - 1) // b


def repr_trunc_pydantic(value: object) -> str:
    # mirrors pydantic_core's truncate_safe_repr (pydantic-core/src/tools.rs)
    # https://github.com/pydantic/pydantic/blob/b58e339b1dd89f96dc2f26df764512f6293197c6/pydantic-core/src/tools.rs#L132-L139
    text = repr(str(value))
    max_len = 50
    if len(text) <= max_len:
        return text
    # pydantic quirk (faithful, not a bug): truncation always yields
    # mid + 3 + (mid - 1) = 52 chars, so inputs only just over max_len
    # come out the same length or even longer.
    mid = _div_ceil(max_len, 2)
    return f"{text[:mid]}...{text[-(mid - 1) :]}"


def pytest_raises_match_exact(
    exception: type[BaseException], message: str
) -> pytest.RaisesExc:
    return pytest.raises(exception, match=f"^{re.escape(message)}$")
