import base64
import logging
import pathlib
import ssl
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from mimesis.locales import Locale
from mimesis.schema import Field

from client import _response_save_dir_get

logger = logging.getLogger(__name__)

UNSPECIFIED = object()

# mimesis pytest plugin BEGIN
# removed in mimesis 0.19????
# https://github.com/lk-geimfari/mimesis/issues/1670#issuecomment-3421030253
# https://github.com/lk-geimfari/mimesis/commit/2d11f31501bbf9ca69c8c6aa233285f737e2509e
# https://github.com/lk-geimfari/mimesis/pull/1660

try:
    import pytest
except ImportError as e:
    raise ImportError("pytest is required to use this plugin") from e

_CacheCallable = Callable[[Locale], Field]


@pytest.fixture(scope="session")
def _mimesis_cache() -> _CacheCallable:
    cached_instances: dict[Locale, Field] = {}

    def factory(locale: Locale) -> Field:
        if locale not in cached_instances:
            cached_instances[locale] = Field(locale)
        return cached_instances[locale]

    return factory


@pytest.fixture
def mimesis_locale() -> Locale:
    """Specifies which locale to use."""
    return Locale.DEFAULT


@pytest.fixture
def mimesis(_mimesis_cache: _CacheCallable, mimesis_locale: Locale) -> Field:
    """Mimesis fixture to provide fake data using all built-in providers."""
    return _mimesis_cache(mimesis_locale)


# mimesis pytest plugin END


@pytest.fixture(autouse=True)
def response_save_dir_get__cache_clear():
    _response_save_dir_get.cache_clear()


@pytest.fixture
def surfboard_api_mock_get_login(httpx_mock, mimesis):
    def _mock(
        *,
        username,
        password,
        status_code=HTTPStatus.OK,
        session_id=UNSPECIFIED,
        token=UNSPECIFIED,
        side_effect=None,
    ):
        if session_id is UNSPECIFIED:
            session_id = mimesis("token_hex")
        if token is UNSPECIFIED:
            token = mimesis("token_hex")
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
def surfboard_api_mock_get_connectionstatus(httpx_mock, mimesis):
    def _mock(
        *,
        token,
        status_code=HTTPStatus.OK,
        session_id=UNSPECIFIED,
        text=UNSPECIFIED,
        side_effect=None,
    ):
        if session_id is UNSPECIFIED:
            session_id = mimesis("token_hex")
        if session_id is not None:
            headers = {"Set-Cookie": f"sessionId={session_id}"}
        else:
            headers = None
        if text is UNSPECIFIED:
            text = mimesis("token_hex")
        url = f"https://192.168.100.1/cmconnectionstatus.html?ct_{token}"
        if side_effect is not None:
            httpx_mock.add_exception(side_effect, url=url)
        else:
            httpx_mock.add_response(
                url=url, status_code=status_code, headers=headers, text=text
            )

    return _mock


_MODEM_SERVER_TOKEN = "modem_server_token"
_MODEM_SERVER_SESSION_ID = "modem_server_session"
_MODEM_SERVER_HTML = "<html>modem server status</html>"


class _RequestHandlerModem(BaseHTTPRequestHandler):
    def do_GET(self):
        if "login_" in self.path:
            body = _MODEM_SERVER_TOKEN.encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Set-Cookie", f"sessionId={_MODEM_SERVER_SESSION_ID}")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif f"ct_{_MODEM_SERVER_TOKEN}" in self.path:
            body = _MODEM_SERVER_HTML.encode()
            self.send_response(HTTPStatus.OK)
            self.send_header("Set-Cookie", f"sessionId={_MODEM_SERVER_SESSION_ID}")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()


@dataclass
class ModemLikeServer:
    host: str
    cert_path: pathlib.Path
    html: str


@pytest.fixture
def modem_like_cert(tmp_path):
    _counter = [0]

    def _make():
        # generate a modem-like cert: 1024-bit RSA, CA:FALSE, self-signed
        _counter[0] += 1
        key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
        name = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, "localhost.localdomain")]
        )
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC))
            .not_valid_after(datetime.now(UTC) + timedelta(days=1))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True
            )
            .sign(key, hashes.SHA256())
        )
        cert_path = tmp_path / f"modem_{_counter[0]}.crt"
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        key_path = tmp_path / f"modem_{_counter[0]}.key"
        key_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
        return cert_path, key_path

    return _make


@pytest.fixture
def modem_like_server(modem_like_cert):
    cert_path, key_path = modem_like_cert()

    server_ip = "127.0.0.1"
    server = HTTPServer((server_ip, 0), _RequestHandlerModem)
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ssl_ctx.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    server.socket = ssl_ctx.wrap_socket(server.socket, server_side=True)

    host = f"{server_ip}:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    logger.info("modem_like_server starting host=%r", host)
    thread.start()

    yield ModemLikeServer(host=host, cert_path=cert_path, html=_MODEM_SERVER_HTML)

    server.shutdown()
    logger.info("modem_like_server shutdown host=%r", host)
