import argparse
import json
import logging
import os
from pathlib import Path

from .instance import instance_dir_get
from .server import DEFAULT__HOST, DEFAULT__PORT, start

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--listen-host", default=DEFAULT__HOST)
parser.add_argument("--listen-port", type=int, default=DEFAULT__PORT)
parser.add_argument("--log-file", action="store_true", default=False)
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
    if args.log_file:
        log_file_path = str(Path(instance_dir_get()) / "exporter.log")
        logger.info("logging to %r", log_file_path)
        handler = logging.FileHandler(log_file_path)
        handler.setFormatter(logging.Formatter(format))
        logging.root.addHandler(handler)


def main() -> None:
    args = parser.parse_args()
    logging_config(args)
    logger.info("starting")
    username = os.environ.get("SURFBOARD_USERNAME")
    password = os.environ["SURFBOARD_PASSWORD"]
    modem_host = os.environ.get("SURFBOARD_MODEM_HOST")
    modem_certificate_verify = json.loads(
        os.environ.get("SURFBOARD_MODEM_CERTIFICATE_VERIFY", "null")
    )
    modem_certificate_path = os.environ.get("SURFBOARD_MODEM_CERTIFICATE_PATH")
    _, thread = start(
        host=args.listen_host,
        port=args.listen_port,
        username=username,
        password=password,
        modem_host=modem_host,
        modem_certificate_verify=modem_certificate_verify,
        modem_certificate_path=modem_certificate_path,
        response_save=args.response_save,
    )
    thread.join()
