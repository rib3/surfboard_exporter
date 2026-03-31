import os
import re
from http import HTTPStatus

import httpx
import time_machine
from re_assert import Matches

from client import (
    _client_create,
    _html_save_dir_get_or_create,
    connection_status_get,
    connection_status_save,
    token_get,
)


def test_html_save_dir_get_or_create(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))

    result = _html_save_dir_get_or_create()

    expected = Matches(
        rf"{re.escape(str(tmp_path))}/surfboard_exporter\.{os.getpid()}\."
    )
    assert result == expected
    assert os.path.isdir(result)
    dirs = list(tmp_path.iterdir())
    dir = dirs[0]
    assert dir.name == Matches(rf"surfboard_exporter\.{os.getpid()}\.")
    assert str(dir) == expected


def test_html_save_dir_get_or_create_once(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))

    result1 = _html_save_dir_get_or_create()
    result2 = _html_save_dir_get_or_create()

    assert result1 == result2
    dirs = list(tmp_path.iterdir())
    dirs[0]
    assert not dirs[1:]


def test_connection_status_save(tmp_path, monkeypatch, mimesis):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    frozen_dt = mimesis("datetime", timezone="UTC")
    content = b"<html>status</html>"
    response = httpx.Response(HTTPStatus.OK, content=content)

    with time_machine.travel(frozen_dt, tick=False):
        connection_status_save(response)

    dirs = list(tmp_path.iterdir())
    save_dir = dirs[0]
    assert save_dir.name == Matches(rf"surfboard_exporter\.{os.getpid()}\.")
    assert not dirs[1:]
    files = list(save_dir.iterdir())
    file = files[0]
    expected_filename = Matches(
        rf"surfboard_exporter\.{re.escape(str(frozen_dt.timestamp()))}\.cmconnectionstatus\..*\.html"
    )
    assert file.name == expected_filename
    assert file.read_bytes() == content
    assert not files[1:]


def test_token_get(surfboard_api_mock_get_login):
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
    surfboard_api_mock_get_connectionstatus(
        token=token, status_code=HTTPStatus.UNAUTHORIZED
    )

    result = connection_status_get("admin", "password")

    assert result is None
