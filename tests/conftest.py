import base64
import enum
import logging
import os
import ssl
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from faker import Faker
from polyfactory import Use
from polyfactory.decorators import post_generated
from polyfactory.factories.base import BaseFactory
from polyfactory.factories.dataclass_factory import DataclassFactory
from polyfactory.pytest_plugin import register_fixture
from pytest_httpserver import HTTPServer
from pytest_httpx import HTTPXMock

from surfboard_exporter.files import instance_dir_get
from surfboard_exporter.settings import Settings
from testsupport.faker_with_providers import FakerWithProviders
from testsupport.modem_html import (
    ConnectionStatus,
    DownstreamBondedChannels,
    DownstreamBondedChannelsRow,
    StartupProcedure,
    UpstreamBondedChannels,
    UpstreamBondedChannelsRow,
)
from testsupport.surfboard_provider import SurfboardProvider

logger = logging.getLogger(__name__)


class _Unspecified(enum.Enum):
    UNSPECIFIED = enum.auto()


UNSPECIFIED = _Unspecified.UNSPECIFIED


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "only: run only this test (dev-only, do not commit)"
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    focused = [i for i in items if i.get_closest_marker("only")]
    if focused:
        config.hook.pytest_deselected(items=[i for i in items if i not in focused])
        items[:] = focused
        terminal = config.pluginmanager.getplugin("terminalreporter")
        if isinstance(terminal, pytest.TerminalReporter):
            terminal.write_sep(
                "!", f"only mode: {len(focused)} test(s) selected", red=True, bold=True
            )


def pytest_make_parametrize_id(val: object) -> str | None:
    if isinstance(val, ConnectionStatus):
        return val.testdata_id
    return None  # defer to pytest


@pytest.fixture(autouse=True)
def _env_surfboard_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("SURFBOARD_"):
            monkeypatch.delenv(key)


