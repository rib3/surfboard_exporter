from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from testsupport.raises import pytest_raises_match_exact, repr_trunc_pydantic

_INT = TypeAdapter(int)


def _pydantic_input_value(value: object) -> str:
    try:
        _INT.validate_python(value)
    except ValidationError as error:
        rendered = str(error)
        after_value = rendered.split("input_value=", 1)[1]
        return after_value.split(", input_type=", 1)[0]
    raise RuntimeError(f"expected ValidationError for {value!r}")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("", "''"),
        ("abc", "'abc'"),
        (
            "012345678901234567890123456789012345678901234567",
            "'012345678901234567890123456789012345678901234567'",
        ),
        (
            "0123456789012345678901234567890123456789012345678",
            "'012345678901234567890123...67890123456789012345678'",
        ),
        (
            "01234567890123456789012345678901234567890123456789",
            "'012345678901234567890123...78901234567890123456789'",
        ),
    ],
)
def test__repr_trunc_pydantic(value, expected):
    result = repr_trunc_pydantic(value)

    assert result == expected


@pytest.mark.parametrize("length", [0, 1, 2, 3, 47, 48, 49, 50, 51, 52, 53, 90])
def test__repr_trunc_pydantic__matches_pydantic(length):
    value = "A" * length

    result = repr_trunc_pydantic(value)

    expected = _pydantic_input_value(value)
    assert result == expected


@pytest.mark.parametrize("value", [Path("/some/path"), Path("/" + "x" * 60), 12345])
def test__repr_trunc_pydantic__non_str(value):
    expected = repr_trunc_pydantic(str(value))

    result = repr_trunc_pydantic(value)

    assert result == expected


def test__pytest_raises_match_exact__anchored():
    substring = "needle"

    with pytest.raises(AssertionError):
        with pytest_raises_match_exact(ValueError, substring):
            raise ValueError(f"a {substring} in text")


def test__pytest_raises_match_exact__escaped():
    message = "a+b"

    with pytest_raises_match_exact(ValueError, message):
        raise ValueError(message)
