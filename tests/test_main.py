import math
from datetime import datetime
from unittest.mock import mock_open, patch

from prometheus_client import REGISTRY

import main

HTML = """
<table class="simpleTable">
<tbody>
<tr><th colspan="8"><strong>Downstream Bonded Channels</strong></th></tr>
<tr><td>Channel ID</td><td>Lock Status</td><td>Modulation</td><td>Frequency</td>
    <td>Power</td><td>SNR/MER</td><td>Corrected</td><td>Uncorrectables</td></tr>
<tr align="left">
  <td>1</td><td>Locked</td><td>QAM256</td><td>387000000 Hz</td>
  <td>-8.2 dBmV</td><td>43.5 dB</td><td>100</td><td>200</td>
</tr>
</tbody>
</table>
<table class="simpleTable">
<tbody>
<tr><th colspan="7"><strong>Upstream Bonded Channels</strong></th></tr>
<tr><td>Channel</td><td>Channel ID</td><td>Lock Status</td><td>US Channel Type</td>
    <td>Frequency</td><td>Width</td><td>Power</td></tr>
<tr align="left">
  <td>1</td><td>1</td><td>Locked</td><td>SC-QAM Upstream</td>
  <td>16400000 Hz</td><td>6400000 Hz</td><td>46.0 dBmV</td>
</tr>
</tbody>
</table>
<p id="systime"><strong>Current System Time:</strong> Thu Mar 26 14:58:02 2026</p>
"""

HTML_WITH_BAD_TIME = HTML.replace("Thu Mar 26 14:58:02 2026", "not-a-date")
HTML_NO_TIME = HTML.replace(
    '<p id="systime"><strong>Current System Time:</strong> Thu Mar 26 14:58:02 2026</p>',
    "",
)

HTML_150 = HTML.replace("<td>100</td>", "<td>150</td>").replace(
    "<td>200</td>", "<td>250</td>"
)

LABELS = {"channel_id": "1"}


def scrape_with(html):
    with patch("builtins.open", mock_open(read_data=html)):
        main.scrape()


def setup_function():
    main._prev_corrected.clear()
    main._prev_uncorrectables.clear()


def test_system_time():
    scrape_with(HTML)

    assert (
        REGISTRY.get_sample_value("surfboard_system_time")
        == datetime(2026, 3, 26, 14, 58, 2).timestamp()
    )


def test_system_time_missing_element():
    scrape_with(HTML_NO_TIME)
    assert math.isnan(REGISTRY.get_sample_value("surfboard_system_time"))


def test_system_time_invalid_format():
    scrape_with(HTML_WITH_BAD_TIME)
    assert math.isnan(REGISTRY.get_sample_value("surfboard_system_time"))


def test_downstream_gauges():
    scrape_with(HTML)

    assert (
        REGISTRY.get_sample_value("surfboard_downstream_frequency_hz", LABELS)
        == 387000000
    )
    assert REGISTRY.get_sample_value("surfboard_downstream_power_dbmv", LABELS) == -8.2
    assert REGISTRY.get_sample_value("surfboard_downstream_snr_db", LABELS) == 43.5


def test_upstream_gauges():
    scrape_with(HTML)

    assert (
        REGISTRY.get_sample_value("surfboard_upstream_frequency_hz", LABELS) == 16400000
    )
    assert REGISTRY.get_sample_value("surfboard_upstream_width_hz", LABELS) == 6400000
    assert REGISTRY.get_sample_value("surfboard_upstream_power_dbmv", LABELS) == 46.0


def test_counter_first_scrape_is_zero():
    scrape_with(HTML)

    assert (
        REGISTRY.get_sample_value("surfboard_downstream_corrected_total", LABELS) == 0.0
    )
    assert (
        REGISTRY.get_sample_value("surfboard_downstream_uncorrectables_total", LABELS)
        == 0.0
    )


def test_counter_delta():
    scrape_with(HTML)
    before_corrected = REGISTRY.get_sample_value(
        "surfboard_downstream_corrected_total", LABELS
    )
    before_uncorrectables = REGISTRY.get_sample_value(
        "surfboard_downstream_uncorrectables_total", LABELS
    )

    scrape_with(HTML_150)
    assert (
        REGISTRY.get_sample_value("surfboard_downstream_corrected_total", LABELS)
        == before_corrected + 50
    )
    assert (
        REGISTRY.get_sample_value("surfboard_downstream_uncorrectables_total", LABELS)
        == before_uncorrectables + 50
    )
