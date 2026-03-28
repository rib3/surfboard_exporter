import base64

import httpx

from client import _client_create, connection_status_get, token_get


def test_token_get(respx_mock):
    auth = base64.b64encode(b"admin:password").decode()
    respx_mock.get(f"https://192.168.100.1/cmconnectionstatus.html?login_{auth}").mock(
        return_value=httpx.Response(200, text="abc123token")
    )
    client = _client_create()

    result = token_get(client, "admin", "password")

    assert result == "abc123token"


def test_token_get_cached(respx_mock):
    auth = base64.b64encode(b"admin:password").decode()
    respx_mock.get(f"https://192.168.100.1/cmconnectionstatus.html?login_{auth}").mock(
        return_value=httpx.Response(
            200, text="abc123token", headers={"Set-Cookie": "sessionId=sess1"}
        )
    )
    client = _client_create()

    token_get(client, "admin", "password")
    token_get(client, "admin", "password")

    assert respx_mock.calls.call_count == 1


def test_connection_status_get(respx_mock):
    auth = base64.b64encode(b"admin:password").decode()
    respx_mock.get(f"https://192.168.100.1/cmconnectionstatus.html?login_{auth}").mock(
        return_value=httpx.Response(200, text="abc123token")
    )
    respx_mock.get("https://192.168.100.1/cmconnectionstatus.html?ct_abc123token").mock(
        return_value=httpx.Response(200, text="<html>status</html>")
    )

    result = connection_status_get("admin", "password")

    assert result == "<html>status</html>"
