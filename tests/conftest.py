import base64
from http import HTTPStatus
from typing import Callable

import httpx
import pytest
from mimesis.locales import Locale
from mimesis.schema import Field

import client
from client import _TOKEN_CACHE

UNDEFINED = object()

# mimesis pytest plugin BEGIN
# removed in mimesis 0.19????
# https://github.com/lk-geimfari/mimesis/issues/1670#issuecomment-3421030253
# https://github.com/lk-geimfari/mimesis/commit/2d11f31501bbf9ca69c8c6aa233285f737e2509e
# https://github.com/lk-geimfari/mimesis/pull/1660

try:
    import pytest
except ImportError:
    raise ImportError("pytest is required to use this plugin")

_CacheCallable = Callable[[Locale], Field]


@pytest.fixture(scope="session")
def _mimesis_cache() -> _CacheCallable:
    cached_instances: dict[Locale, Field] = {}

    def factory(locale: Locale) -> Field:
        if locale not in cached_instances:
            cached_instances[locale] = Field(locale)
        return cached_instances[locale]

    return factory


@pytest.fixture()
def mimesis_locale() -> Locale:
    """Specifies which locale to use."""
    return Locale.DEFAULT


@pytest.fixture()
def mimesis(_mimesis_cache: _CacheCallable, mimesis_locale: Locale) -> Field:
    """Mimesis fixture to provide fake data using all built-in providers."""
    return _mimesis_cache(mimesis_locale)


# mimesis pytest plugin END


@pytest.fixture(autouse=True)
def clear_token_cache():
    _TOKEN_CACHE.clear()


@pytest.fixture(autouse=True)
def html_save_dir_reset():
    client._HTML_SAVE_DIR = None


@pytest.fixture
def surfboard_api_mock_get_login(respx_mock, mimesis):
    def _mock(
        *,
        username,
        password,
        status_code=HTTPStatus.OK,
        token=UNDEFINED,
        session_id=UNDEFINED,
        return_value=UNDEFINED,
        side_effect=None,
    ):
        if token is UNDEFINED:
            token = mimesis("token_hex")
        if session_id is UNDEFINED:
            session_id = mimesis("token_hex")
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        if session_id is not None:
            headers = {"Set-Cookie": f"sessionId={session_id}"}
        else:
            headers = None
        if return_value is UNDEFINED:
            if side_effect is not None:
                return_value = None
            else:
                return_value = httpx.Response(status_code, text=token, headers=headers)
        return respx_mock.get(
            f"https://192.168.100.1/cmconnectionstatus.html?login_{auth}"
        ).mock(return_value=return_value, side_effect=side_effect)

    return _mock


@pytest.fixture
def surfboard_api_mock_get_connectionstatus(respx_mock, mimesis):
    def _mock(
        *,
        token,
        status_code=HTTPStatus.OK,
        text=UNDEFINED,
        return_value=UNDEFINED,
        side_effect=None,
    ):
        if text is UNDEFINED:
            text = mimesis("token_hex")
        if return_value is UNDEFINED:
            if side_effect is not None:
                return_value = None
            else:
                return_value = httpx.Response(status_code, text=text)
        return respx_mock.get(
            f"https://192.168.100.1/cmconnectionstatus.html?ct_{token}"
        ).mock(return_value=return_value, side_effect=side_effect)

    return _mock
