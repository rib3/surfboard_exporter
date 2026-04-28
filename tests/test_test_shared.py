from types import SimpleNamespace

import pytest

from .test_shared import assert_attrs_list


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

    assert "namespace(a=2, b='y')" in str(exc_info.value)


def test__assert_attrs_list__objs_shorter__shows_unmatched_expected_in_diff():
    items = [SimpleNamespace(a=1, b="x")]

    with pytest.raises(AssertionError) as exc_info:
        assert_attrs_list(items, dict(a=1, b="x"), dict(a=2, b="y"))

    assert "{'a': 2, 'b': 'y'}" in str(exc_info.value)
