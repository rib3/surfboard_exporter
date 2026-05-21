import logging

from prometheus_client import REGISTRY

from .collector import SurfboardCollector
from .files import tempfile_config
from .log import logging_config, logging_init
from .server import start
from .settings import Settings

logger = logging.getLogger(__name__)


def main() -> None:
    logging_init()
    settings = Settings()
    tempfile_config(settings)
    logging_config(settings)
    logger.info("starting")
    collector = collector_from_settings(settings)
    REGISTRY.register(collector)
    _, thread = start(
        host=settings.listen_host,
        port=settings.listen_port,
    )
    thread.join()


def collector_from_settings(settings: Settings) -> SurfboardCollector:
    return SurfboardCollector(
        username=settings.username,
        password=settings.password.get_secret_value(),
        modem_host=settings.modem_host,
        modem_certificate_verify=settings.modem_certificate_verify,
        modem_certificate_file=settings.modem_certificate_file,
        response_save=settings.response_save,
    )