@pytest.fixture(autouse=True)
def _env_clear_tmpdir(monkeypatch: pytest.MonkeyPatch) -> None:
    # env vars taken from `tempfile._candidate_tempdir_list`
    # https://github.com/python/cpython/blob/e56ae817e5f3df37a603251641ada5bf182af152/Lib/tempfile.py#L164
    for key in ("TMPDIR", "TEMP", "TMP"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(autouse=True)
def _chdir_tmp_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    # avoid project-root .env leaking in (pydantic-settings reads relative to cwd)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def dotenv_file(_chdir_tmp_path: Path) -> Path:
    dotenv_file = _chdir_tmp_path / ".env"
    assert dotenv_file.name == Settings.model_config.get("env_file")
    return dotenv_file


@pytest.fixture
def cli_args_set(monkeypatch: pytest.MonkeyPatch):
    def _set(args: list[str]) -> None:
        # argv[0] is the program name; pydantic-settings parses argv[1:]
        monkeypatch.setattr(sys, "argv", ["surfboard_exporter", *args])

    return _set


@pytest.fixture(autouse=True)
def _sys_argv_patch(cli_args_set: Callable[[list[str]], None]) -> None:
    # avoid pytest's own argv leaking into pydantic-settings' CLI parser
    cli_args_set([])


@pytest.fixture
def env_surfboard_password(
    _env_surfboard_clear: None,  # guarantee it runs before our setenv
    faker: FakerWithProviders,
    monkeypatch: pytest.MonkeyPatch,
) -> str:
    password = faker.password()
    monkeypatch.setenv("SURFBOARD_PASSWORD", password)
    return password


@pytest.fixture
def secrets_dir(faker: FakerWithProviders, tmp_path: Path) -> Path:
    path = tmp_path / f"secrets.{faker.word()}"
    path.mkdir()
    return path


@pytest.fixture
def env_surfboard_secrets_dir(
    _env_surfboard_clear: None,  # guarantee it runs before our setenv
    monkeypatch: pytest.MonkeyPatch,
    secrets_dir: Path,
) -> Path:
    monkeypatch.setenv("SURFBOARD_SECRETS_DIR", str(secrets_dir))
    return secrets_dir


class UseFaker(Use):
    def __init__(self, method_name: str, *args, **kwargs) -> None:
        super().__init__(
            lambda: getattr(BaseFactory.__faker__, method_name)(*args, **kwargs)
        )


@pytest.fixture(scope="session")
def _session_faker(_session_faker: Faker) -> Faker:
    _session_faker.add_provider(SurfboardProvider)
    BaseFactory.__faker__.add_provider(SurfboardProvider)
    return _session_faker


@pytest.fixture(autouse=True)
def instance_dir_get__cache_clear() -> None:
    instance_dir_get.cache_clear()


@pytest.fixture
def surfboard_api_mock_get_login(httpx_mock: HTTPXMock, faker: FakerWithProviders):
    def _mock(
        *,
        username: str = "admin",
        password: str,
        status_code: HTTPStatus = HTTPStatus.OK,
        session_id: str | None | _Unspecified = UNSPECIFIED,
        token: str | _Unspecified = UNSPECIFIED,
        side_effect: Exception | None = None,
    ) -> None:
        if session_id is UNSPECIFIED:
            session_id = faker.surfboard_session_id()
        if token is UNSPECIFIED:
            token = faker.surfboard_token()
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        url = f"https://192.168.100.1/cmconnectionstatus.html?login_{auth}"
        if side_effect is not None:
            httpx_mock.add_exception(side_effect, url=url)
        else:
            if session_id is not None:
                headers = {"Set-Cookie": f"sessionId={session_id}"}
            else:
                headers = None
            httpx_mock.add_response(
                url=url, status_code=status_code, headers=headers, text=token
            )

    return _mock


@pytest.fixture
def surfboard_api_mock_get_connectionstatus(
    httpx_mock: HTTPXMock, faker: FakerWithProviders
):
    def _mock(
        *,
        token: str,
        status_code: HTTPStatus = HTTPStatus.OK,
        session_id: str | None | _Unspecified = UNSPECIFIED,
        text: str | _Unspecified = UNSPECIFIED,
        side_effect: Exception | None = None,
    ) -> None:
        if session_id is UNSPECIFIED:
            session_id = faker.surfboard_session_id()
        if session_id is not None:
            headers = {"Set-Cookie": f"sessionId={session_id}"}
        else:
            headers = None
        if text is UNSPECIFIED:
            text = faker.text()
        url = f"https://192.168.100.1/cmconnectionstatus.html?ct_{token}"
        if side_effect is not None:
            httpx_mock.add_exception(side_effect, url=url)
        else:
            httpx_mock.add_response(
                url=url, status_code=status_code, headers=headers, text=text
            )

    return _mock


@pytest.fixture
def key_cert_like_modem(tmp_path: Path):
    def _make() -> tuple[Path, Path]:
        # generate a modem-like cert: 1024-bit RSA, CA:FALSE, self-signed
        key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        prefix = "modem-"
        key_file = NamedTemporaryFile(
            prefix=prefix, suffix=".key", dir=tmp_path, delete=False
        )
        key_file.write(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
        name = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, "localhost.localdomain")]
        )
        now = datetime.now(UTC)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=1))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .sign(key, hashes.SHA256())
        )
        cert_file = NamedTemporaryFile(
            prefix=prefix, suffix=".crt", dir=tmp_path, delete=False
        )
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
        return Path(key_file.name), Path(cert_file.name)

    return _make


@dataclass
class HttpServerModem:
    server: HTTPServer
    cert_path: Path
    host: str


@pytest.fixture
def https_server_modem(key_cert_like_modem) -> Iterator[HttpServerModem]:
    key_path, cert_path = key_cert_like_modem()
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ssl_ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    logger.debug("https_server_modem starting")
    with HTTPServer(host="127.0.0.1", ssl_context=ssl_ctx) as server:
        host = f"{server.host}:{server.port}"
        logger.info("https_server_modem started host=%r", host)
        yield HttpServerModem(server=server, cert_path=cert_path, host=host)
        assert not server.ordered_handlers, (
            f"unfulfilled ordered requests: {server.ordered_handlers}"
        )
        server.check()
        logger.info("https_server_modem stopping host=%r", host)


