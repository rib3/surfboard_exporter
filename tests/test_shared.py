def assert_attrs(obj, **expected_attrs):
    actual = {attr: getattr(obj, attr) for attr in expected_attrs}
    assert actual == expected_attrs
