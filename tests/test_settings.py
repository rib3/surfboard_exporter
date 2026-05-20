import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from surfboard_exporter.settings import Settings

from .test_shared import assert_attrs

logger = logging.getLogger(__name__)

PASSWORD_CONFLICT_MESSAGE = "set password or password_file, not both"


def test__settings__defaults(env_surfboard_password):
    settings = Settings(_cli_parse_args=[])

    assert_attrs(
        settings,
        username="admin",
        modem_host="192.168.100.1",
        modem_certificate_verify=True,
        modem_certificate_file=None,
        listen_host="0.0.0.0",
        listen_port=9779,
        log_file=False,
        response_save=False,
        tmpdir=None,
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


def test__settings__password_file__password(monkeypatch, tmp_path):
    password_file = tmp_path / "password"
    password_file.write_text("from-file")
    monkeypatch.setenv("SURFBOARD_PASSWORD", "from-env")
    monkeypatch.setenv("SURFBOARD_PASSWORD_FILE", str(password_file))

    with pytest.raises(ValidationError, match=PASSWORD_CONFLICT_MESSAGE):
        Settings(_cli_parse_args=[])


def test__settings__secrets_dir(caplog, env_surfboard_secrets_dir):
    password = "from-secrets-dir"
    (env_surfboard_secrets_dir / "SURFBOARD_PASSWORD").write_text(password)

    settings = Settings(_cli_parse_args=[])

    assert settings.password.get_secret_value() == password
    expected_log_tuple = (
        "surfboard_exporter.settings",
        logging.INFO,
        f"SURFBOARD_SECRETS_DIR={str(env_surfboard_secrets_dir)!r}",
    )
    assert expected_log_tuple in caplog.record_tuples


def test__settings__env__overrides_secrets_dir(env_surfboard_secrets_dir, monkeypatch):
    env_password = "from-env"
    secrets_dir_password = "from-secrets-dir"
    (env_surfboard_secrets_dir / "SURFBOARD_PASSWORD").write_text(secrets_dir_password)
    monkeypatch.setenv("SURFBOARD_PASSWORD", env_password)

    settings = Settings(_cli_parse_args=[])

    assert settings.password.get_secret_value() == env_password


def test__settings__password_file__secrets_dir__password(
    env_surfboard_secrets_dir, monkeypatch, tmp_path
):
    password_file = tmp_path / "password"
    password_file.write_text("from-password-file")
    (env_surfboard_secrets_dir / "SURFBOARD_PASSWORD").write_text("from-secrets-dir")
    monkeypatch.setenv("SURFBOARD_PASSWORD_FILE", str(password_file))

    with pytest.raises(ValidationError, match=PASSWORD_CONFLICT_MESSAGE):
        Settings(_cli_parse_args=[])


def test__settings__modem_certificate_verify__false(
    env_surfboard_password, monkeypatch
):
    monkeypatch.setenv("SURFBOARD_MODEM_CERTIFICATE_VERIFY", "false")

    settings = Settings(_cli_parse_args=[])

    assert settings.modem_certificate_verify is False


def test__settings__modem_certificate_file__exists(
    env_surfboard_password, monkeypatch, tmp_path
):
    cert_file = tmp_path / "cert.crt"
    cert_file.write_text("dummy")
    monkeypatch.setenv("SURFBOARD_MODEM_CERTIFICATE_FILE", str(cert_file))

    settings = Settings(_cli_parse_args=[])

    assert settings.modem_certificate_file == cert_file


def test__settings__modem_certificate_file__does_not_exist(
    env_surfboard_password, monkeypatch, tmp_path
):
    missing = tmp_path / "missing.crt"
    monkeypatch.setenv("SURFBOARD_MODEM_CERTIFICATE_FILE", str(missing))

    with pytest.raises(ValidationError, match="modem_certificate_file"):
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


def test__settings__tmpdir__expanduser(env_surfboard_password, monkeypatch):
    monkeypatch.setenv("TMPDIR", "~/tmp")

    settings = Settings(_cli_parse_args=[])

    expected_tmpdir = Path.home() / "tmp"
    assert settings.tmpdir == expected_tmpdir


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
