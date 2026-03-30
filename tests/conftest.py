import base64

import httpx
import pytest

from client import _token_cache


@pytest.fixture(autouse=True)
def clear_token_cache():
    _token_cache.clear()


@pytest.fixture
def surfboard_api_mock_get_login(respx_mock):
    def _mock(username, password, *, status_code=200, token=None, session_id=None):
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        if session_id is not None:
            headers = {"Set-Cookie": f"sessionId={session_id}"}
        else:
            headers = None
        return respx_mock.get(
            f"https://192.168.100.1/cmconnectionstatus.html?login_{auth}"
        ).mock(return_value=httpx.Response(status_code, text=token, headers=headers))

    return _mock


@pytest.fixture
def surfboard_api_mock_get_connectionstatus(respx_mock):
    def _mock(*, token, status_code=200, text=None):
        return respx_mock.get(
            f"https://192.168.100.1/cmconnectionstatus.html?ct_{token}"
        ).mock(return_value=httpx.Response(status_code, text=text))

    return _mock
