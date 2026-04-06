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
        _metric(
            "surfboard_ssl_verify",
            "Whether SSL verification is enabled (1=enabled, 0=disabled)",
            "gauge",
            [
                _sample("surfboard_ssl_verify", {}, 1.0),
            ],
        ),
        _metric(
            "surfboard_scrape_success",
            "Whether the scrape was successful (1=success, 0=failure)",
            "gauge",
            [
                _sample("surfboard_scrape_success", {}, 1.0),
            ],
        ),
        _metric(
            "surfboard_system_time",
            "System time (Unix timestamp)",
            "gauge",
            [
                _sample("surfboard_system_time", {}, expected_system_time),
            ],
        ),
        _metric(
            "surfboard_upstream_frequency_hz",
            "Upstream channel frequency (Hz)",
            "gauge",
            [
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "1"}, 16400000.0
                ),
            ],
        ),
        _metric(
            "surfboard_upstream_width_hz",
            "Upstream channel width (Hz)",
            "gauge",
            [
                _sample("surfboard_upstream_width_hz", {"channel_id": "1"}, 6400000.0),
            ],
        ),
        _metric(
            "surfboard_upstream_power_dbmv",
            "Upstream power (dBmV)",
            "gauge",
            [
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "1"}, 46.0),
            ],
        ),
        _metric(
            "surfboard_downstream_frequency_hz",
            "Downstream channel frequency (Hz)",
            "gauge",
            [
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "1"},
                    387000000.0,
                ),
            ],
        ),
        _metric(
            "surfboard_downstream_power_dbmv",
            "Downstream power (dBmV)",
            "gauge",
            [
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "1"}, -8.2),
            ],
        ),
        _metric(
            "surfboard_downstream_snr_db",
            "Downstream SNR/MER (dB)",
            "gauge",
            [
                _sample("surfboard_downstream_snr_db", {"channel_id": "1"}, 43.5),
            ],
        ),
        _metric(
            "surfboard_downstream_corrected",
            "Downstream corrected codewords",
            "counter",
            [
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "1"}, 100.0
                ),
            ],
        ),
        _metric(
            "surfboard_downstream_uncorrectables",
            "Downstream uncorrectable codewords",
            "counter",
            [
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "1"},
                    200.0,
                ),
            ],
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
        _metric(
            "surfboard_ssl_verify",
            "Whether SSL verification is enabled (1=enabled, 0=disabled)",
            "gauge",
            [
                _sample("surfboard_ssl_verify", {}, 1.0),
            ],
        ),
        _metric(
            "surfboard_scrape_success",
            "Whether the scrape was successful (1=success, 0=failure)",
            "gauge",
            [
                _sample("surfboard_scrape_success", {}, 1.0),
            ],
        ),
        _metric(
            "surfboard_system_time",
            "System time (Unix timestamp)",
            "gauge",
            [
                _sample("surfboard_system_time", {}, expected_system_time),
            ],
        ),
        _metric(
            "surfboard_upstream_frequency_hz",
            "Upstream channel frequency (Hz)",
            "gauge",
            [
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "1"}, 16400000.0
                ),
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "2"}, 22800000.0
                ),
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "3"}, 29200000.0
                ),
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "4"}, 35600000.0
                ),
            ],
        ),
        _metric(
            "surfboard_upstream_width_hz",
            "Upstream channel width (Hz)",
            "gauge",
            [
                _sample("surfboard_upstream_width_hz", {"channel_id": "1"}, 6400000.0),
                _sample("surfboard_upstream_width_hz", {"channel_id": "2"}, 6400000.0),
                _sample("surfboard_upstream_width_hz", {"channel_id": "3"}, 6400000.0),
                _sample("surfboard_upstream_width_hz", {"channel_id": "4"}, 6400000.0),
            ],
        ),
        _metric(
            "surfboard_upstream_power_dbmv",
            "Upstream power (dBmV)",
            "gauge",
            [
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "1"}, 46.0),
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "2"}, 48.0),
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "3"}, 47.0),
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "4"}, 48.0),
            ],
        ),
        _metric(
            "surfboard_downstream_frequency_hz",
            "Downstream channel frequency (Hz)",
            "gauge",
            [
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "20"},
                    975000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "1"},
                    387000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "2"},
                    393000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "3"},
                    399000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "4"},
                    405000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "5"},
                    411000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "6"},
                    417000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "7"},
                    423000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "8"},
                    429000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "9"},
                    435000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "10"},
                    441000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "11"},
                    447000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "12"},
                    453000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "13"},
                    459000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "14"},
                    465000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "15"},
                    471000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "16"},
                    477000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "17"},
                    957000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "18"},
                    963000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "19"},
                    969000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "21"},
                    981000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "22"},
                    987000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "23"},
                    993000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "24"},
                    999000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "193"},
                    774000000.0,
                ),
            ],
        ),
        _metric(
            "surfboard_downstream_power_dbmv",
            "Downstream power (dBmV)",
            "gauge",
            [
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "20"}, -7.3),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "1"}, -8.2),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "2"}, -8.7),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "3"}, -9.3),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "4"}, -9.4),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "5"}, -9.2),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "6"}, -8.6),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "7"}, -8.3),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "8"}, -8.4),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "9"}, -8.9),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "10"}, -9.4),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "11"}, -9.3),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "12"}, -8.7),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "13"}, -8.1),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "14"}, -8.1),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "15"}, -8.6),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "16"}, -9.2),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "17"}, -8.3),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "18"}, -7.6),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "19"}, -7.2),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "21"}, -7.8),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "22"}, -8.1),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "23"}, -7.8),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "24"}, -7.7),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "193"}, -8.5),
            ],
        ),
        _metric(
            "surfboard_downstream_snr_db",
            "Downstream SNR/MER (dB)",
            "gauge",
            [
                _sample("surfboard_downstream_snr_db", {"channel_id": "20"}, 41.5),
                _sample("surfboard_downstream_snr_db", {"channel_id": "1"}, 43.5),
                _sample("surfboard_downstream_snr_db", {"channel_id": "2"}, 43.2),
                _sample("surfboard_downstream_snr_db", {"channel_id": "3"}, 42.0),
                _sample("surfboard_downstream_snr_db", {"channel_id": "4"}, 42.4),
                _sample("surfboard_downstream_snr_db", {"channel_id": "5"}, 42.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "6"}, 42.6),
                _sample("surfboard_downstream_snr_db", {"channel_id": "7"}, 42.8),
                _sample("surfboard_downstream_snr_db", {"channel_id": "8"}, 43.2),
                _sample("surfboard_downstream_snr_db", {"channel_id": "9"}, 42.6),
                _sample("surfboard_downstream_snr_db", {"channel_id": "10"}, 41.9),
                _sample("surfboard_downstream_snr_db", {"channel_id": "11"}, 42.4),
                _sample("surfboard_downstream_snr_db", {"channel_id": "12"}, 42.6),
                _sample("surfboard_downstream_snr_db", {"channel_id": "13"}, 42.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "14"}, 42.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "15"}, 30.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "16"}, 30.1),
                _sample("surfboard_downstream_snr_db", {"channel_id": "17"}, 41.4),
                _sample("surfboard_downstream_snr_db", {"channel_id": "18"}, 41.8),
                _sample("surfboard_downstream_snr_db", {"channel_id": "19"}, 41.9),
                _sample("surfboard_downstream_snr_db", {"channel_id": "21"}, 41.1),
                _sample("surfboard_downstream_snr_db", {"channel_id": "22"}, 41.0),
                _sample("surfboard_downstream_snr_db", {"channel_id": "23"}, 41.3),
                _sample("surfboard_downstream_snr_db", {"channel_id": "24"}, 41.0),
                _sample("surfboard_downstream_snr_db", {"channel_id": "193"}, 17.0),
            ],
        ),
        _metric(
            "surfboard_downstream_corrected",
            "Downstream corrected codewords",
            "counter",
            [
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "20"}, 3555.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "1"},
                    232263.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "2"}, 85776.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "3"},
                    230296.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "4"},
                    250661.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "5"},
                    222604.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "6"},
                    217616.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "7"},
                    213849.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "8"},
                    212308.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "9"},
                    214025.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "10"},
                    224305.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "11"},
                    228119.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "12"},
                    241083.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "13"},
                    271700.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "14"},
                    253546.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "15"},
                    46267820.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "16"},
                    172884998.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "17"}, 9685.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "18"}, 4931.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "19"}, 3862.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "21"}, 5133.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "22"}, 6155.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "23"}, 6073.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "24"}, 4859.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "193"},
                    1366671191.0,
                ),
            ],
        ),
        _metric(
            "surfboard_downstream_uncorrectables",
            "Downstream uncorrectable codewords",
            "counter",
            [
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "20"},
                    2096.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "1"},
                    375707.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "2"},
                    48483.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "3"},
                    378439.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "4"},
                    346300.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "5"},
                    330745.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "6"},
                    309869.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "7"},
                    295936.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "8"},
                    277445.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "9"},
                    243066.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "10"},
                    214273.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "11"},
                    199786.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "12"},
                    147333.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "13"},
                    232013.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "14"},
                    85992.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "15"},
                    292531.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "16"},
                    4283932.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "17"},
                    7806.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "18"},
                    4922.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "19"},
                    3265.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "21"},
                    2743.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "22"},
                    3719.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "23"},
                    5006.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "24"},
                    4586.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "193"},
                    1937019.0,
                ),
            ],
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
        _metric(
            "surfboard_ssl_verify",
            "Whether SSL verification is enabled (1=enabled, 0=disabled)",
            "gauge",
            [
                _sample("surfboard_ssl_verify", {}, 1.0),
            ],
        ),
        _metric(
            "surfboard_scrape_success",
            "Whether the scrape was successful (1=success, 0=failure)",
            "gauge",
            [
                _sample("surfboard_scrape_success", {}, 1.0),
            ],
        ),
        _metric(
            "surfboard_system_time",
            "System time (Unix timestamp)",
            "gauge",
            [
                _sample("surfboard_system_time", {}, expected_system_time),
            ],
        ),
        _metric(
            "surfboard_upstream_frequency_hz",
            "Upstream channel frequency (Hz)",
            "gauge",
            [
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "1"}, 16400000.0
                ),
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "2"}, 22800000.0
                ),
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "3"}, 29200000.0
                ),
                _sample(
                    "surfboard_upstream_frequency_hz", {"channel_id": "4"}, 35600000.0
                ),
            ],
        ),
        _metric(
            "surfboard_upstream_width_hz",
            "Upstream channel width (Hz)",
            "gauge",
            [
                _sample("surfboard_upstream_width_hz", {"channel_id": "1"}, 6400000.0),
                _sample("surfboard_upstream_width_hz", {"channel_id": "2"}, 6400000.0),
                _sample("surfboard_upstream_width_hz", {"channel_id": "3"}, 6400000.0),
                _sample("surfboard_upstream_width_hz", {"channel_id": "4"}, 6400000.0),
            ],
        ),
        _metric(
            "surfboard_upstream_power_dbmv",
            "Upstream power (dBmV)",
            "gauge",
            [
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "1"}, 46.0),
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "2"}, 47.0),
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "3"}, 46.0),
                _sample("surfboard_upstream_power_dbmv", {"channel_id": "4"}, 47.0),
            ],
        ),
        _metric(
            "surfboard_downstream_frequency_hz",
            "Downstream channel frequency (Hz)",
            "gauge",
            [
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "20"},
                    975000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "1"},
                    387000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "2"},
                    393000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "3"},
                    399000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "4"},
                    405000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "5"},
                    411000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "6"},
                    417000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "7"},
                    423000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "8"},
                    429000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "9"},
                    435000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "10"},
                    441000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "11"},
                    447000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "12"},
                    453000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "13"},
                    459000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "14"},
                    465000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "15"},
                    471000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "16"},
                    477000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "17"},
                    957000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "18"},
                    963000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "19"},
                    969000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "21"},
                    981000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "22"},
                    987000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "23"},
                    993000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "24"},
                    999000000.0,
                ),
                _sample(
                    "surfboard_downstream_frequency_hz",
                    {"channel_id": "193"},
                    774000000.0,
                ),
            ],
        ),
        _metric(
            "surfboard_downstream_power_dbmv",
            "Downstream power (dBmV)",
            "gauge",
            [
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "20"}, -9.7),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "1"}, -9.3),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "2"}, -9.6),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "3"}, -10.0),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "4"}, -10.1),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "5"}, -9.9),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "6"}, -9.6),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "7"}, -9.4),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "8"}, -9.5),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "9"}, -9.8),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "10"}, -10.1),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "11"}, -10.0),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "12"}, -9.6),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "13"}, -9.2),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "14"}, -9.3),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "15"}, -9.7),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "16"}, -10.0),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "17"}, -10.5),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "18"}, -10.0),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "19"}, -9.7),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "21"}, -10.1),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "22"}, -10.4),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "23"}, -10.1),
                _sample("surfboard_downstream_power_dbmv", {"channel_id": "24"}, -10.3),
                _sample(
                    "surfboard_downstream_power_dbmv", {"channel_id": "193"}, -10.5
                ),
            ],
        ),
        _metric(
            "surfboard_downstream_snr_db",
            "Downstream SNR/MER (dB)",
            "gauge",
            [
                _sample("surfboard_downstream_snr_db", {"channel_id": "20"}, 39.8),
                _sample("surfboard_downstream_snr_db", {"channel_id": "1"}, 42.5),
                _sample("surfboard_downstream_snr_db", {"channel_id": "2"}, 42.4),
                _sample("surfboard_downstream_snr_db", {"channel_id": "3"}, 41.4),
                _sample("surfboard_downstream_snr_db", {"channel_id": "4"}, 41.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "5"}, 42.1),
                _sample("surfboard_downstream_snr_db", {"channel_id": "6"}, 41.8),
                _sample("surfboard_downstream_snr_db", {"channel_id": "7"}, 41.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "8"}, 42.2),
                _sample("surfboard_downstream_snr_db", {"channel_id": "9"}, 41.8),
                _sample("surfboard_downstream_snr_db", {"channel_id": "10"}, 41.3),
                _sample("surfboard_downstream_snr_db", {"channel_id": "11"}, 41.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "12"}, 40.6),
                _sample("surfboard_downstream_snr_db", {"channel_id": "13"}, 41.5),
                _sample("surfboard_downstream_snr_db", {"channel_id": "14"}, 41.9),
                _sample("surfboard_downstream_snr_db", {"channel_id": "15"}, 32.9),
                _sample("surfboard_downstream_snr_db", {"channel_id": "16"}, 30.1),
                _sample("surfboard_downstream_snr_db", {"channel_id": "17"}, 39.7),
                _sample("surfboard_downstream_snr_db", {"channel_id": "18"}, 40.0),
                _sample("surfboard_downstream_snr_db", {"channel_id": "19"}, 40.1),
                _sample("surfboard_downstream_snr_db", {"channel_id": "21"}, 39.4),
                _sample("surfboard_downstream_snr_db", {"channel_id": "22"}, 39.2),
                _sample("surfboard_downstream_snr_db", {"channel_id": "23"}, 39.4),
                _sample("surfboard_downstream_snr_db", {"channel_id": "24"}, 39.0),
                _sample("surfboard_downstream_snr_db", {"channel_id": "193"}, 17.8),
            ],
        ),
        _metric(
            "surfboard_downstream_corrected",
            "Downstream corrected codewords",
            "counter",
            [
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "20"}, 4030.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "1"},
                    242830.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "2"}, 96209.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "3"},
                    241391.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "4"},
                    263079.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "5"},
                    231458.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "6"},
                    225216.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "7"},
                    220859.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "8"},
                    219215.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "9"},
                    220279.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "10"},
                    230568.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "11"},
                    234409.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "12"},
                    246251.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "13"},
                    280736.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "14"},
                    257639.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "15"},
                    47502872.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "16"},
                    172988432.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "17"},
                    10316.0,
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "18"}, 5433.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "19"}, 4241.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "21"}, 5634.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "22"}, 6758.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "23"}, 6748.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total", {"channel_id": "24"}, 5326.0
                ),
                _sample(
                    "surfboard_downstream_corrected_total",
                    {"channel_id": "193"},
                    1454959720.0,
                ),
            ],
        ),
        _metric(
            "surfboard_downstream_uncorrectables",
            "Downstream uncorrectable codewords",
            "counter",
            [
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "20"},
                    2127.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "1"},
                    380046.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "2"},
                    52921.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "3"},
                    383321.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "4"},
                    350594.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "5"},
                    334754.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "6"},
                    313119.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "7"},
                    298511.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "8"},
                    279809.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "9"},
                    245579.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "10"},
                    216911.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "11"},
                    202251.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "12"},
                    149073.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "13"},
                    245801.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "14"},
                    86973.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "15"},
                    294073.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "16"},
                    4285899.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "17"},
                    7915.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "18"},
                    5005.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "19"},
                    3303.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "21"},
                    2819.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "22"},
                    3816.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "23"},
                    5045.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "24"},
                    4669.0,
                ),
                _sample(
                    "surfboard_downstream_uncorrectables_total",
                    {"channel_id": "193"},
                    2049372.0,
                ),
            ],
        ),
    ]
    assert metrics == expected_metrics
