import logging

from prometheus_client import REGISTRY, start_http_server

from .collector import SurfboardCollector

logger = logging.getLogger(__name__)

DEFAULT__PORT = 9779


def start(
    *,
    port: int = DEFAULT__PORT,
    username: str | None = None,
    password: str,
    modem_host: str | None = None,
    modem_certificate_verify: bool | None = None,
    modem_certificate_path: str | None = None,
    response_save: bool = False,
):
    logger.info("port=%r", port)
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
    server, thread = start_http_server(port)
    logger.info(
        "listening at http://%s:%d/metrics", server.server_name, server.server_port
    )
    return server, thread
