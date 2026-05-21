import logging

from prometheus_client import start_http_server

from .settings import DEFAULT__HOST, DEFAULT__PORT

logger = logging.getLogger(__name__)


def start(*, host: str = DEFAULT__HOST, port: int = DEFAULT__PORT):
    logger.info("host=%r port=%r", host, port)
    server, thread = start_http_server(port, addr=host)
    logger.info("listening at http://%s:%d/metrics", host, server.server_port)
    return server, thread
