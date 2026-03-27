import base64
import logging

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


@cachetools.cached(
    cachetools.TTLCache(maxsize=128, ttl=30),
    key=lambda client, username, password: (id(client), username, password),
)
def login(client: httpx.Client, username: str, password: str) -> str:
    logger.info("cookies (before)=%r", dict(client.cookies))
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    response = client.get(
        f"cmconnectionstatus.html?login_{auth}",
        headers={"Authorization": f"Basic {auth}"},
    )
    logger.info("response=%r, response.text=%r", response, response.text)
    response.raise_for_status()
    logger.info("cookies=%r", dict(client.cookies))
    return response.text


def connection_status_get(username: str, password: str) -> str:
    client = _client_get_or_create()
    token = login(client, username, password)
    logger.info("cookies (before)=%r", dict(client.cookies))
    response = client.get(f"cmconnectionstatus.html?ct_{token}")
    logger.info("response=%r", response)
    logger.info("cookies=%r", dict(client.cookies))
    response.raise_for_status()
    return response.text
