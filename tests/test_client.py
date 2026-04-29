import logging
import os
import re
from http import HTTPStatus

import httpx
import pytest
import time_machine
from re_assert import Matches

from surfboard_exporter.client import (
    SurfboardClient,
    TokenUnavailableError,
    _response_save,
)


def test__response_save(tmp_path, monkeypatch, faker):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    frozen_dt = faker.date_time_utc()
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


@pytest.mark.parametrize(
    ("client_kwargs", "expected_username"),
    [
        ({}, "admin"),
        ({"username": "user"}, "user"),
    ],
)
def test__token_get(surfboard_api_mock_get_login, client_kwargs, expected_username):
    surfboard_api_mock_get_login(
        username=expected_username, password="password", token="abc123token"
    )
    client = SurfboardClient(password="password", **client_kwargs)

    result = client.token_get()

    assert result == "abc123token"


def test__init__username__empty():
    with pytest.raises(
        ValueError, match="^username='' is not valid, pass a real value, or None$"
    ):
        SurfboardClient(username="", password="password")


def test__init__modem_host__empty():
    with pytest.raises(
        ValueError, match="^modem_host='' is not valid, pass a real value, or None$"
    ):
        SurfboardClient(password="password", modem_host="")


def test__init__modem_certificate_path__does_not_exist(tmp_path):
    missing = str(tmp_path / "missing.crt")
    expected = f"modem_certificate_path={missing!r} does not exist"

    with pytest.raises(FileNotFoundError, match=f"^{re.escape(expected)}$"):
        SurfboardClient(password="password", modem_certificate_path=missing)


def test__token_get__cached(caplog, faker, httpx_mock, surfboard_api_mock_get_login):
    caplog.set_level(logging.DEBUG, logger="surfboard_exporter.client")
    token = faker.surfboard_token()
    surfboard_api_mock_get_login(password="password", token=token)
    client = SurfboardClient(password="password")

    client.token_get()

    assert len(httpx_mock.get_requests()) == 1
    expected_cached_log_tuple = (
        "surfboard_exporter.client",
        logging.DEBUG,
        f"using cached token={token!r}",
    )
    assert expected_cached_log_tuple not in caplog.record_tuples

    client.token_get()

    assert len(httpx_mock.get_requests()) == 1
    assert expected_cached_log_tuple in caplog.record_tuples


@pytest.mark.parametrize("session_id", [None, ""])
def test__token_get__no_session_id(caplog, session_id, surfboard_api_mock_get_login):
    caplog.set_level(logging.DEBUG, logger="surfboard_exporter.client")
    surfboard_api_mock_get_login(password="password", session_id=session_id)
    client = SurfboardClient(password="password")

    with pytest.raises(TokenUnavailableError):
        client.token_get()

    expected_log_tuple = (
        "surfboard_exporter.client",
        logging.DEBUG,
        f"no session_id ({session_id!r}) after request, not using token",
    )
    assert expected_log_tuple in caplog.record_tuples


def test__token_get__session_cleared__refetches(
    caplog,
    faker,
    surfboard_api_mock_get_connectionstatus,
    surfboard_api_mock_get_login,
):
    caplog.set_level(logging.DEBUG, logger="surfboard_exporter.client")
    client = SurfboardClient(password="password")

    token1 = faker.surfboard_token()
    surfboard_api_mock_get_login(password="password", token=token1)

    first = client.token_get()

    assert first == token1

    surfboard_api_mock_get_connectionstatus(token=token1, session_id="")

    client.connection_status_get()

    token2 = faker.surfboard_token()
    surfboard_api_mock_get_login(password="password", token=token2)

    second = client.token_get()

    assert second == token2
    expected_log_tuple = (
        "surfboard_exporter.client",
        logging.DEBUG,
        "no existing session_id (''), ensuring no cached token",
    )
    assert expected_log_tuple in caplog.record_tuples


def test__token_get__network_error(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        password="password",
        side_effect=httpx.ConnectError("connection refused"),
    )
    client = SurfboardClient(password="password")

    with pytest.raises(TokenUnavailableError):
        client.token_get()


def test__connection_status_get(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text)
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result == text


