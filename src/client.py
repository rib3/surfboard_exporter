import base64
import functools
import logging
import os
import pathlib
import ssl
import tempfile
from datetime import datetime
from http import HTTPStatus

import httpx

logger = logging.getLogger(__name__)


class TokenUnavailableError(Exception):
    pass


@functools.cache
def _response_save_dir_get() -> str:
    prefix = f"surfboard_exporter.{os.getpid()}."
    return tempfile.mkdtemp(prefix=prefix)


def _response_save(response: httpx.Response) -> None:
    # time.time() (at least under time_machine) may have additional digits compared to
    # datetime.timestamp() used in tests
    # example: 1792793067.4058182 vs 1792793067.405818
    epoch = datetime.now().timestamp()
    path = response.request.url.path.lstrip("/")
    prefix = f"{epoch}.{path}."
    save_dir = _response_save_dir_get()
    with tempfile.NamedTemporaryFile(prefix=prefix, delete=False, dir=save_dir) as f:
        logger.info("writing to %r", f.name)
        f.write(response.content)


class SurfboardClient:
    def __init__(
        self,
        *,
        username: str | None = None,
        password: str,
        modem_host: str | None = None,
        modem_certificate_verify: bool | None = None,
        modem_certificate_path: str | None = None,
    ) -> None:
        if username is None:
            username = "admin"
        if not username:
            raise ValueError(
                f"username={username!r} is not valid, pass a real value, or None"
            )
        self._username = username
        self._password = password

        if modem_host is None:
            modem_host = "192.168.100.1"
        if not modem_host:
            raise ValueError(
                f"modem_host={modem_host!r} is not valid, pass a real value, or None"
            )
        base_url = f"https://{modem_host}"

        if modem_certificate_verify is None:
            modem_certificate_verify = True
        self.verify = self._verify_get(modem_certificate_verify, modem_certificate_path)
        self._client = httpx.Client(base_url=base_url, verify=self.verify)
        self._token: str | None = None

    def _verify_get(
        self, modem_certificate_verify: bool, modem_certificate_path: str | None
    ) -> bool | ssl.SSLContext:
        logger.info("modem_certificate_verify=%r", modem_certificate_verify)
        if not modem_certificate_verify:
            return False
        logger.info("modem_certificate_path=%r", modem_certificate_path)
        if modem_certificate_path:
            return self._ssl_context_get_modem(modem_certificate_path)
        return True

    def _ssl_context_get_modem(self, path: str) -> ssl.SSLContext:
        if not pathlib.Path(path).is_file():
            raise FileNotFoundError(f"modem_certificate_path={path!r} does not exist")
        # modem cert is self-signed, use a context with only the modem cert as CA
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.load_verify_locations(cafile=path)
        # modem cert has CA:FALSE
        # partial chain allows a non-CA cert in trust store to terminate the chain
        ssl_context.verify_flags |= ssl.VERIFY_X509_PARTIAL_CHAIN
        ssl_context.check_hostname = False  # work around CN=localhost.localdomain
        # lower seclevel to support weak modem cert key (1024-bit RSA)
        ssl_context.set_ciphers("DEFAULT@SECLEVEL=1")
        return ssl_context

    def _session_id(self) -> str | None:
        return self._client.cookies.get("sessionId")

    def token_get(self) -> str:
        session_id = self._session_id()
        if not session_id:
            logger.debug("no session_id, clearing token=%r", self._token)
            self._token = None
        if self._token:
            logger.debug("token (cached)=%r", self._token)
            return self._token

        logger.debug("cookies (before)=%r", dict(self._client.cookies))
        auth = base64.b64encode(f"{self._username}:{self._password}".encode()).decode()
        try:
            response = self._client.get(
                f"cmconnectionstatus.html?login_{auth}",
                headers={"Authorization": f"Basic {auth}"},
            )
            logger.info("response=%r", response)
            logger.debug("response.text=%r", response.text)
            response.raise_for_status()
        except httpx.HTTPError as e:
            if "SSL" in str(e):
                logger.error("ssl problem: %s", e)
            raise TokenUnavailableError from e
        logger.debug("cookies=%r", dict(self._client.cookies))
        token = response.text
        logger.debug("token=%r (self._token=%r)", token, self._token)
        session_id = self._session_id()
        if session_id:
            self._token = token
        else:
            self._token = None  # so next call refreshes
            raise TokenUnavailableError
        return self._token

    def connection_status_get(self, response_save: bool = False) -> str | None:
        try:
            token = self.token_get()
        except TokenUnavailableError:
            logger.warning("can't get status, token unavailable", exc_info=True)
            return None

        logger.debug("cookies (before)=%r", dict(self._client.cookies))
        try:
            response = self._client.get(f"cmconnectionstatus.html?ct_{token}")
        except httpx.HTTPError:
            logger.warning("connection status request failed", exc_info=True)
            return None
        logger.info("response=%r", response)
        if response_save:
            _response_save(response)

        if response.status_code != HTTPStatus.OK:
            logger.warning(
                "response.status_code=%r != %r", response.status_code, HTTPStatus.OK
            )
            return None

        logger.debug("cookies=%r", dict(self._client.cookies))
        session_id = self._session_id()
        if not session_id:
            logger.warning("session_id=%r empty after request", session_id)
            return None

        return response.text
