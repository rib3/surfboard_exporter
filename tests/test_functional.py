import re
from datetime import datetime

import pytest
from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.parser import text_string_to_metric_families

from surfboard_exporter.collector import SurfboardCollector
from testdata import CONNECTION_STATUSES
from tests.test_collector import HTML, LABELS, _get_sample_value
from testsupport.metrics import (
    _metric_connectivity_state_ok_sample,
    _metric_docsis_network_access_allowed_sample,
    _metric_scrape_success_sample,
    _metric_security_enabled_sample,
    _metric_ssl_verify_sample,
    _metric_system_time_sample,
    _metrics_downstream,
    _metrics_upstream,
    expected_metrics_get,
)
from testsupport.modem_html import (
    DownstreamBondedChannelsRow,
    UpstreamBondedChannelsRow,
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


def test__init__modem_certificate_file__does_not_exist(tmp_path):
    missing = tmp_path / "missing.crt"
    expected = f"modem_certificate_file={str(missing)!r} does not exist"

    with pytest.raises(FileNotFoundError, match=f"^{re.escape(expected)}$"):
        SurfboardCollector(password="pass", modem_certificate_file=missing)


@pytest.mark.parametrize(
    ("collector_kwargs", "expected_username"),
    [
        ({}, "admin"),
        ({"username": "user"}, "user"),
    ],
)
def test__generate_latest(
    surfboard_api__mock__login__get,
    surfboard_api__mock__connectionstatus__get,
    collector_kwargs,
    expected_username,
):
    token = "abc123token"
    surfboard_api__mock__login__get(
        username=expected_username, password="pass", token=token
    )
    surfboard_api__mock__connectionstatus__get(token=token, text=HTML)

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
def test__generate_latest__ssl_verify__enabled__certificate_file__none(
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
    https_server_modem__expect_ordered_request__login__get,
    https_server_modem__expect_ordered_request__connectionstatus__get,
):
    _, token = https_server_modem__expect_ordered_request__login__get(
        username="user", password="pass"
    )
    https_server_modem__expect_ordered_request__connectionstatus__get(token=token)

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


@pytest.mark.parametrize("connection_status", CONNECTION_STATUSES)
def test__generate_latest__real_html(
    connection_status,
    surfboard_api__mock__login__get,
    surfboard_api__mock__connectionstatus__get,
):
    token = "abc123token"
    surfboard_api__mock__login__get(password="pass", token=token)
    surfboard_api__mock__connectionstatus__get(
        token=token, text=connection_status.html_raw
    )

    registry = CollectorRegistry()
    collector = SurfboardCollector(password="pass")
    registry.register(collector)

    output = generate_latest(registry)

    metrics = list(text_string_to_metric_families(output.decode("utf-8")))
    expected_metrics = expected_metrics_get(connection_status)
    assert metrics == expected_metrics
