from client import _client_create, connection_status_get, token_get


def test_token_get(respx_mock, surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        username="admin", password="password", token="abc123token"
    )
    client = _client_create()

    result = token_get(client, "admin", "password")

    assert result == "abc123token"


def test_token_get_cached(respx_mock, surfboard_api_mock_get_login):
    login_mock = surfboard_api_mock_get_login(username="admin", password="password")
    client = _client_create()

    token_get(client, "admin", "password")
    token_get(client, "admin", "password")

    assert login_mock.call_count == 1
    assert respx_mock.calls.call_count == 1


def test_connection_status_get(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text)

    result = connection_status_get("admin", "password")

    assert result == text


def test_connection_status_get_non_200(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, status_code=401)

    result = connection_status_get("admin", "password")

    assert result is None
