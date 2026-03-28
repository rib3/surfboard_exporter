import pytest

from client import _token_cache


@pytest.fixture(autouse=True)
def clear_token_cache():
    _token_cache.clear()
