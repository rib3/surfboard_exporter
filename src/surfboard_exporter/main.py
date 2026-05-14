import logging
from pathlib import Path

from .instance import instance_dir_get
from .server import start
from .settings import Settings

logger = logging.getLogger(__name__)

LOG_FORMAT = ":".join(
    [
        "%(created)s",
        # "%(asctime)s",
        "%(process)d",
        "%(thread)d",
        "%(threadName)s",
        # "%(taskName)s",
        "%(name)s",
        "%(levelname)s",
        "%(module)s",
        "%(funcName)s",
        "%(message)s",
    ]
)


def logging_init() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def logging_config(settings: Settings) -> None:
    level = logging.DEBUG if settings.verbose else logging.INFO
    logging.root.setLevel(level)
    if settings.log_file:
        log_file_path = str(Path(instance_dir_get()) / "exporter.log")
        logger.info("logging to %r", log_file_path)
        handler = logging.FileHandler(log_file_path)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.root.addHandler(handler)


def main() -> None:
    logging_init()
    settings = Settings()
    logging_config(settings)
    logger.info("starting")
    _, thread = start(
        host=settings.listen_host,
        port=settings.listen_port,
        username=settings.username,
        password=settings.password.get_secret_value(),
        modem_host=settings.modem_host,
        modem_certificate_verify=settings.modem_certificate_verify,
        modem_certificate_path=settings.modem_certificate_path,
        response_save=settings.response_save,
    )
    thread.join()
