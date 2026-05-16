import logging
from pathlib import Path

from prometheus_client import REGISTRY, start_http_server

from .collector import SurfboardCollector
from .settings import DEFAULT__HOST, DEFAULT__PORT

logger = logging.getLogger(__name__)


def start(
    *,
    host: str = DEFAULT__HOST,
    port: int = DEFAULT__PORT,
    username: str | None = None,
    password: str,
    modem_host: str | None = None,
    modem_certificate_verify: bool | None = None,
    modem_certificate_path: Path | None = None,
    response_save: bool = False,
):
    logger.info("host=%r port=%r", host, port)
    REGISTRY.register(
        SurfboardCollector(
            username=username,
            password=password,
            modem_host=modem_host,
            modem_certificate_verify=modem_certificate_verify,
            modem_certificate_path=modem_certificate_path,
            response_save=response_save,
        )
    )
    server, thread = start_http_server(port, addr=host)
    logger.info("listening at http://%s:%d/metrics", host, server.server_port)
    return server, thread
