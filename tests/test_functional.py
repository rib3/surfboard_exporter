import re
from datetime import datetime

import pytest
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.metrics_core import Metric
from prometheus_client.parser import text_string_to_metric_families
from prometheus_client.samples import Sample

from surfboard_exporter.collector import SurfboardCollector
from tests.test_collector import HTML, LABELS, _get_sample_value
from testsupport import TESTDATA_DIR
from testsupport.modem_html import (
    DownstreamBondedChannelsRow,
    UpstreamBondedChannelsRow,
)


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


def test__init__username__empty():
    with pytest.raises(
        ValueError, match="^username='' is not valid, pass a real value, or None$"
    ):
        SurfboardCollector(username="", password="pass")


def test__init__modem_host__empty():
    with pytest.raises(
        ValueError, match="^modem_host='' is not valid, pass a real value, or None$"
    ):
        SurfboardCollector(password="pass", modem_host="")


def test__init__modem_certificate_path__does_not_exist(tmp_path):
    missing = tmp_path / "missing.crt"
    expected = f"modem_certificate_path={str(missing)!r} does not exist"

    with pytest.raises(FileNotFoundError, match=f"^{re.escape(expected)}$"):
        SurfboardCollector(password="pass", modem_certificate_path=missing)


@pytest.mark.parametrize(
    ("collector_kwargs", "expected_username"),
    [
        ({}, "admin"),
        ({"username": "user"}, "user"),
    ],
)
def test__generate_latest(
    surfboard_api_mock_get_login,
    surfboard_api_mock_get_connectionstatus,
    collector_kwargs,
    expected_username,
):
    token = "abc123token"
    surfboard_api_mock_get_login(
        username=expected_username, password="pass", token=token
    )
    surfboard_api_mock_get_connectionstatus(token=token, text=HTML)

    registry = CollectorRegistry()
    collector = SurfboardCollector(password="pass", **collector_kwargs)
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
        _metric_connectivity_state_ok_sample(1.0, "Operational"),
        _metric_security_enabled_sample(1.0, "BPI+"),
        _metric_docsis_network_access_allowed_sample(1.0, ""),
        *_metrics_upstream(
            UpstreamBondedChannelsRow(
                channel=1,
                channel_id=1,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=16400000,
                width_hz=6400000,
                power_dbmv=46.0,
            ),
        ),
        *_metrics_downstream(
            DownstreamBondedChannelsRow(
                channel_id=1,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=387000000,
                power_dbmv=-8.2,
                snr_db=43.5,
                corrected=100,
                uncorrectables=200,
            ),
        ),
    ]
    assert metrics == expected_metrics


