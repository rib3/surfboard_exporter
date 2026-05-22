from prometheus_client.metrics_core import Metric
from prometheus_client.samples import Sample

from testsupport.modem_html import (
    ConnectionStatus,
    DownstreamBondedChannelsRow,
    UpstreamBondedChannelsRow,
)
from testsupport.parser import expected_system_time_get


def expected_metrics_get(connection_status: ConnectionStatus) -> list[Metric]:
    startup = connection_status.startup
    return [
        _metric_ssl_verify_sample(1.0),
        _metric_scrape_success_sample(1.0),
        _metric_system_time_sample(expected_system_time_get(connection_status)),
        _metric_connectivity_state_ok_sample(
            1.0 if startup.connectivity_state == "OK" else 0.0,
            startup.connectivity_state_comment,
        ),
        _metric_security_enabled_sample(
            1.0 if startup.security == "Enabled" else 0.0,
            startup.security_comment,
        ),
        _metric_docsis_network_access_allowed_sample(
            1.0 if startup.docsis_network_access_enabled == "Allowed" else 0.0,
            startup.docsis_network_access_enabled_comment,
        ),
        *_metrics_upstream(*connection_status.upstream.rows),
        *_metrics_downstream(*connection_status.downstream.rows),
    ]


def _metric(name, doc, typ, samples):
    m = Metric(name, doc, typ)
    m.samples = samples
    return m


def _sample(name, labels, value):
    return Sample(name, labels, value, None, None, None)


def _samples_channel_id(name, channel_values: dict):
    return [_sample(name, {"channel_id": k}, v) for k, v in channel_values.items()]


def _by_channel_id(channels, attr: str):
    return {str(c.channel_id): getattr(c, attr) for c in channels}


def _metric_ssl_verify_sample(value):
    name = "surfboard_ssl_verify"
    return _metric(
        name,
        "Whether SSL verification is enabled (1=enabled, 0=disabled)",
        "gauge",
        [_sample(name, {}, value)],
    )


def _metric_scrape_success_sample(value):
    name = "surfboard_scrape_success"
    return _metric(
        name,
        "Whether the scrape was successful (1=success, 0=failure)",
        "gauge",
        [_sample(name, {}, value)],
    )


def _metric_system_time_sample(value):
    name = "surfboard_system_time"
    return _metric(
        name,
        "System time (Unix timestamp)",
        "gauge",
        [_sample(name, {}, value)],
    )


def _metric_connectivity_state_ok_sample(value, comment):
    name = "surfboard_connectivity_state_ok"
    return _metric(
        name,
        "Startup Procedure connectivity state (1=OK, 0=not OK, NaN=unknown)",
        "gauge",
        [_sample(name, {"comment": comment}, value)],
    )


def _metric_security_enabled_sample(value, comment):
    name = "surfboard_security_enabled"
    return _metric(
        name,
        "Startup Procedure security (1=Enabled, 0=not enabled, NaN=unknown)",
        "gauge",
        [_sample(name, {"comment": comment}, value)],
    )


def _metric_docsis_network_access_allowed_sample(value, comment):
    name = "surfboard_docsis_network_access_allowed"
    return _metric(
        name,
        (
            "Startup Procedure DOCSIS Network Access"
            " (1=Allowed, 0=not allowed, NaN=unknown)"
        ),
        "gauge",
        [_sample(name, {"comment": comment}, value)],
    )


def _metrics_downstream(*channels: DownstreamBondedChannelsRow):
    return [
        _metric_downstream_locked(channels),
        _metric_downstream_frequency_hz(channels),
        _metric_downstream_power_dbmv(channels),
        _metric_downstream_snr_db(channels),
        _metric_downstream_corrected(channels),
        _metric_downstream_uncorrectables(channels),
    ]


def _metrics_upstream(*channels: UpstreamBondedChannelsRow):
    return [
        _metric_upstream_locked(channels),
        _metric_upstream_frequency_hz(channels),
        _metric_upstream_width_hz(channels),
        _metric_upstream_power_dbmv(channels),
    ]


def _metric_downstream_locked(channels):
    name = "surfboard_downstream_locked"
    samples = [
        _sample(
            name,
            {"channel_id": str(c.channel_id), "lock_status": c.lock_status},
            1.0 if c.lock_status == "Locked" else 0.0,
        )
        for c in channels
    ]
    return _metric(
        name,
        "Downstream channel lock status (1=Locked, 0=not locked)",
        "gauge",
        samples,
    )


def _metric_downstream_frequency_hz(channels):
    name = "surfboard_downstream_frequency_hz"
    channel_values = _by_channel_id(channels, "frequency_hz")
    return _metric(
        name,
        "Downstream channel frequency (Hz)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_downstream_power_dbmv(channels):
    name = "surfboard_downstream_power_dbmv"
    channel_values = _by_channel_id(channels, "power_dbmv")
    return _metric(
        name,
        "Downstream power (dBmV)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_downstream_snr_db(channels):
    name = "surfboard_downstream_snr_db"
    channel_values = _by_channel_id(channels, "snr_db")
    return _metric(
        name,
        "Downstream SNR/MER (dB)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_downstream_corrected(channels):
    name = "surfboard_downstream_corrected"
    channel_values = _by_channel_id(channels, "corrected")
    return _metric(
        name,
        "Downstream corrected codewords",
        "counter",
        _samples_channel_id(f"{name}_total", channel_values),
    )


def _metric_downstream_uncorrectables(channels):
    name = "surfboard_downstream_uncorrectables"
    channel_values = _by_channel_id(channels, "uncorrectables")
    return _metric(
        name,
        "Downstream uncorrectable codewords",
        "counter",
        _samples_channel_id(f"{name}_total", channel_values),
    )


def _metric_upstream_locked(channels):
    name = "surfboard_upstream_locked"
    samples = [
        _sample(
            name,
            {"channel_id": str(c.channel_id), "lock_status": c.lock_status},
            1.0 if c.lock_status == "Locked" else 0.0,
        )
        for c in channels
    ]
    return _metric(
        name,
        "Upstream channel lock status (1=Locked, 0=not locked)",
        "gauge",
        samples,
    )


def _metric_upstream_frequency_hz(channels):
    name = "surfboard_upstream_frequency_hz"
    channel_values = _by_channel_id(channels, "frequency_hz")
    return _metric(
        name,
        "Upstream channel frequency (Hz)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_upstream_width_hz(channels):
    name = "surfboard_upstream_width_hz"
    channel_values = _by_channel_id(channels, "width_hz")
    return _metric(
        name,
        "Upstream channel width (Hz)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_upstream_power_dbmv(channels):
    name = "surfboard_upstream_power_dbmv"
    channel_values = _by_channel_id(channels, "power_dbmv")
    return _metric(
        name,
        "Upstream power (dBmV)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )
