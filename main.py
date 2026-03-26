import time
import logging

from prometheus_client import Counter, Gauge, start_http_server

from parser import parse_downstream_channels

logger = logging.getLogger(__name__)

CM_STATUS_HTML = "cmconnectionstatus.html"

CM_SYSTEM_TIME = Gauge(
    "cm_system_time_seconds", "Cable modem system time (Unix timestamp)"
)

DS_FREQUENCY = Gauge(
    "downstream_frequency_hz", "Downstream channel frequency (Hz)", ["channel_id"]
)
DS_POWER = Gauge("downstream_power_dbmv", "Downstream power (dBmV)", ["channel_id"])
DS_SNR = Gauge("downstream_snr_db", "Downstream SNR/MER (dB)", ["channel_id"])
DS_CORRECTED = Counter(
    "downstream_corrected", "Downstream corrected codewords", ["channel_id"]
)
DS_UNCORRECTABLES = Counter(
    "downstream_uncorrectables",
    "Downstream uncorrectable codewords",
    ["channel_id"],
)


_prev_corrected: dict[str, int] = {}
_prev_uncorrectables: dict[str, int] = {}


def scrape() -> None:
    with open(CM_STATUS_HTML, encoding="windows-1252") as f:
        html = f.read()
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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s:%(levelname)s:%(name)s:%(message)s",
    )
    logger.info("starting")
    start_http_server(8000)
    while True:
        scrape()
        logger.info("scraped")
        time.sleep(30)
