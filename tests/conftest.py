import base64
from collections.abc import Callable
from http import HTTPStatus

import pytest
from mimesis.locales import Locale
from mimesis.schema import Field

from client import _response_save_dir_get

UNDEFINED = object()

# mimesis pytest plugin BEGIN
# removed in mimesis 0.19????
# https://github.com/lk-geimfari/mimesis/issues/1670#issuecomment-3421030253
# https://github.com/lk-geimfari/mimesis/commit/2d11f31501bbf9ca69c8c6aa233285f737e2509e
# https://github.com/lk-geimfari/mimesis/pull/1660

try:
    import pytest
except ImportError as e:
    raise ImportError("pytest is required to use this plugin") from e

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
def response_save_dir_get__cache_clear():
    _response_save_dir_get.cache_clear()


@pytest.fixture
def surfboard_api_mock_get_login(httpx_mock, mimesis):
    def _mock(
        *,
        username,
        password,
        status_code=HTTPStatus.OK,
        session_id=UNDEFINED,
        token=UNDEFINED,
        side_effect=None,
    ):
        if session_id is UNDEFINED:
            session_id = mimesis("token_hex")
        if token is UNDEFINED:
            token = mimesis("token_hex")
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        url = f"https://192.168.100.1/cmconnectionstatus.html?login_{auth}"
        if side_effect is not None:
            httpx_mock.add_exception(side_effect, url=url)
        else:
            if session_id is not None:
                headers = {"Set-Cookie": f"sessionId={session_id}"}
            else:
                headers = None
            httpx_mock.add_response(
                url=url, status_code=status_code, headers=headers, text=token
            )

    return _mock


@pytest.fixture
def surfboard_api_mock_get_connectionstatus(httpx_mock, mimesis):
    def _mock(
        *,
        token,
        status_code=HTTPStatus.OK,
        session_id=UNDEFINED,
        text=UNDEFINED,
        side_effect=None,
    ):
        if session_id is UNDEFINED:
            session_id = mimesis("token_hex")
        if session_id is not None:
            headers = {"Set-Cookie": f"sessionId={session_id}"}
        else:
            headers = None
        if text is UNDEFINED:
            text = mimesis("token_hex")
        url = f"https://192.168.100.1/cmconnectionstatus.html?ct_{token}"
        if side_effect is not None:
            httpx_mock.add_exception(side_effect, url=url)
        else:
            httpx_mock.add_response(
                url=url, status_code=status_code, headers=headers, text=text
            )

    return _mock
