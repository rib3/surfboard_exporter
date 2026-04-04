import os
import re
from http import HTTPStatus

import httpx
import pytest
import time_machine
from re_assert import Matches

from client import (
    SurfboardClient,
    TokenUnavailable,
    _response_save,
    _response_save_dir_get,
)


def test__response_save_dir_get(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))

    result = _response_save_dir_get()

    expected = Matches(
        rf"{re.escape(str(tmp_path))}/surfboard_exporter\.{os.getpid()}\."
    )
    assert result == expected
    assert os.path.isdir(result)
    dirs = list(tmp_path.iterdir())
    dir = dirs[0]
    assert dir.name == Matches(rf"surfboard_exporter\.{os.getpid()}\.")
    assert str(dir) == expected


def test__response_save_dir_get__once(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))

    result1 = _response_save_dir_get()
    result2 = _response_save_dir_get()

    assert result1 == result2
    dirs = list(tmp_path.iterdir())
    dirs[0]
    assert not dirs[1:]


def test__response_save(tmp_path, monkeypatch, mimesis):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    frozen_dt = mimesis("datetime", timezone="UTC")
    content = b"<html>status</html>"
    request = httpx.Request(
        "GET", "https://192.168.100.1/cmconnectionstatus.html?ct_token"
    )
    response = httpx.Response(HTTPStatus.OK, content=content, request=request)

    with time_machine.travel(frozen_dt, tick=False):
        _response_save(response)

    dirs = list(tmp_path.iterdir())
    save_dir = dirs[0]
    assert save_dir.name == Matches(rf"surfboard_exporter\.{os.getpid()}\.")
    assert not dirs[1:]
    files = list(save_dir.iterdir())
    file = files[0]
    expected_filename = Matches(
        rf"{re.escape(str(frozen_dt.timestamp()))}\.cmconnectionstatus\.html\..*"
    )
    assert file.name == expected_filename
    assert file.read_bytes() == content
    assert not files[1:]


def test__token_get(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        username="admin", password="password", token="abc123token"
    )
    client = SurfboardClient("admin", "password")

    result = client.token_get()

    assert result == "abc123token"


def test__token_get__cached(respx_mock, surfboard_api_mock_get_login):
    login_mock = surfboard_api_mock_get_login(username="admin", password="password")
    client = SurfboardClient("admin", "password")

    client.token_get()
    client.token_get()

    assert login_mock.call_count == 1
    assert respx_mock.calls.call_count == 1


def test__token_get__no_session_id(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(username="admin", password="password", session_id=None)
    client = SurfboardClient("admin", "password")

    with pytest.raises(TokenUnavailable):
        client.token_get()


def test__token_get__network_error(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        username="admin",
        password="password",
        side_effect=httpx.ConnectError("connection refused"),
    )
    client = SurfboardClient("admin", "password")

    with pytest.raises(TokenUnavailable):
        client.token_get()


def test__connection_status_get(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text)
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result == text


def test__connection_status_get__token_network_error(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        username="admin",
        password="password",
        side_effect=httpx.ConnectError("connection refused"),
    )
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__token_get__fails(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        username="admin", password="password", status_code=HTTPStatus.UNAUTHORIZED
    )
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__token_get__no_session_id(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(username="admin", password="password", session_id=None)
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__non_200(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(
        token=token, status_code=HTTPStatus.UNAUTHORIZED
    )
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__network_error(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(
        token=token, side_effect=httpx.ConnectError("connection refused")
    )
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result is None