@pytest.mark.parametrize("collector_kwargs", [{}, {"modem_certificate_verify": True}])
def test__generate_latest__ssl_verify__enabled__certificate_path__none(
    https_server_modem, collector_kwargs
):
    registry = CollectorRegistry()
    collector = SurfboardCollector(
        username="user",
        password="pass",
        modem_host=https_server_modem.host,
        **collector_kwargs,
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
    collector = SurfboardCollector(
        username="user",
        password="pass",
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
    html = (TESTDATA_DIR / "cmconnectionstatus.2026-03-26-1558.html").read_text(
        encoding="windows-1252"
    )
    token = "abc123token"
    surfboard_api_mock_get_login(password="pass", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=html)

    registry = CollectorRegistry()
    collector = SurfboardCollector(password="pass")
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    expected_system_time = datetime(2026, 3, 26, 14, 58, 2).timestamp()
    expected_metrics = [
        _metric_ssl_verify_sample(1.0),
        _metric_scrape_success_sample(1.0),
        _metric_system_time_sample(expected_system_time),
        _metric_connectivity_state_ok_sample(1.0, "Operational"),
        _metric_security_enabled_sample(1.0, "BPI+"),
        _metric_docsis_network_access_allowed_sample(1.0, ""),
        *_metrics_upstream(
            UpstreamBondedChannelsRow(
                channel=1,
                channel_id=1,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=16400000,
                width_hz=6400000,
                power_dbmv=46.0,
            ),
            UpstreamBondedChannelsRow(
                channel=2,
                channel_id=2,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=22800000,
                width_hz=6400000,
                power_dbmv=48.0,
            ),
            UpstreamBondedChannelsRow(
                channel=3,
                channel_id=3,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=29200000,
                width_hz=6400000,
                power_dbmv=47.0,
            ),
            UpstreamBondedChannelsRow(
                channel=4,
                channel_id=4,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=35600000,
                width_hz=6400000,
                power_dbmv=48.0,
            ),
        ),
        *_metrics_downstream(
            DownstreamBondedChannelsRow(
                channel_id=20,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=975000000,
                power_dbmv=-7.3,
                snr_db=41.5,
                corrected=3555,
                uncorrectables=2096,
            ),
            DownstreamBondedChannelsRow(
                channel_id=1,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=387000000,
                power_dbmv=-8.2,
                snr_db=43.5,
                corrected=232263,
                uncorrectables=375707,
            ),
            DownstreamBondedChannelsRow(
                channel_id=2,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=393000000,
                power_dbmv=-8.7,
                snr_db=43.2,
                corrected=85776,
                uncorrectables=48483,
            ),
            DownstreamBondedChannelsRow(
                channel_id=3,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=399000000,
                power_dbmv=-9.3,
                snr_db=42.0,
                corrected=230296,
                uncorrectables=378439,
            ),
            DownstreamBondedChannelsRow(
                channel_id=4,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=405000000,
                power_dbmv=-9.4,
                snr_db=42.4,
                corrected=250661,
                uncorrectables=346300,
            ),
            DownstreamBondedChannelsRow(
                channel_id=5,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=411000000,
                power_dbmv=-9.2,
                snr_db=42.7,
                corrected=222604,
                uncorrectables=330745,
            ),
            DownstreamBondedChannelsRow(
                channel_id=6,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=417000000,
                power_dbmv=-8.6,
                snr_db=42.6,
                corrected=217616,
                uncorrectables=309869,
            ),
            DownstreamBondedChannelsRow(
                channel_id=7,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=423000000,
                power_dbmv=-8.3,
                snr_db=42.8,
                corrected=213849,
                uncorrectables=295936,
            ),
            DownstreamBondedChannelsRow(
                channel_id=8,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=429000000,
                power_dbmv=-8.4,
                snr_db=43.2,
                corrected=212308,
                uncorrectables=277445,
            ),
            DownstreamBondedChannelsRow(
                channel_id=9,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=435000000,
                power_dbmv=-8.9,
                snr_db=42.6,
                corrected=214025,
                uncorrectables=243066,
            ),
            DownstreamBondedChannelsRow(
                channel_id=10,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=441000000,
                power_dbmv=-9.4,
                snr_db=41.9,
                corrected=224305,
                uncorrectables=214273,
            ),
            DownstreamBondedChannelsRow(
                channel_id=11,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=447000000,
                power_dbmv=-9.3,
                snr_db=42.4,
                corrected=228119,
                uncorrectables=199786,
            ),
            DownstreamBondedChannelsRow(
                channel_id=12,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=453000000,
                power_dbmv=-8.7,
                snr_db=42.6,
                corrected=241083,
                uncorrectables=147333,
            ),
            DownstreamBondedChannelsRow(
                channel_id=13,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=459000000,
                power_dbmv=-8.1,
                snr_db=42.7,
                corrected=271700,
                uncorrectables=232013,
            ),
            DownstreamBondedChannelsRow(
                channel_id=14,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=465000000,
                power_dbmv=-8.1,
                snr_db=42.7,
                corrected=253546,
                uncorrectables=85992,
            ),
            DownstreamBondedChannelsRow(
                channel_id=15,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=471000000,
                power_dbmv=-8.6,
                snr_db=30.7,
                corrected=46267820,
                uncorrectables=292531,
            ),
            DownstreamBondedChannelsRow(
                channel_id=16,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=477000000,
                power_dbmv=-9.2,
                snr_db=30.1,
                corrected=172884998,
                uncorrectables=4283932,
            ),
            DownstreamBondedChannelsRow(
                channel_id=17,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=957000000,
                power_dbmv=-8.3,
                snr_db=41.4,
                corrected=9685,
                uncorrectables=7806,
            ),
            DownstreamBondedChannelsRow(
                channel_id=18,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=963000000,
                power_dbmv=-7.6,
                snr_db=41.8,
                corrected=4931,
                uncorrectables=4922,
            ),
            DownstreamBondedChannelsRow(
                channel_id=19,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=969000000,
                power_dbmv=-7.2,
                snr_db=41.9,
                corrected=3862,
                uncorrectables=3265,
            ),
            DownstreamBondedChannelsRow(
                channel_id=21,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=981000000,
                power_dbmv=-7.8,
                snr_db=41.1,
                corrected=5133,
                uncorrectables=2743,
            ),
            DownstreamBondedChannelsRow(
                channel_id=22,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=987000000,
                power_dbmv=-8.1,
                snr_db=41.0,
                corrected=6155,
                uncorrectables=3719,
            ),
            DownstreamBondedChannelsRow(
                channel_id=23,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=993000000,
                power_dbmv=-7.8,
                snr_db=41.3,
                corrected=6073,
                uncorrectables=5006,
            ),
            DownstreamBondedChannelsRow(
                channel_id=24,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=999000000,
                power_dbmv=-7.7,
                snr_db=41.0,
                corrected=4859,
                uncorrectables=4586,
            ),
            DownstreamBondedChannelsRow(
                channel_id=193,
                lock_status="Locked",
                modulation="Other",
                frequency_hz=774000000,
                power_dbmv=-8.5,
                snr_db=17.0,
                corrected=1366671191,
                uncorrectables=1937019,
            ),
        ),
    ]
    assert metrics == expected_metrics


def test__generate_latest_real_html__2026_03_30_1441(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    html = (TESTDATA_DIR / "cmconnectionstatus.2026-03-30-1441.html").read_text(
        encoding="windows-1252"
    )
    token = "abc123token"
    surfboard_api_mock_get_login(password="pass", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=html)

    registry = CollectorRegistry()
    collector = SurfboardCollector(password="pass")
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    expected_system_time = datetime(2026, 3, 30, 13, 40, 58).timestamp()
    expected_metrics = [
        _metric_ssl_verify_sample(1.0),
        _metric_scrape_success_sample(1.0),
        _metric_system_time_sample(expected_system_time),
        _metric_connectivity_state_ok_sample(1.0, "Operational"),
        _metric_security_enabled_sample(1.0, "BPI+"),
        _metric_docsis_network_access_allowed_sample(1.0, ""),
        *_metrics_upstream(
            UpstreamBondedChannelsRow(
                channel=1,
                channel_id=1,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=16400000,
                width_hz=6400000,
                power_dbmv=46.0,
            ),
            UpstreamBondedChannelsRow(
                channel=2,
                channel_id=2,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=22800000,
                width_hz=6400000,
                power_dbmv=47.0,
            ),
            UpstreamBondedChannelsRow(
                channel=3,
                channel_id=3,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=29200000,
                width_hz=6400000,
                power_dbmv=46.0,
            ),
            UpstreamBondedChannelsRow(
                channel=4,
                channel_id=4,
                lock_status="Locked",
                channel_type="SC-QAM Upstream",
                frequency_hz=35600000,
                width_hz=6400000,
                power_dbmv=47.0,
            ),
        ),
        *_metrics_downstream(
            DownstreamBondedChannelsRow(
                channel_id=20,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=975000000,
                power_dbmv=-9.7,
                snr_db=39.8,
                corrected=4030,
                uncorrectables=2127,
            ),
            DownstreamBondedChannelsRow(
                channel_id=1,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=387000000,
                power_dbmv=-9.3,
                snr_db=42.5,
                corrected=242830,
                uncorrectables=380046,
            ),
            DownstreamBondedChannelsRow(
                channel_id=2,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=393000000,
                power_dbmv=-9.6,
                snr_db=42.4,
                corrected=96209,
                uncorrectables=52921,
            ),
            DownstreamBondedChannelsRow(
                channel_id=3,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=399000000,
                power_dbmv=-10.0,
                snr_db=41.4,
                corrected=241391,
                uncorrectables=383321,
            ),
            DownstreamBondedChannelsRow(
                channel_id=4,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=405000000,
                power_dbmv=-10.1,
                snr_db=41.7,
                corrected=263079,
                uncorrectables=350594,
            ),
            DownstreamBondedChannelsRow(
                channel_id=5,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=411000000,
                power_dbmv=-9.9,
                snr_db=42.1,
                corrected=231458,
                uncorrectables=334754,
            ),
            DownstreamBondedChannelsRow(
                channel_id=6,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=417000000,
                power_dbmv=-9.6,
                snr_db=41.8,
                corrected=225216,
                uncorrectables=313119,
            ),
            DownstreamBondedChannelsRow(
                channel_id=7,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=423000000,
                power_dbmv=-9.4,
                snr_db=41.7,
                corrected=220859,
                uncorrectables=298511,
            ),
            DownstreamBondedChannelsRow(
                channel_id=8,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=429000000,
                power_dbmv=-9.5,
                snr_db=42.2,
                corrected=219215,
                uncorrectables=279809,
            ),
            DownstreamBondedChannelsRow(
                channel_id=9,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=435000000,
                power_dbmv=-9.8,
                snr_db=41.8,
                corrected=220279,
                uncorrectables=245579,
            ),
            DownstreamBondedChannelsRow(
                channel_id=10,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=441000000,
                power_dbmv=-10.1,
                snr_db=41.3,
                corrected=230568,
                uncorrectables=216911,
            ),
            DownstreamBondedChannelsRow(
                channel_id=11,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=447000000,
                power_dbmv=-10.0,
                snr_db=41.7,
                corrected=234409,
                uncorrectables=202251,
            ),
            DownstreamBondedChannelsRow(
                channel_id=12,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=453000000,
                power_dbmv=-9.6,
                snr_db=40.6,
                corrected=246251,
                uncorrectables=149073,
            ),
            DownstreamBondedChannelsRow(
                channel_id=13,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=459000000,
                power_dbmv=-9.2,
                snr_db=41.5,
                corrected=280736,
                uncorrectables=245801,
            ),
            DownstreamBondedChannelsRow(
                channel_id=14,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=465000000,
                power_dbmv=-9.3,
                snr_db=41.9,
                corrected=257639,
                uncorrectables=86973,
            ),
            DownstreamBondedChannelsRow(
                channel_id=15,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=471000000,
                power_dbmv=-9.7,
                snr_db=32.9,
                corrected=47502872,
                uncorrectables=294073,
            ),
            DownstreamBondedChannelsRow(
                channel_id=16,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=477000000,
                power_dbmv=-10.0,
                snr_db=30.1,
                corrected=172988432,
                uncorrectables=4285899,
            ),
            DownstreamBondedChannelsRow(
                channel_id=17,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=957000000,
                power_dbmv=-10.5,
                snr_db=39.7,
                corrected=10316,
                uncorrectables=7915,
            ),
            DownstreamBondedChannelsRow(
                channel_id=18,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=963000000,
                power_dbmv=-10.0,
                snr_db=40.0,
                corrected=5433,
                uncorrectables=5005,
            ),
            DownstreamBondedChannelsRow(
                channel_id=19,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=969000000,
                power_dbmv=-9.7,
                snr_db=40.1,
                corrected=4241,
                uncorrectables=3303,
            ),
            DownstreamBondedChannelsRow(
                channel_id=21,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=981000000,
                power_dbmv=-10.1,
                snr_db=39.4,
                corrected=5634,
                uncorrectables=2819,
            ),
            DownstreamBondedChannelsRow(
                channel_id=22,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=987000000,
                power_dbmv=-10.4,
                snr_db=39.2,
                corrected=6758,
                uncorrectables=3816,
            ),
            DownstreamBondedChannelsRow(
                channel_id=23,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=993000000,
                power_dbmv=-10.1,
                snr_db=39.4,
                corrected=6748,
                uncorrectables=5045,
            ),
            DownstreamBondedChannelsRow(
                channel_id=24,
                lock_status="Locked",
                modulation="QAM256",
                frequency_hz=999000000,
                power_dbmv=-10.3,
                snr_db=39.0,
                corrected=5326,
                uncorrectables=4669,
            ),
            DownstreamBondedChannelsRow(
                channel_id=193,
                lock_status="Locked",
                modulation="Other",
                frequency_hz=774000000,
                power_dbmv=-10.5,
                snr_db=17.8,
                corrected=1454959720,
                uncorrectables=2049372,
            ),
        ),
    ]
    assert metrics == expected_metrics
