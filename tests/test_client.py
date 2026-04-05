import os
import re
from http import HTTPStatus
from pathlib import Path

import httpx
import pytest
import time_machine
from re_assert import Matches

from client import (
    SurfboardClient,
    TokenUnavailableError,
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
    assert Path(result).is_dir()
    dirs = list(tmp_path.iterdir())
    assert dirs[0].name == Matches(rf"surfboard_exporter\.{os.getpid()}\.")
    assert str(dirs[0]) == expected


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


def test__token_get__cached(httpx_mock, surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(username="admin", password="password")
    client = SurfboardClient("admin", "password")

    client.token_get()
    client.token_get()

    assert len(httpx_mock.get_requests()) == 1


def test__token_get__no_session_id(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(username="admin", password="password", session_id=None)
    client = SurfboardClient("admin", "password")

    with pytest.raises(TokenUnavailableError):
        client.token_get()


def test__token_get__network_error(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        username="admin",
        password="password",
        side_effect=httpx.ConnectError("connection refused"),
    )
    client = SurfboardClient("admin", "password")

    with pytest.raises(TokenUnavailableError):
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


def test__connection_status_get__response_save(
    tmp_path,
    monkeypatch,
    mimesis,
    surfboard_api_mock_get_login,
    surfboard_api_mock_get_connectionstatus,
):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    frozen_dt = mimesis("datetime", timezone="UTC")
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text)
    client = SurfboardClient("admin", "password")

    with time_machine.travel(frozen_dt, tick=False):
        result = client.connection_status_get(response_save=True)

    assert result == text
    dirs = list(tmp_path.iterdir())
    expected_dir_name = Matches(rf"surfboard_exporter\.{os.getpid()}\.")
    assert dirs[0].name == expected_dir_name
    files = list(dirs[0].iterdir())
    expected_file_name = Matches(
        rf"{re.escape(str(frozen_dt.timestamp()))}\.cmconnectionstatus\.html\..*"
    )
    assert files[0].name == expected_file_name
    assert files[0].read_bytes() == text.encode()
    assert not files[1:]
    assert not dirs[1:]


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


def test__connection_status_get__no_session_after_status(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, session_id="")
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__no_session_cookie_after_status(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(username="admin", password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text, session_id=None)
    client = SurfboardClient("admin", "password")

    result = client.connection_status_get()

    assert result == text
