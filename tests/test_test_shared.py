import logging
import re
from types import SimpleNamespace

import pytest

from .test_shared import assert_attrs_list

logger = logging.getLogger(__name__)

# ANSI SGR: CSI (\x1b[), digit/semicolon params, final byte "m".
# Covers color, bold, and reset; not other CSI finals (cursor, erase).
_ANSI_SGR_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi_sgr(s: str) -> str:
    return _ANSI_SGR_RE.sub("", s)


def test__assert_attrs_list__empty():
    assert_attrs_list([])


def test__assert_attrs_list__match():
    items = [SimpleNamespace(a=1, b="x"), SimpleNamespace(a=2, b="y")]

    assert_attrs_list(items, dict(a=1, b="x"), dict(a=2, b="y"))


def test__assert_attrs_list__subset_attrs():
    items = [SimpleNamespace(a=1, b="x"), SimpleNamespace(a=2, b="y")]

    assert_attrs_list(items, dict(a=1), dict(b="y"))


def test__assert_attrs_list__attr_mismatch__raises():
    items = [SimpleNamespace(a=1, b="x")]

    with pytest.raises(AssertionError):
        assert_attrs_list(items, dict(a=2, b="x"))


def test__assert_attrs_list__objs_longer__shows_extra_obj_in_diff():
    items = [SimpleNamespace(a=1, b="x"), SimpleNamespace(a=2, b="y")]

    with pytest.raises(AssertionError) as exc_info:
        assert_attrs_list(items, dict(a=1, b="x"))

    msg = _strip_ansi_sgr(str(exc_info.value))
    logger.info("msg:\n%s\n-----\n%r", msg, msg)
    assert "namespace(a=2, b='y')" in msg


def test__assert_attrs_list__objs_shorter__shows_unmatched_expected_in_diff():
    items = [SimpleNamespace(a=1, b="x")]

    with pytest.raises(AssertionError) as exc_info:
        assert_attrs_list(items, dict(a=1, b="x"), dict(a=2, b="y"))

    msg = _strip_ansi_sgr(str(exc_info.value))
    logger.info("msg:\n%s\n-----\n%r", msg, msg)
    assert "{'a': 2, 'b': 'y'}" in msg
