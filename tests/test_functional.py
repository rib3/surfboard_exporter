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
        _metric_upstream_frequency_hz({"1": 16400000.0}),
        _metric_upstream_width_hz({"1": 6400000.0}),
        _metric_upstream_power_dbmv({"1": 46.0}),
        _metric_downstream_frequency_hz({"1": 387000000.0}),
        _metric_downstream_power_dbmv({"1": -8.2}),
        _metric_downstream_snr_db({"1": 43.5}),
        _metric_downstream_corrected({"1": 100.0}),
        _metric_downstream_uncorrectables({"1": 200.0}),
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
        _metric_upstream_frequency_hz(
            {
                "1": 16400000.0,
                "2": 22800000.0,
                "3": 29200000.0,
                "4": 35600000.0,
            }
        ),
        _metric_upstream_width_hz(
            {
                "1": 6400000.0,
                "2": 6400000.0,
                "3": 6400000.0,
                "4": 6400000.0,
            }
        ),
        _metric_upstream_power_dbmv(
            {
                "1": 46.0,
                "2": 48.0,
                "3": 47.0,
                "4": 48.0,
            }
        ),
        _metric_downstream_frequency_hz(
            {
                "20": 975000000.0,
                "1": 387000000.0,
                "2": 393000000.0,
                "3": 399000000.0,
                "4": 405000000.0,
                "5": 411000000.0,
                "6": 417000000.0,
                "7": 423000000.0,
                "8": 429000000.0,
                "9": 435000000.0,
                "10": 441000000.0,
                "11": 447000000.0,
                "12": 453000000.0,
                "13": 459000000.0,
                "14": 465000000.0,
                "15": 471000000.0,
                "16": 477000000.0,
                "17": 957000000.0,
                "18": 963000000.0,
                "19": 969000000.0,
                "21": 981000000.0,
                "22": 987000000.0,
                "23": 993000000.0,
                "24": 999000000.0,
                "193": 774000000.0,
            }
        ),
        _metric_downstream_power_dbmv(
            {
                "20": -7.3,
                "1": -8.2,
                "2": -8.7,
                "3": -9.3,
                "4": -9.4,
                "5": -9.2,
                "6": -8.6,
                "7": -8.3,
                "8": -8.4,
                "9": -8.9,
                "10": -9.4,
                "11": -9.3,
                "12": -8.7,
                "13": -8.1,
                "14": -8.1,
                "15": -8.6,
                "16": -9.2,
                "17": -8.3,
                "18": -7.6,
                "19": -7.2,
                "21": -7.8,
                "22": -8.1,
                "23": -7.8,
                "24": -7.7,
                "193": -8.5,
            }
        ),
        _metric_downstream_snr_db(
            {
                "20": 41.5,
                "1": 43.5,
                "2": 43.2,
                "3": 42.0,
                "4": 42.4,
                "5": 42.7,
                "6": 42.6,
                "7": 42.8,
                "8": 43.2,
                "9": 42.6,
                "10": 41.9,
                "11": 42.4,
                "12": 42.6,
                "13": 42.7,
                "14": 42.7,
                "15": 30.7,
                "16": 30.1,
                "17": 41.4,
                "18": 41.8,
                "19": 41.9,
                "21": 41.1,
                "22": 41.0,
                "23": 41.3,
                "24": 41.0,
                "193": 17.0,
            }
        ),
        _metric_downstream_corrected(
            {
                "20": 3555.0,
                "1": 232263.0,
                "2": 85776.0,
                "3": 230296.0,
                "4": 250661.0,
                "5": 222604.0,
                "6": 217616.0,
                "7": 213849.0,
                "8": 212308.0,
                "9": 214025.0,
                "10": 224305.0,
                "11": 228119.0,
                "12": 241083.0,
                "13": 271700.0,
                "14": 253546.0,
                "15": 46267820.0,
                "16": 172884998.0,
                "17": 9685.0,
                "18": 4931.0,
                "19": 3862.0,
                "21": 5133.0,
                "22": 6155.0,
                "23": 6073.0,
                "24": 4859.0,
                "193": 1366671191.0,
            }
        ),
        _metric_downstream_uncorrectables(
            {
                "20": 2096.0,
                "1": 375707.0,
                "2": 48483.0,
                "3": 378439.0,
                "4": 346300.0,
                "5": 330745.0,
                "6": 309869.0,
                "7": 295936.0,
                "8": 277445.0,
                "9": 243066.0,
                "10": 214273.0,
                "11": 199786.0,
                "12": 147333.0,
                "13": 232013.0,
                "14": 85992.0,
                "15": 292531.0,
                "16": 4283932.0,
                "17": 7806.0,
                "18": 4922.0,
                "19": 3265.0,
                "21": 2743.0,
                "22": 3719.0,
                "23": 5006.0,
                "24": 4586.0,
                "193": 1937019.0,
            }
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
        _metric_upstream_frequency_hz(
            {
                "1": 16400000.0,
                "2": 22800000.0,
                "3": 29200000.0,
                "4": 35600000.0,
            }
        ),
        _metric_upstream_width_hz(
            {
                "1": 6400000.0,
                "2": 6400000.0,
                "3": 6400000.0,
                "4": 6400000.0,
            }
        ),
        _metric_upstream_power_dbmv(
            {
                "1": 46.0,
                "2": 47.0,
                "3": 46.0,
                "4": 47.0,
            }
        ),
        _metric_downstream_frequency_hz(
            {
                "20": 975000000.0,
                "1": 387000000.0,
                "2": 393000000.0,
                "3": 399000000.0,
                "4": 405000000.0,
                "5": 411000000.0,
                "6": 417000000.0,
                "7": 423000000.0,
                "8": 429000000.0,
                "9": 435000000.0,
                "10": 441000000.0,
                "11": 447000000.0,
                "12": 453000000.0,
                "13": 459000000.0,
                "14": 465000000.0,
                "15": 471000000.0,
                "16": 477000000.0,
                "17": 957000000.0,
                "18": 963000000.0,
                "19": 969000000.0,
                "21": 981000000.0,
                "22": 987000000.0,
                "23": 993000000.0,
                "24": 999000000.0,
                "193": 774000000.0,
            }
        ),
        _metric_downstream_power_dbmv(
            {
                "20": -9.7,
                "1": -9.3,
                "2": -9.6,
                "3": -10.0,
                "4": -10.1,
                "5": -9.9,
                "6": -9.6,
                "7": -9.4,
                "8": -9.5,
                "9": -9.8,
                "10": -10.1,
                "11": -10.0,
                "12": -9.6,
                "13": -9.2,
                "14": -9.3,
                "15": -9.7,
                "16": -10.0,
                "17": -10.5,
                "18": -10.0,
                "19": -9.7,
                "21": -10.1,
                "22": -10.4,
                "23": -10.1,
                "24": -10.3,
                "193": -10.5,
            }
        ),
        _metric_downstream_snr_db(
            {
                "20": 39.8,
                "1": 42.5,
                "2": 42.4,
                "3": 41.4,
                "4": 41.7,
                "5": 42.1,
                "6": 41.8,
                "7": 41.7,
                "8": 42.2,
                "9": 41.8,
                "10": 41.3,
                "11": 41.7,
                "12": 40.6,
                "13": 41.5,
                "14": 41.9,
                "15": 32.9,
                "16": 30.1,
                "17": 39.7,
                "18": 40.0,
                "19": 40.1,
                "21": 39.4,
                "22": 39.2,
                "23": 39.4,
                "24": 39.0,
                "193": 17.8,
            }
        ),
        _metric_downstream_corrected(
            {
                "20": 4030.0,
                "1": 242830.0,
                "2": 96209.0,
                "3": 241391.0,
                "4": 263079.0,
                "5": 231458.0,
                "6": 225216.0,
                "7": 220859.0,
                "8": 219215.0,
                "9": 220279.0,
                "10": 230568.0,
                "11": 234409.0,
                "12": 246251.0,
                "13": 280736.0,
                "14": 257639.0,
                "15": 47502872.0,
                "16": 172988432.0,
                "17": 10316.0,
                "18": 5433.0,
                "19": 4241.0,
                "21": 5634.0,
                "22": 6758.0,
                "23": 6748.0,
                "24": 5326.0,
                "193": 1454959720.0,
            }
        ),
        _metric_downstream_uncorrectables(
            {
                "20": 2127.0,
                "1": 380046.0,
                "2": 52921.0,
                "3": 383321.0,
                "4": 350594.0,
                "5": 334754.0,
                "6": 313119.0,
                "7": 298511.0,
                "8": 279809.0,
                "9": 245579.0,
                "10": 216911.0,
                "11": 202251.0,
                "12": 149073.0,
                "13": 245801.0,
                "14": 86973.0,
                "15": 294073.0,
                "16": 4285899.0,
                "17": 7915.0,
                "18": 5005.0,
                "19": 3303.0,
                "21": 2819.0,
                "22": 3816.0,
                "23": 5045.0,
                "24": 4669.0,
                "193": 2049372.0,
            }
        ),
    ]
    assert metrics == expected_metrics