def test__connection_status_get__modem_certificate_verify__true(
    surfboard_api_mock_get_login, caplog
):
    ssl_error = httpx.ConnectError("SSL verification failed")
    surfboard_api_mock_get_login(
        password="password",
        side_effect=ssl_error,
    )
    client = SurfboardClient(password="password", modem_certificate_verify=True)

    result = client.connection_status_get()

    assert result is None
    expected_log_tuple_ssl = (
        "surfboard_exporter.client",
        logging.ERROR,
        Matches(f"ssl problem:.*{ssl_error}"),
    )
    assert expected_log_tuple_ssl in caplog.record_tuples


def test__connection_status_get__modem_certificate_verify__false(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text)
    client = SurfboardClient(password="password", modem_certificate_verify=False)

    result = client.connection_status_get()

    assert result == text


def test__connection_status_get__modem_certificate_path(
    https_server_modem,
    https_server_modem_expect_ordered_request_login_get,
    https_server_modem_expect_ordered_request_connectionstatus_get,
):
    session_id, token = https_server_modem_expect_ordered_request_login_get(
        username="admin", password="password"
    )
    _, status_html = https_server_modem_expect_ordered_request_connectionstatus_get(
        token=token, session_id=session_id
    )
    client = SurfboardClient(
        password="password",
        modem_host=https_server_modem.host,
        modem_certificate_verify=True,
        modem_certificate_path=https_server_modem.cert_path,
    )

    result = client.connection_status_get()

    assert result == status_html


@pytest.mark.parametrize("client_kwargs", [{}, {"modem_certificate_verify": True}])
def test__connection_status_get__modem_certificate_path__none__ssl_fails(
    https_server_modem, caplog, client_kwargs
):
    client = SurfboardClient(
        password="password",
        modem_host=https_server_modem.host,
        **client_kwargs,
    )

    result = client.connection_status_get()

    assert result is None
    expected_log_tuple_ssl = (
        "surfboard_exporter.client",
        logging.ERROR,
        Matches("ssl problem:.*CERTIFICATE_VERIFY_FAILED.*EE certificate key too weak"),
    )
    assert expected_log_tuple_ssl in caplog.record_tuples


def test__connection_status_get__modem_certificate_path__wrong_cert__ssl_fails(
    https_server_modem, key_cert_like_modem, caplog
):
    _, wrong_cert_path = key_cert_like_modem()
    client = SurfboardClient(
        password="password",
        modem_host=https_server_modem.host,
        modem_certificate_verify=True,
        modem_certificate_path=wrong_cert_path,
    )

    result = client.connection_status_get()

    assert result is None
    expected_log_tuple_ssl = (
        "surfboard_exporter.client",
        logging.ERROR,
        Matches("ssl problem:.*CERTIFICATE_VERIFY_FAILED.*self-signed certificate"),
    )
    assert expected_log_tuple_ssl in caplog.record_tuples
    expected_log_tuple = (
        "surfboard_exporter.client",
        logging.WARNING,
        "can't get status, token unavailable",
    )
    assert expected_log_tuple in caplog.record_tuples


def test__connection_status_get__response_save(
    tmp_path,
    monkeypatch,
    faker,
    surfboard_api_mock_get_login,
    surfboard_api_mock_get_connectionstatus,
):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    frozen_dt = faker.date_time_utc()
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text)
    client = SurfboardClient(password="password")

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
        password="password",
        side_effect=httpx.ConnectError("connection refused"),
    )
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__token_get__fails(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(
        password="password", status_code=HTTPStatus.UNAUTHORIZED
    )
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__token_get__no_session_id(surfboard_api_mock_get_login):
    surfboard_api_mock_get_login(password="password", session_id=None)
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__non_200(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(password="password", token=token)
    surfboard_api_mock_get_connectionstatus(
        token=token, status_code=HTTPStatus.UNAUTHORIZED
    )
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__network_error(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(password="password", token=token)
    surfboard_api_mock_get_connectionstatus(
        token=token, side_effect=httpx.ConnectError("connection refused")
    )
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__no_session_after_status(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, session_id="")
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result is None


def test__connection_status_get__no_session_cookie_after_status(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    text = "<html>status</html>"
    surfboard_api_mock_get_login(password="password", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=text, session_id=None)
    client = SurfboardClient(password="password")

    result = client.connection_status_get()

    assert result == text
