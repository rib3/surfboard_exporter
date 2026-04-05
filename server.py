import logging

from prometheus_client import REGISTRY, start_http_server
from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily

from client import SurfboardClient
from parser import parse_downstream_channels, parse_system_time, parse_upstream_channels

logger = logging.getLogger(__name__)


class SurfboardCollector:
    def __init__(
        self,
        username: str,
        password: str,
        modem_certificate_path: str | None = None,
        response_save: bool = False,
    ) -> None:
        self._client = SurfboardClient(
            username, password, modem_certificate_path=modem_certificate_path
        )
        self.response_save = response_save
        logger.info("response_save=%r", self.response_save)

    def collect(self):
        logger.info("collect start")
        html = self._client.connection_status_get(response_save=self.response_save)
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


def start(
    username: str,
    password: str,
    modem_certificate_path: str | None = None,
    response_save: bool = False,
):
    REGISTRY.register(
        SurfboardCollector(
            username,
            password,
            modem_certificate_path=modem_certificate_path,
            response_save=response_save,
        )
    )
    return start_http_server(8000)
