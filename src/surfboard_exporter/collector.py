import logging

from prometheus_client.core import CounterMetricFamily, GaugeMetricFamily

from .client import SurfboardClient
from .parser import (
    parse_connectivity_state,
    parse_downstream_channels,
    parse_security,
    parse_system_time,
    parse_upstream_channels,
)

logger = logging.getLogger(__name__)


class SurfboardCollector:
    def __init__(
        self,
        *,
        username: str | None = None,
        password: str,
        modem_host: str | None = None,
        modem_certificate_verify: bool | None = None,
        modem_certificate_path: str | None = None,
        response_save: bool = False,
    ) -> None:
        self._client = SurfboardClient(
            username=username,
            password=password,
            modem_host=modem_host,
            modem_certificate_verify=modem_certificate_verify,
            modem_certificate_path=modem_certificate_path,
        )
        self.response_save = response_save
        logger.info("response_save=%r", self.response_save)

    def collect(self):
        logger.debug("collect start")
        yield GaugeMetricFamily(
            "surfboard_ssl_verify",
            "Whether SSL verification is enabled (1=enabled, 0=disabled)",
            value=1 if self._client.ssl_verify_enabled else 0,
        )
        html = self._client.connection_status_get(response_save=self.response_save)
        yield GaugeMetricFamily(
            "surfboard_scrape_success",
            "Whether the scrape was successful (1=success, 0=failure)",
            value=1 if html else 0,
        )
        if not html:
            logger.warning("skipping collect, html=%r", html)
            return

        yield GaugeMetricFamily(
            "surfboard_system_time",
            "System time (Unix timestamp)",
            value=parse_system_time(html),
        )
        state = parse_connectivity_state(html)
        conn_ok = GaugeMetricFamily(
            "surfboard_connectivity_state_ok",
            "Startup Procedure connectivity state (1=OK, 0=not OK, NaN=unknown)",
            labels=["comment"],
        )
        conn_ok.add_metric([state.comment], state.ok)
        yield conn_ok
        security = parse_security(html)
        security_enabled = GaugeMetricFamily(
            "surfboard_security_enabled",
            "Startup Procedure security (1=Enabled, 0=not enabled, NaN=unknown)",
            labels=["comment"],
        )
        security_enabled.add_metric([security.comment], security.enabled)
        yield security_enabled
        yield from self.collect_upstream(html)
        yield from self.collect_downstream(html)

        logger.debug("collect end")

    def collect_upstream(self, html: str):
        us_locked = GaugeMetricFamily(
            "surfboard_upstream_locked",
            "Upstream channel lock status (1=Locked, 0=not locked)",
            labels=["channel_id", "lock_status"],
        )
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
            labels = [str(ch.channel_id)]
            us_locked.add_metric(labels + [ch.lock_status], ch.locked)
            us_frequency.add_metric(labels, ch.frequency_hz)
            us_width.add_metric(labels, ch.width_hz)
            us_power.add_metric(labels, ch.power_dbmv)
        yield us_locked
        yield us_frequency
        yield us_width
        yield us_power

    def collect_downstream(self, html: str):
        ds_locked = GaugeMetricFamily(
            "surfboard_downstream_locked",
            "Downstream channel lock status (1=Locked, 0=not locked)",
            labels=["channel_id", "lock_status"],
        )
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
            labels = [str(ch.channel_id)]
            ds_locked.add_metric(labels + [ch.lock_status], ch.locked)
            ds_frequency.add_metric(labels, ch.frequency_hz)
            ds_power.add_metric(labels, ch.power_dbmv)
            ds_snr.add_metric(labels, ch.snr_db)
            ds_corrected.add_metric(labels, ch.corrected)
            ds_uncorrectables.add_metric(labels, ch.uncorrectables)
        yield ds_locked
        yield ds_frequency
        yield ds_power
        yield ds_snr
        yield ds_corrected
        yield ds_uncorrectables
