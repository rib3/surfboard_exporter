from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.metrics_core import Metric
from prometheus_client.parser import text_string_to_metric_families
from prometheus_client.samples import Sample

import server
from tests.test_server import HTML, LABELS, _get_sample_value


def _metric(name, doc, typ, samples):
    m = Metric(name, doc, typ)
    m.samples = samples
    return m


def _sample(name, labels, value):
    return Sample(name, labels, value, None, None, None)


def _samples_channel_id(name, channel_values: dict):
    return [_sample(name, {"channel_id": k}, v) for k, v in channel_values.items()]


def _by_channel_id(channels, attr: str):
    return {c.channel_id: getattr(c, attr) for c in channels}


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


@dataclass
class UpstreamChannelValues:
    channel_id: str
    lock_status: str
    locked: float
    frequency_hz: float
    width_hz: float
    power_dbmv: float


def _metrics_upstream(*channels: UpstreamChannelValues):
    return [
        _metric_upstream_locked(channels),
        _metric_upstream_frequency_hz(_by_channel_id(channels, "frequency_hz")),
        _metric_upstream_width_hz(_by_channel_id(channels, "width_hz")),
        _metric_upstream_power_dbmv(_by_channel_id(channels, "power_dbmv")),
    ]


@dataclass
class DownstreamChannelValues:
    channel_id: str
    lock_status: str
    locked: float
    frequency_hz: float
    power_dbmv: float
    snr_db: float
    corrected: float
    uncorrectables: float


def _metrics_downstream(*channels: DownstreamChannelValues):
    return [
        _metric_downstream_locked(channels),
        _metric_downstream_frequency_hz(_by_channel_id(channels, "frequency_hz")),
        _metric_downstream_power_dbmv(_by_channel_id(channels, "power_dbmv")),
        _metric_downstream_snr_db(_by_channel_id(channels, "snr_db")),
        _metric_downstream_corrected(_by_channel_id(channels, "corrected")),
        _metric_downstream_uncorrectables(_by_channel_id(channels, "uncorrectables")),
    ]


def _metric_upstream_locked(channels):
    name = "surfboard_upstream_locked"
    samples = [
        _sample(
            name,
            {"channel_id": c.channel_id, "lock_status": c.lock_status},
            c.locked,
        )
        for c in channels
    ]
    return _metric(
        name,
        "Upstream channel lock status (1=Locked, 0=not locked)",
        "gauge",
        samples,
    )


