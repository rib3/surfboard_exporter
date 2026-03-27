import time
import logging

from prometheus_client import Counter, Gauge, start_http_server

from parser import parse_downstream_channels, parse_system_time, parse_upstream_channels

logger = logging.getLogger(__name__)

CM_STATUS_HTML = "cmconnectionstatus.html"

SYSTEM_TIME = Gauge("surfboard_system_time", "System time (Unix timestamp)")

DS_FREQUENCY = Gauge(
    "surfboard_downstream_frequency_hz",
    "Downstream channel frequency (Hz)",
    ["channel_id"],
)
DS_POWER = Gauge(
    "surfboard_downstream_power_dbmv", "Downstream power (dBmV)", ["channel_id"]
)
DS_SNR = Gauge("surfboard_downstream_snr_db", "Downstream SNR/MER (dB)", ["channel_id"])
DS_CORRECTED = Counter(
    "surfboard_downstream_corrected", "Downstream corrected codewords", ["channel_id"]
)
DS_UNCORRECTABLES = Counter(
    "surfboard_downstream_uncorrectables",
    "Downstream uncorrectable codewords",
    ["channel_id"],
)


US_FREQUENCY = Gauge(
    "surfboard_upstream_frequency_hz", "Upstream channel frequency (Hz)", ["channel_id"]
)
US_WIDTH = Gauge(
    "surfboard_upstream_width_hz", "Upstream channel width (Hz)", ["channel_id"]
)
US_POWER = Gauge(
    "surfboard_upstream_power_dbmv", "Upstream power (dBmV)", ["channel_id"]
)

_prev_corrected: dict[str, int] = {}
_prev_uncorrectables: dict[str, int] = {}


def scrape() -> None:
    logger.info("scrape start")

    with open(CM_STATUS_HTML, encoding="windows-1252") as f:
        html = f.read()

    SYSTEM_TIME.set(parse_system_time(html))

    for ch in parse_upstream_channels(html):
        labels = {"channel_id": str(ch.channel_id)}
        US_FREQUENCY.labels(**labels).set(ch.frequency_hz)
        US_WIDTH.labels(**labels).set(ch.width_hz)
        US_POWER.labels(**labels).set(ch.power_dbmv)

    for ch in parse_downstream_channels(html):
        labels = {"channel_id": str(ch.channel_id)}
        cid = str(ch.channel_id)
        DS_FREQUENCY.labels(**labels).set(ch.frequency_hz)
        DS_POWER.labels(**labels).set(ch.power_dbmv)
        DS_SNR.labels(**labels).set(ch.snr_db)
        DS_CORRECTED.labels(**labels).inc(
            ch.corrected - _prev_corrected.get(cid, ch.corrected)
        )
        DS_UNCORRECTABLES.labels(**labels).inc(
            ch.uncorrectables - _prev_uncorrectables.get(cid, ch.uncorrectables)
        )
        _prev_corrected[cid] = ch.corrected
        _prev_uncorrectables[cid] = ch.uncorrectables

    logger.info("scrape end")


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
    start_http_server(8000)
    while True:
        scrape()
        time.sleep(30)


if __name__ == "__main__":
    main()
