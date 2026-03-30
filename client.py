import base64
import logging
from http import HTTPStatus

import cachetools
import httpx

logger = logging.getLogger(__name__)

_client: httpx.Client | None = None


def _client_create() -> httpx.Client:
    return httpx.Client(base_url="https://192.168.100.1", verify=False)


def _client_get_or_create() -> httpx.Client:
    global _client
    if _client is None:
        _client = _client_create()
    return _client


_token_cache: cachetools.TTLCache = cachetools.TTLCache(maxsize=128, ttl=30)


def _session_id_from_client(client: httpx.Client) -> str | None:
    return client.cookies.get("sessionId")


def token_get(client: httpx.Client, username: str, password: str) -> str:
    session_id = _session_id_from_client(client)
    if session_id:
        token = _token_cache.get(session_id)
        logger.debug("token (cached)=%r", token)
        if token:
            return token

    logger.info("cookies (before)=%r", dict(client.cookies))
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    response = client.get(
        f"cmconnectionstatus.html?login_{auth}",
        headers={"Authorization": f"Basic {auth}"},
    )
    logger.info("response=%r, response.text=%r", response, response.text)
    response.raise_for_status()
    logger.info("cookies=%r", dict(client.cookies))
    token = response.text
    logger.debug("token=%r", token)
    session_id = _session_id_from_client(client)
    if session_id:
        _token_cache[session_id] = token
    return token


def connection_status_get(username: str, password: str) -> str | None:
    client = _client_get_or_create()
    token = token_get(client, username, password)
    logger.info("cookies (before)=%r", dict(client.cookies))
    response = client.get(f"cmconnectionstatus.html?ct_{token}")
    logger.info("response=%r", response)
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
