from datetime import datetime

import server
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.metrics_core import Metric
from prometheus_client.parser import text_string_to_metric_families
from prometheus_client.samples import Sample

from tests.test_server import HTML, LABELS, _get_sample_value


def _metric(name, doc, typ, samples):
    m = Metric(name, doc, typ)
    m.samples = samples
    return m


def _sample(name, labels, value):
    return Sample(name, labels, value, None, None, None)


def test_generate_latest(
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