def _metric_upstream_frequency_hz(channel_values: dict):
    name = "surfboard_upstream_frequency_hz"
    return _metric(
        name,
        "Upstream channel frequency (Hz)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_upstream_width_hz(channel_values: dict):
    name = "surfboard_upstream_width_hz"
    return _metric(
        name,
        "Upstream channel width (Hz)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_upstream_power_dbmv(channel_values: dict):
    name = "surfboard_upstream_power_dbmv"
    return _metric(
        name,
        "Upstream power (dBmV)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_downstream_locked(channels):
    name = "surfboard_downstream_locked"
    samples = [
        _sample(
            name,
            {"channel_id": c.channel_id, "lock_status": c.lock_status},
            c.locked,
        )
        for c in channels
    ]
    return _metric(
        name,
        "Downstream channel lock status (1=Locked, 0=not locked)",
        "gauge",
        samples,
    )


def _metric_downstream_frequency_hz(channel_values: dict):
    name = "surfboard_downstream_frequency_hz"
    return _metric(
        name,
        "Downstream channel frequency (Hz)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_downstream_power_dbmv(channel_values: dict):
    name = "surfboard_downstream_power_dbmv"
    return _metric(
        name,
        "Downstream power (dBmV)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_downstream_snr_db(channel_values: dict):
    name = "surfboard_downstream_snr_db"
    return _metric(
        name,
        "Downstream SNR/MER (dB)",
        "gauge",
        _samples_channel_id(name, channel_values),
    )


def _metric_downstream_corrected(channel_values: dict):
    name = "surfboard_downstream_corrected"
    return _metric(
        name,
        "Downstream corrected codewords",
        "counter",
        _samples_channel_id(f"{name}_total", channel_values),
    )


def _metric_downstream_uncorrectables(channel_values: dict):
    name = "surfboard_downstream_uncorrectables"
    return _metric(
        name,
        "Downstream uncorrectable codewords",
        "counter",
        _samples_channel_id(f"{name}_total", channel_values),
    )


def test__generate_latest(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(username="user", password="pass", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=HTML)

    registry = CollectorRegistry()
    collector = server.SurfboardCollector("user", "pass")
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    expected_system_time = datetime(2026, 3, 26, 14, 58, 2).timestamp()
    assert _get_sample_value(metrics, "surfboard_system_time") == expected_system_time
    assert (
        _get_sample_value(metrics, "surfboard_downstream_frequency_hz", LABELS)
        == 387000000
    )
    assert _get_sample_value(metrics, "surfboard_downstream_power_dbmv", LABELS) == -8.2
    assert _get_sample_value(metrics, "surfboard_downstream_snr_db", LABELS) == 43.5
    assert (
        _get_sample_value(metrics, "surfboard_downstream_corrected_total", LABELS)
        == 100
    )
    assert (
        _get_sample_value(metrics, "surfboard_downstream_uncorrectables_total", LABELS)
        == 200
    )
    assert (
        _get_sample_value(metrics, "surfboard_upstream_frequency_hz", LABELS)
        == 16400000
    )
    assert _get_sample_value(metrics, "surfboard_upstream_width_hz", LABELS) == 6400000
    assert _get_sample_value(metrics, "surfboard_upstream_power_dbmv", LABELS) == 46.0

    expected_metrics = [
        _metric_ssl_verify_sample(1.0),
        _metric_scrape_success_sample(1.0),
        _metric_system_time_sample(expected_system_time),
        *_metrics_upstream(
            UpstreamChannelValues(
                channel_id="1",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=16400000.0,
                width_hz=6400000.0,
                power_dbmv=46.0,
            ),
        ),
        *_metrics_downstream(
            DownstreamChannelValues(
                channel_id="1",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=387000000.0,
                power_dbmv=-8.2,
                snr_db=43.5,
                corrected=100.0,
                uncorrectables=200.0,
            ),
        ),
    ]
    assert metrics == expected_metrics


@pytest.mark.parametrize("collector_kwargs", [{}, {"modem_certificate_verify": True}])
def test__generate_latest__ssl_verify__enabled__certificate_path__none(
    https_server_modem, collector_kwargs
):
    registry = CollectorRegistry()
    collector = server.SurfboardCollector(
        "user", "pass", modem_host=https_server_modem.host, **collector_kwargs
    )
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    assert _get_sample_value(metrics, "surfboard_ssl_verify") == 1.0
    assert _get_sample_value(metrics, "surfboard_scrape_success") == 0.0


def test__generate_latest__ssl_verify__disabled(
    https_server_modem,
    https_server_modem_expect_ordered_request_login_get,
    https_server_modem_expect_ordered_request_connectionstatus_get,
):
    _, token = https_server_modem_expect_ordered_request_login_get(
        username="user", password="pass"
    )
    https_server_modem_expect_ordered_request_connectionstatus_get(token=token)

    registry = CollectorRegistry()
    collector = server.SurfboardCollector(
        "user",
        "pass",
        modem_host=https_server_modem.host,
        modem_certificate_verify=False,
    )
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    assert _get_sample_value(metrics, "surfboard_ssl_verify") == 0.0
    assert _get_sample_value(metrics, "surfboard_scrape_success") == 1.0


def test__generate_latest_real_html__2026_03_26_1558(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    html = Path("testdata/cmconnectionstatus.2026-03-26-1558.html").read_text(
        encoding="windows-1252"
    )
    token = "abc123token"
    surfboard_api_mock_get_login(username="user", password="pass", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=html)

    registry = CollectorRegistry()
    collector = server.SurfboardCollector("user", "pass")
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    expected_system_time = datetime(2026, 3, 26, 14, 58, 2).timestamp()
    expected_metrics = [
        _metric_ssl_verify_sample(1.0),
        _metric_scrape_success_sample(1.0),
        _metric_system_time_sample(expected_system_time),
        *_metrics_upstream(
            UpstreamChannelValues(
                channel_id="1",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=16400000.0,
                width_hz=6400000.0,
                power_dbmv=46.0,
            ),
            UpstreamChannelValues(
                channel_id="2",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=22800000.0,
                width_hz=6400000.0,
                power_dbmv=48.0,
            ),
            UpstreamChannelValues(
                channel_id="3",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=29200000.0,
                width_hz=6400000.0,
                power_dbmv=47.0,
            ),
            UpstreamChannelValues(
                channel_id="4",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=35600000.0,
                width_hz=6400000.0,
                power_dbmv=48.0,
            ),
        ),
        *_metrics_downstream(
            DownstreamChannelValues(
                channel_id="20",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=975000000.0,
                power_dbmv=-7.3,
                snr_db=41.5,
                corrected=3555.0,
                uncorrectables=2096.0,
            ),
            DownstreamChannelValues(
                channel_id="1",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=387000000.0,
                power_dbmv=-8.2,
                snr_db=43.5,
                corrected=232263.0,
                uncorrectables=375707.0,
            ),
            DownstreamChannelValues(
                channel_id="2",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=393000000.0,
                power_dbmv=-8.7,
                snr_db=43.2,
                corrected=85776.0,
                uncorrectables=48483.0,
            ),
            DownstreamChannelValues(
                channel_id="3",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=399000000.0,
                power_dbmv=-9.3,
                snr_db=42.0,
                corrected=230296.0,
                uncorrectables=378439.0,
            ),
            DownstreamChannelValues(
                channel_id="4",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=405000000.0,
                power_dbmv=-9.4,
                snr_db=42.4,
                corrected=250661.0,
                uncorrectables=346300.0,
            ),
            DownstreamChannelValues(
                channel_id="5",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=411000000.0,
                power_dbmv=-9.2,
                snr_db=42.7,
                corrected=222604.0,
                uncorrectables=330745.0,
            ),
            DownstreamChannelValues(
                channel_id="6",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=417000000.0,
                power_dbmv=-8.6,
                snr_db=42.6,
                corrected=217616.0,
                uncorrectables=309869.0,
            ),
            DownstreamChannelValues(
                channel_id="7",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=423000000.0,
                power_dbmv=-8.3,
                snr_db=42.8,
                corrected=213849.0,
                uncorrectables=295936.0,
            ),
            DownstreamChannelValues(
                channel_id="8",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=429000000.0,
                power_dbmv=-8.4,
                snr_db=43.2,
                corrected=212308.0,
                uncorrectables=277445.0,
            ),
            DownstreamChannelValues(
                channel_id="9",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=435000000.0,
                power_dbmv=-8.9,
                snr_db=42.6,
                corrected=214025.0,
                uncorrectables=243066.0,
            ),
            DownstreamChannelValues(
                channel_id="10",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=441000000.0,
                power_dbmv=-9.4,
                snr_db=41.9,
                corrected=224305.0,
                uncorrectables=214273.0,
            ),
            DownstreamChannelValues(
                channel_id="11",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=447000000.0,
                power_dbmv=-9.3,
                snr_db=42.4,
                corrected=228119.0,
                uncorrectables=199786.0,
            ),
            DownstreamChannelValues(
                channel_id="12",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=453000000.0,
                power_dbmv=-8.7,
                snr_db=42.6,
                corrected=241083.0,
                uncorrectables=147333.0,
            ),
            DownstreamChannelValues(
                channel_id="13",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=459000000.0,
                power_dbmv=-8.1,
                snr_db=42.7,
                corrected=271700.0,
                uncorrectables=232013.0,
            ),
            DownstreamChannelValues(
                channel_id="14",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=465000000.0,
                power_dbmv=-8.1,
                snr_db=42.7,
                corrected=253546.0,
                uncorrectables=85992.0,
            ),
            DownstreamChannelValues(
                channel_id="15",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=471000000.0,
                power_dbmv=-8.6,
                snr_db=30.7,
                corrected=46267820.0,
                uncorrectables=292531.0,
            ),
            DownstreamChannelValues(
                channel_id="16",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=477000000.0,
                power_dbmv=-9.2,
                snr_db=30.1,
                corrected=172884998.0,
                uncorrectables=4283932.0,
            ),
            DownstreamChannelValues(
                channel_id="17",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=957000000.0,
                power_dbmv=-8.3,
                snr_db=41.4,
                corrected=9685.0,
                uncorrectables=7806.0,
            ),
            DownstreamChannelValues(
                channel_id="18",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=963000000.0,
                power_dbmv=-7.6,
                snr_db=41.8,
                corrected=4931.0,
                uncorrectables=4922.0,
            ),
            DownstreamChannelValues(
                channel_id="19",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=969000000.0,
                power_dbmv=-7.2,
                snr_db=41.9,
                corrected=3862.0,
                uncorrectables=3265.0,
            ),
            DownstreamChannelValues(
                channel_id="21",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=981000000.0,
                power_dbmv=-7.8,
                snr_db=41.1,
                corrected=5133.0,
                uncorrectables=2743.0,
            ),
            DownstreamChannelValues(
                channel_id="22",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=987000000.0,
                power_dbmv=-8.1,
                snr_db=41.0,
                corrected=6155.0,
                uncorrectables=3719.0,
            ),
            DownstreamChannelValues(
                channel_id="23",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=993000000.0,
                power_dbmv=-7.8,
                snr_db=41.3,
                corrected=6073.0,
                uncorrectables=5006.0,
            ),
            DownstreamChannelValues(
                channel_id="24",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=999000000.0,
                power_dbmv=-7.7,
                snr_db=41.0,
                corrected=4859.0,
                uncorrectables=4586.0,
            ),
            DownstreamChannelValues(
                channel_id="193",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=774000000.0,
                power_dbmv=-8.5,
                snr_db=17.0,
                corrected=1366671191.0,
                uncorrectables=1937019.0,
            ),
        ),
    ]
    assert metrics == expected_metrics


def test__generate_latest_real_html__2026_03_30_1441(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    html = Path("testdata/cmconnectionstatus.2026-03-30-1441.html").read_text(
        encoding="windows-1252"
    )
    token = "abc123token"
    surfboard_api_mock_get_login(username="user", password="pass", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=html)

    registry = CollectorRegistry()
    collector = server.SurfboardCollector("user", "pass")
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    expected_system_time = datetime(2026, 3, 30, 13, 40, 58).timestamp()
    expected_metrics = [
        _metric_ssl_verify_sample(1.0),
        _metric_scrape_success_sample(1.0),
        _metric_system_time_sample(expected_system_time),
        *_metrics_upstream(
            UpstreamChannelValues(
                channel_id="1",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=16400000.0,
                width_hz=6400000.0,
                power_dbmv=46.0,
            ),
            UpstreamChannelValues(
                channel_id="2",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=22800000.0,
                width_hz=6400000.0,
                power_dbmv=47.0,
            ),
            UpstreamChannelValues(
                channel_id="3",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=29200000.0,
                width_hz=6400000.0,
                power_dbmv=46.0,
            ),
            UpstreamChannelValues(
                channel_id="4",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=35600000.0,
                width_hz=6400000.0,
                power_dbmv=47.0,
            ),
        ),
        *_metrics_downstream(
            DownstreamChannelValues(
                channel_id="20",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=975000000.0,
                power_dbmv=-9.7,
                snr_db=39.8,
                corrected=4030.0,
                uncorrectables=2127.0,
            ),
            DownstreamChannelValues(
                channel_id="1",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=387000000.0,
                power_dbmv=-9.3,
                snr_db=42.5,
                corrected=242830.0,
                uncorrectables=380046.0,
            ),
            DownstreamChannelValues(
                channel_id="2",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=393000000.0,
                power_dbmv=-9.6,
                snr_db=42.4,
                corrected=96209.0,
                uncorrectables=52921.0,
            ),
            DownstreamChannelValues(
                channel_id="3",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=399000000.0,
                power_dbmv=-10.0,
                snr_db=41.4,
                corrected=241391.0,
                uncorrectables=383321.0,
            ),
            DownstreamChannelValues(
                channel_id="4",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=405000000.0,
                power_dbmv=-10.1,
                snr_db=41.7,
                corrected=263079.0,
                uncorrectables=350594.0,
            ),
            DownstreamChannelValues(
                channel_id="5",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=411000000.0,
                power_dbmv=-9.9,
                snr_db=42.1,
                corrected=231458.0,
                uncorrectables=334754.0,
            ),
            DownstreamChannelValues(
                channel_id="6",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=417000000.0,
                power_dbmv=-9.6,
                snr_db=41.8,
                corrected=225216.0,
                uncorrectables=313119.0,
            ),
            DownstreamChannelValues(
                channel_id="7",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=423000000.0,
                power_dbmv=-9.4,
                snr_db=41.7,
                corrected=220859.0,
                uncorrectables=298511.0,
            ),
            DownstreamChannelValues(
                channel_id="8",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=429000000.0,
                power_dbmv=-9.5,
                snr_db=42.2,
                corrected=219215.0,
                uncorrectables=279809.0,
            ),
            DownstreamChannelValues(
                channel_id="9",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=435000000.0,
                power_dbmv=-9.8,
                snr_db=41.8,
                corrected=220279.0,
                uncorrectables=245579.0,
            ),
            DownstreamChannelValues(
                channel_id="10",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=441000000.0,
                power_dbmv=-10.1,
                snr_db=41.3,
                corrected=230568.0,
                uncorrectables=216911.0,
            ),
            DownstreamChannelValues(
                channel_id="11",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=447000000.0,
                power_dbmv=-10.0,
                snr_db=41.7,
                corrected=234409.0,
                uncorrectables=202251.0,
            ),
            DownstreamChannelValues(
                channel_id="12",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=453000000.0,
                power_dbmv=-9.6,
                snr_db=40.6,
                corrected=246251.0,
                uncorrectables=149073.0,
            ),
            DownstreamChannelValues(
                channel_id="13",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=459000000.0,
                power_dbmv=-9.2,
                snr_db=41.5,
                corrected=280736.0,
                uncorrectables=245801.0,
            ),
            DownstreamChannelValues(
                channel_id="14",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=465000000.0,
                power_dbmv=-9.3,
                snr_db=41.9,
                corrected=257639.0,
                uncorrectables=86973.0,
            ),
            DownstreamChannelValues(
                channel_id="15",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=471000000.0,
                power_dbmv=-9.7,
                snr_db=32.9,
                corrected=47502872.0,
                uncorrectables=294073.0,
            ),
            DownstreamChannelValues(
                channel_id="16",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=477000000.0,
                power_dbmv=-10.0,
                snr_db=30.1,
                corrected=172988432.0,
                uncorrectables=4285899.0,
            ),
            DownstreamChannelValues(
                channel_id="17",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=957000000.0,
                power_dbmv=-10.5,
                snr_db=39.7,
                corrected=10316.0,
                uncorrectables=7915.0,
            ),
            DownstreamChannelValues(
                channel_id="18",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=963000000.0,
                power_dbmv=-10.0,
                snr_db=40.0,
                corrected=5433.0,
                uncorrectables=5005.0,
            ),
            DownstreamChannelValues(
                channel_id="19",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=969000000.0,
                power_dbmv=-9.7,
                snr_db=40.1,
                corrected=4241.0,
                uncorrectables=3303.0,
            ),
            DownstreamChannelValues(
                channel_id="21",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=981000000.0,
                power_dbmv=-10.1,
                snr_db=39.4,
                corrected=5634.0,
                uncorrectables=2819.0,
            ),
            DownstreamChannelValues(
                channel_id="22",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=987000000.0,
                power_dbmv=-10.4,
                snr_db=39.2,
                corrected=6758.0,
                uncorrectables=3816.0,
            ),
            DownstreamChannelValues(
                channel_id="23",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=993000000.0,
                power_dbmv=-10.1,
                snr_db=39.4,
                corrected=6748.0,
                uncorrectables=5045.0,
            ),
            DownstreamChannelValues(
                channel_id="24",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=999000000.0,
                power_dbmv=-10.3,
                snr_db=39.0,
                corrected=5326.0,
                uncorrectables=4669.0,
            ),
            DownstreamChannelValues(
                channel_id="193",
                lock_status="Locked",
                locked=1.0,
                frequency_hz=774000000.0,
                power_dbmv=-10.5,
                snr_db=17.8,
                corrected=1454959720.0,
                uncorrectables=2049372.0,
            ),
        ),
    ]
    assert metrics == expected_metrics
