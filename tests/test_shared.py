from collections.abc import Iterable
from typing import Any


def _obj_as_dict(obj: Any, attrs: Iterable[str]) -> dict[str, Any]:
    d = {attr: getattr(obj, attr) for attr in attrs}
    return d


def assert_attrs(obj: Any, **expected_attrs: Any) -> None:
    actual = _obj_as_dict(obj, expected_attrs)
    assert actual == expected_attrs


def assert_attrs_list(
    objs: Iterable[Any], *expected_attrs_list: dict[str, Any]
) -> None:
    objs = list(objs)
    expected_attrs_list = list(expected_attrs_list)
    actual_list = [
        _obj_as_dict(obj, expected_attrs)
        for obj, expected_attrs in zip(objs, expected_attrs_list, strict=False)
    ]
    actual_list.extend(objs[len(expected_attrs_list) :])
    assert actual_list == expected_attrs_list
