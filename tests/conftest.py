import pytest

from client import login


@pytest.fixture(autouse=True)
def clear_login_cache():
    login.cache.clear()
