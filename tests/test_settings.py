import logging

import pytest
from pydantic import ValidationError

from surfboard_exporter.settings import Settings

from .test_shared import assert_attrs

logger = logging.getLogger(__name__)


def test__settings__defaults(monkeypatch):
    password = "secret"
    monkeypatch.setenv("SURFBOARD_PASSWORD", password)

    settings = Settings(_cli_parse_args=[])

    assert_attrs(
        settings,
        username="admin",
        modem_host="192.168.100.1",
        modem_certificate_verify=True,
        modem_certificate_path=None,
        listen_host="0.0.0.0",
        listen_port=9779,
        log_file=False,
        response_save=False,
        verbose=False,
    )
    assert settings.password.get_secret_value() == password


def test__settings__password__missing():
    with pytest.raises(ValidationError, match="SURFBOARD_PASSWORD"):
        Settings(_cli_parse_args=[])


def test__settings__password_file(caplog, monkeypatch, tmp_path):
    password = "from-file"
    password_file = tmp_path / "password"
    password_file.write_text(f"{password}\n")
    monkeypatch.setenv("SURFBOARD_PASSWORD_FILE", str(password_file))

    settings = Settings(_cli_parse_args=[])

    assert settings.password.get_secret_value() == password
    expected_log_tuple = (
        "surfboard_exporter.settings",
        logging.INFO,
        f"loading password from {str(password_file)!r}",
    )
    assert expected_log_tuple in caplog.record_tuples


def test__settings__password_file__overrides_password(monkeypatch, tmp_path):
    password = "from-file"
    password_file = tmp_path / "password"
    password_file.write_text(password)
    monkeypatch.setenv("SURFBOARD_PASSWORD", "from-env")
    monkeypatch.setenv("SURFBOARD_PASSWORD_FILE", str(password_file))

    settings = Settings(_cli_parse_args=[])

    assert settings.password.get_secret_value() == password


def test__settings__modem_certificate_verify__false(monkeypatch):
    monkeypatch.setenv("SURFBOARD_PASSWORD", "x")
    monkeypatch.setenv("SURFBOARD_MODEM_CERTIFICATE_VERIFY", "false")

    settings = Settings(_cli_parse_args=[])

    assert settings.modem_certificate_verify is False


def test__settings__cli__listen_port(monkeypatch):
    monkeypatch.setenv("SURFBOARD_PASSWORD", "x")
    listen_port = 5555

    settings = Settings(_cli_parse_args=["--listen-port", str(listen_port)])

    assert settings.listen_port == listen_port


def test__settings__cli__listen_port__overrides_env(monkeypatch):
    monkeypatch.setenv("SURFBOARD_PASSWORD", "x")
    monkeypatch.setenv("SURFBOARD_LISTEN_PORT", "1234")
    listen_port = 5555

    settings = Settings(_cli_parse_args=["--listen-port", str(listen_port)])

    assert settings.listen_port == listen_port


def test__settings__cli__verbose__short(monkeypatch):
    monkeypatch.setenv("SURFBOARD_PASSWORD", "x")

    settings = Settings(_cli_parse_args=["-v"])

    assert settings.verbose is True


def test__settings__cli__log_file(monkeypatch):
    monkeypatch.setenv("SURFBOARD_PASSWORD", "x")

    settings = Settings(_cli_parse_args=["--log-file"])

    assert settings.log_file is True
