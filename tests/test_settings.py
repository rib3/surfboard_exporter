import logging

import pytest
from pydantic import ValidationError

from surfboard_exporter.settings import Settings

from .test_shared import assert_attrs

logger = logging.getLogger(__name__)


def test__settings__defaults(env_surfboard_password):
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
    assert settings.password.get_secret_value() == env_surfboard_password


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


def test__settings__modem_certificate_verify__false(
    env_surfboard_password, monkeypatch
):
    monkeypatch.setenv("SURFBOARD_MODEM_CERTIFICATE_VERIFY", "false")

    settings = Settings(_cli_parse_args=[])

    assert settings.modem_certificate_verify is False


def test__settings__modem_certificate_path__exists(
    env_surfboard_password, monkeypatch, tmp_path
):
    cert_file = tmp_path / "cert.crt"
    cert_file.write_text("dummy")
    monkeypatch.setenv("SURFBOARD_MODEM_CERTIFICATE_PATH", str(cert_file))

    settings = Settings(_cli_parse_args=[])

    assert settings.modem_certificate_path == cert_file


def test__settings__modem_certificate_path__does_not_exist(
    env_surfboard_password, monkeypatch, tmp_path
):
    missing = tmp_path / "missing.crt"
    monkeypatch.setenv("SURFBOARD_MODEM_CERTIFICATE_PATH", str(missing))

    with pytest.raises(ValidationError, match="modem_certificate_path"):
        Settings(_cli_parse_args=[])


def test__settings__cli__listen_port(env_surfboard_password):
    listen_port = 5555

    settings = Settings(_cli_parse_args=["--listen-port", str(listen_port)])

    assert settings.listen_port == listen_port


def test__settings__cli__listen_port__overrides_env(
    env_surfboard_password, monkeypatch
):
    monkeypatch.setenv("SURFBOARD_LISTEN_PORT", "1234")
    listen_port = 5555

    settings = Settings(_cli_parse_args=["--listen-port", str(listen_port)])

    assert settings.listen_port == listen_port


def test__settings__cli__verbose__short(env_surfboard_password):
    settings = Settings(_cli_parse_args=["-v"])

    assert settings.verbose is True


def test__settings__cli__log_file(env_surfboard_password):
    settings = Settings(_cli_parse_args=["--log-file"])

    assert settings.log_file is True


def test__settings__env_file(tmp_path):
    password = "from-env-file"
    modem_host = "10.0.0.1"
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"SURFBOARD_PASSWORD={password}\nSURFBOARD_MODEM_HOST={modem_host}\n"
    )

    settings = Settings(_env_file=str(env_file), _cli_parse_args=[])

    assert settings.password.get_secret_value() == password
    assert settings.modem_host == modem_host


def test__settings__env_file__env_overrides(
    env_surfboard_password, monkeypatch, tmp_path
):
    modem_host = "10.0.0.2"
    monkeypatch.setenv("SURFBOARD_MODEM_HOST", modem_host)
    env_file = tmp_path / ".env"
    env_file.write_text("SURFBOARD_MODEM_HOST=from-file\n")

    settings = Settings(_env_file=str(env_file), _cli_parse_args=[])

    assert settings.modem_host == modem_host
