import logging
import os

from server import start

logger = logging.getLogger(__name__)


def logging_config() -> None:
    format = ":".join(
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
    logging.basicConfig(level=logging.DEBUG, format=format)


def main() -> None:
    logging_config()
    logger.info("starting")
    username = os.environ.get("SURFBOARD_USERNAME", "admin")
    password = os.environ["SURFBOARD_PASSWORD"]
    _, thread = start(username, password)
    thread.join()


if __name__ == "__main__":
    main()
