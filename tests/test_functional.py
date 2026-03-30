from datetime import datetime

import server
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.parser import text_string_to_metric_families

from tests.test_server import HTML, LABELS, _get_sample_value


def test_generate_latest(
    surfboard_api_mock_get_login, surfboard_api_mock_get_connectionstatus
):
    token = "abc123token"
    surfboard_api_mock_get_login(username="user", password="pass", token=token)
    surfboard_api_mock_get_connectionstatus(token=token, text=HTML)

    registry = CollectorRegistry()
    collector = server.SurfboardCollector("user", "pass")
    registry.register(collector)

    output = generate_latest(registry).decode("utf-8")

    metrics = list(text_string_to_metric_families(output))
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
