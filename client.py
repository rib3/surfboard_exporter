import base64
import logging
import os
import tempfile
from datetime import datetime
from http import HTTPStatus

import cachetools
import httpx

logger = logging.getLogger(__name__)

_RESPONSE_SAVE_DIR: str | None = None


class TokenUnavailable(Exception):
    pass


def _response_save_dir_get_or_create() -> str:
    global _RESPONSE_SAVE_DIR
    if _RESPONSE_SAVE_DIR is None:
        prefix = f"surfboard_exporter.{os.getpid()}."
        _RESPONSE_SAVE_DIR = tempfile.mkdtemp(prefix=prefix)
    return _RESPONSE_SAVE_DIR


def _response_save(response: httpx.Response) -> None:
    epoch = datetime.now().timestamp()
    path = response.request.url.path.lstrip("/")
    prefix = f"{epoch}.{path}."
    dir = _response_save_dir_get_or_create()
    with tempfile.NamedTemporaryFile(prefix=prefix, delete=False, dir=dir) as f:
        logger.info("writing to %r", f.name)
        f.write(response.content)


class SurfboardClient:
    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._client = httpx.Client(base_url="https://192.168.100.1", verify=False)
        self._token_cache: cachetools.TTLCache = cachetools.TTLCache(
            maxsize=128, ttl=30
        )

    def _session_id(self) -> str | None:
        return self._client.cookies.get("sessionId")

    def token_get(self) -> str:
        session_id = self._session_id()
        if session_id:
            token = self._token_cache.get(session_id)
            logger.debug("token (cached)=%r", token)
            if token:
                return token

        logger.info("cookies (before)=%r", dict(self._client.cookies))
        auth = base64.b64encode(f"{self._username}:{self._password}".encode()).decode()
        try:
            response = self._client.get(
                f"cmconnectionstatus.html?login_{auth}",
                headers={"Authorization": f"Basic {auth}"},
            )
            logger.info("response=%r, response.text=%r", response, response.text)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise TokenUnavailable() from e
        logger.info("cookies=%r", dict(self._client.cookies))
        token = response.text
        logger.debug("token=%r", token)
        session_id = self._session_id()
        if session_id:
            self._token_cache[session_id] = token
        return token

    def connection_status_get(self, response_save: bool = False) -> str | None:
        try:
            token = self.token_get()
        except TokenUnavailable:
            logger.warning("can't get status, token unavailable", exc_info=True)
            return None

        logger.info("cookies (before)=%r", dict(self._client.cookies))
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

        logger.info("cookies=%r", dict(self._client.cookies))
        session_id = self._session_id()
        if not session_id:
            logger.warning("session_id=%r empty after request", session_id)
            return None

        return response.text
