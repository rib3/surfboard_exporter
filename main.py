import logging
import os

from prometheus_client import REGISTRY, start_http_server
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily

from client import connection_status_get
from parser import parse_downstream_channels, parse_system_time, parse_upstream_channels

logger = logging.getLogger(__name__)


class SurfboardCollector:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    def collect(self):
        logger.info("collect start")
        html = connection_status_get(self.username, self.password)

        if not html:
            logger.warning("skipping collect, html=%r", html)
            return

        yield GaugeMetricFamily(
            "surfboard_system_time",
            "System time (Unix timestamp)",
            value=parse_system_time(html),
        )
        yield from self.collect_upstream(html)
        yield from self.collect_downstream(html)

        logger.info("collect end")

    def collect_upstream(self, html: str):
        us_frequency = GaugeMetricFamily(
            "surfboard_upstream_frequency_hz",
            "Upstream channel frequency (Hz)",
            labels=["channel_id"],
        )
        us_width = GaugeMetricFamily(
            "surfboard_upstream_width_hz",
            "Upstream channel width (Hz)",
            labels=["channel_id"],
        )
        us_power = GaugeMetricFamily(
            "surfboard_upstream_power_dbmv",
            "Upstream power (dBmV)",
            labels=["channel_id"],
        )
        for ch in parse_upstream_channels(html):
            cid = [str(ch.channel_id)]
            us_frequency.add_metric(cid, ch.frequency_hz)
            us_width.add_metric(cid, ch.width_hz)
            us_power.add_metric(cid, ch.power_dbmv)
        yield us_frequency
        yield us_width
        yield us_power

    def collect_downstream(self, html: str):
        ds_frequency = GaugeMetricFamily(
            "surfboard_downstream_frequency_hz",
            "Downstream channel frequency (Hz)",
            labels=["channel_id"],
        )
        ds_power = GaugeMetricFamily(
            "surfboard_downstream_power_dbmv",
            "Downstream power (dBmV)",
            labels=["channel_id"],
        )
        ds_snr = GaugeMetricFamily(
            "surfboard_downstream_snr_db",
            "Downstream SNR/MER (dB)",
            labels=["channel_id"],
        )
        ds_corrected = CounterMetricFamily(
            "surfboard_downstream_corrected",
            "Downstream corrected codewords",
            labels=["channel_id"],
        )
        ds_uncorrectables = CounterMetricFamily(
            "surfboard_downstream_uncorrectables",
            "Downstream uncorrectable codewords",
            labels=["channel_id"],
        )
        for ch in parse_downstream_channels(html):
            cid = [str(ch.channel_id)]
            ds_frequency.add_metric(cid, ch.frequency_hz)
            ds_power.add_metric(cid, ch.power_dbmv)
            ds_snr.add_metric(cid, ch.snr_db)
            ds_corrected.add_metric(cid, ch.corrected)
            ds_uncorrectables.add_metric(cid, ch.uncorrectables)
        yield ds_frequency
        yield ds_power
        yield ds_snr
        yield ds_corrected
        yield ds_uncorrectables


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
    REGISTRY.register(SurfboardCollector(username, password))
    _, thread = start_http_server(8000)
    thread.join()


if __name__ == "__main__":
    main()
