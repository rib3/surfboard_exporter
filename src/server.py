import logging

from prometheus_client import REGISTRY, start_http_server

from collector import SurfboardCollector

logger = logging.getLogger(__name__)


def start(
    *,
    username: str | None = None,
    password: str,
    modem_host: str | None = None,
    modem_certificate_verify: bool | None = None,
    modem_certificate_path: str | None = None,
    response_save: bool = False,
):
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
    return start_http_server(8000)
