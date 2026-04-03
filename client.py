import base64
import logging
import os
import tempfile
from datetime import datetime
from http import HTTPStatus

import cachetools
import httpx

logger = logging.getLogger(__name__)

_HTML_SAVE_DIR: str | None = None
_CLIENT: httpx.Client | None = None
_TOKEN_CACHE: cachetools.TTLCache = cachetools.TTLCache(maxsize=128, ttl=30)


class TokenUnavailable(Exception):
    pass


def _html_save_dir_get_or_create() -> str:
    global _HTML_SAVE_DIR
    if _HTML_SAVE_DIR is None:
        prefix = f"surfboard_exporter.{os.getpid()}."
        _HTML_SAVE_DIR = tempfile.mkdtemp(prefix=prefix)
    return _HTML_SAVE_DIR


def connection_status_save(response: httpx.Response) -> None:
    epoch = datetime.now().timestamp()
    prefix = f"surfboard_exporter.{epoch}.cmconnectionstatus."
    dir = _html_save_dir_get_or_create()
    with tempfile.NamedTemporaryFile(
        prefix=prefix, suffix=".html", delete=False, dir=dir
    ) as f:
        logger.info("writing to %r", f.name)
        f.write(response.content)


def _client_create() -> httpx.Client:
    return httpx.Client(base_url="https://192.168.100.1", verify=False)


def _client_get_or_create() -> httpx.Client:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = _client_create()
    return _CLIENT


def _session_id_from_client(client: httpx.Client) -> str | None:
    return client.cookies.get("sessionId")


def token_get(client: httpx.Client, username: str, password: str) -> str:
    session_id = _session_id_from_client(client)
    if session_id:
        token = _TOKEN_CACHE.get(session_id)
        logger.debug("token (cached)=%r", token)
        if token:
            return token

    logger.info("cookies (before)=%r", dict(client.cookies))
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    try:
        response = client.get(
            f"cmconnectionstatus.html?login_{auth}",
            headers={"Authorization": f"Basic {auth}"},
        )
        logger.info("response=%r, response.text=%r", response, response.text)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise TokenUnavailable() from e
    logger.info("cookies=%r", dict(client.cookies))
    token = response.text
    logger.debug("token=%r", token)
    session_id = _session_id_from_client(client)
    if session_id:
        _TOKEN_CACHE[session_id] = token
    return token


def connection_status_get(username: str, password: str, html_save=False) -> str | None:
    client = _client_get_or_create()
    try:
        token = token_get(client, username, password)
    except TokenUnavailable:
        logger.warning("can't get status, token unavailable", exc_info=True)
        return None

    logger.info("cookies (before)=%r", dict(client.cookies))
    try:
        response = client.get(f"cmconnectionstatus.html?ct_{token}")
    except httpx.HTTPError:
        logger.warning("connection status request failed", exc_info=True)
        return None
    logger.info("response=%r", response)
    if html_save:
        connection_status_save(response)

    if response.status_code != HTTPStatus.OK:
        logger.warning(
            "response.status_code=%r != %r", response.status_code, HTTPStatus.OK
        )
        return None

    logger.info("cookies=%r", dict(client.cookies))
    session_id = _session_id_from_client(client)
    if not session_id:
        logger.warning("session_id=%r empty after request", session_id)
        return None

    return response.text