@pytest.fixture
def https_server_modem_expect_ordered_request_login_get(
    https_server_modem: HttpServerModem, faker: FakerWithProviders
):
    def _expect(
        *,
        username: str,
        password: str,
        session_id: str | None | _Unspecified = UNSPECIFIED,
        token: str | _Unspecified = UNSPECIFIED,
    ) -> tuple[str | None, str]:
        if session_id is UNSPECIFIED:
            session_id = faker.surfboard_session_id()
        if token is UNSPECIFIED:
            token = faker.surfboard_token()
        auth = base64.b64encode(f"{username}:{password}".encode()).decode()
        if session_id is not None:
            headers = {"Set-Cookie": f"sessionId={session_id}"}
        else:
            headers = None
        https_server_modem.server.expect_ordered_request(
            "/cmconnectionstatus.html",
            query_string=f"login_{auth}",
        ).respond_with_data(token, headers=headers)
        return session_id, token

    return _expect


@pytest.fixture
def https_server_modem_expect_ordered_request_connectionstatus_get(
    https_server_modem: HttpServerModem, faker: FakerWithProviders
):
    def _expect(
        *,
        token: str,
        status_code: HTTPStatus = HTTPStatus.OK,
        session_id: str | None | _Unspecified = UNSPECIFIED,
        text: str | _Unspecified = UNSPECIFIED,
    ) -> tuple[str | None, str]:
        if session_id is UNSPECIFIED:
            session_id = faker.surfboard_session_id()
        if session_id is not None:
            headers = {"Set-Cookie": f"sessionId={session_id}"}
        else:
            headers = None
        if text is UNSPECIFIED:
            text = faker.text()
        https_server_modem.server.expect_ordered_request(
            "/cmconnectionstatus.html",
            query_string=f"ct_{token}",
        ).respond_with_data(text, status=status_code, headers=headers)
        return session_id, text

    return _expect


@register_fixture
class StartupProcedureFactory(DataclassFactory):
    __model__ = StartupProcedure
    connectivity_state = UseFaker("surfboard_connectivity_state")
    connectivity_state_comment = UseFaker("surfboard_connectivity_state_comment")
    security = UseFaker("surfboard_security")
    security_comment = UseFaker("surfboard_security_comment")
    docsis_network_access_enabled = UseFaker("surfboard_docsis_network_access_enabled")
    docsis_network_access_enabled_comment = UseFaker(
        "surfboard_docsis_network_access_enabled_comment"
    )


@register_fixture
class DownstreamBondedChannelsRowFactory(DataclassFactory):
    __model__ = DownstreamBondedChannelsRow
    channel_id = UseFaker("surfboard_downstream_channel_id")
    lock_status = UseFaker("surfboard_downstream_lock_status")
    modulation = UseFaker("surfboard_downstream_modulation")
    frequency_hz = UseFaker("surfboard_downstream_frequency_hz")
    power_dbmv = UseFaker("surfboard_downstream_power_dbmv")
    snr_db = UseFaker("surfboard_downstream_snr_db")
    corrected = UseFaker("surfboard_downstream_corrected")
    uncorrectables = UseFaker("surfboard_downstream_uncorrectables")


@register_fixture
class DownstreamBondedChannelsFactory(DataclassFactory):
    __model__ = DownstreamBondedChannels

    @post_generated
    @classmethod
    def rows(cls) -> list[DownstreamBondedChannelsRow]:
        count = cls.__random__.choice([0, 24, 25])
        return DownstreamBondedChannelsRowFactory.batch(count)


@register_fixture
class UpstreamBondedChannelsRowFactory(DataclassFactory):
    __model__ = UpstreamBondedChannelsRow
    channel = UseFaker("surfboard_upstream_channel")
    channel_id = UseFaker("surfboard_upstream_channel_id")
    lock_status = UseFaker("surfboard_upstream_lock_status")
    channel_type = UseFaker("surfboard_upstream_channel_type")
    frequency_hz = UseFaker("surfboard_upstream_frequency_hz")
    width_hz = UseFaker("surfboard_upstream_width_hz")
    power_dbmv = UseFaker("surfboard_upstream_power_dbmv")


@register_fixture
class UpstreamBondedChannelsFactory(DataclassFactory):
    __model__ = UpstreamBondedChannels
    __min_collection_length__ = 0
    __max_collection_length__ = 4


@register_fixture
class ConnectionStatusFactory(DataclassFactory):
    __model__ = ConnectionStatus
    system_time_str = None
    # real-capture stem (testdata/<id>.html); factory should generate None
    testdata_id = None

    @post_generated
    @classmethod
    def system_time(cls, system_time_str):
        if system_time_str is None:
            provider = cls.get_provider_map()[datetime]
            return provider()
        return None
        # return Null
