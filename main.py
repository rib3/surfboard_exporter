import argparse
import json
import logging
import os

from server import start

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--response-save", action="store_true", default=False)
parser.add_argument("-v", "--verbose", action="store_true", default=False)


def logging_config(args) -> None:
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
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format=format)


def main() -> None:
    args = parser.parse_args()
    logging_config(args)
    logger.info("starting")
    username = os.environ.get("SURFBOARD_USERNAME", "admin")
    password = os.environ["SURFBOARD_PASSWORD"]
    modem_host = os.environ.get("SURFBOARD_MODEM_HOST", "192.168.100.1")
    modem_certificate_verify = json.loads(
        os.environ.get("SURFBOARD_MODEM_CERTIFICATE_VERIFY", "true")
    )
    modem_certificate_path = os.environ.get("SURFBOARD_MODEM_CERTIFICATE_PATH") or None
    _, thread = start(
        username,
        password,
        modem_host=modem_host,
        modem_certificate_verify=modem_certificate_verify,
        modem_certificate_path=modem_certificate_path,
        response_save=args.response_save,
    )
    thread.join()


if __name__ == "__main__":
    main()
