import math
from datetime import datetime
from unittest.mock import patch

import server

HTML = """
<table class="simpleTable">
<tbody>
<tr><th colspan=8><strong>Downstream Bonded Channels</strong></th></tr>
      <td><strong>Channel ID</strong></td>
      <td><strong>Lock Status</strong></td>
      <td><strong>Modulation</strong></td>
      <td><strong>Frequency</strong></td>
      <td><strong>Power</strong></td>
      <td><strong>SNR/MER</strong></td>
      <td><strong>Corrected</strong></td>
      <td><strong>Uncorrectables</strong></td>
   </tr>
<tr align="left">
  <td>1</td><td>Locked</td><td>QAM256</td><td>387000000 Hz</td>
  <td>-8.2 dBmV</td><td>43.5 dB</td><td>100</td><td>200</td>
</tr>
</tbody>
</table>
<table class="simpleTable">
<tbody>
<tr><th colspan=7><strong>Upstream Bonded Channels</strong></th></tr>
      <td><strong>Channel</strong></td>
      <td><strong>Channel ID</strong></td>
      <td><strong>Lock Status</strong></td>
      <td><strong>US Channel Type</td>
      <td><strong>Frequency</strong></td>
      <td><strong>Width</strong></td>
      <td><strong>Power</strong></td>
   </tr>
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
    '<p id="systime">'
    "<strong>Current System Time:</strong> Thu Mar 26 14:58:02 2026"
    "</p>",
    "",
)

LABELS = {"channel_id": "1"}


def _get_sample_value(metrics, name, labels=None):
    for metric in metrics:
        for sample in metric.samples:
            if sample.name == name and (labels is None or sample.labels == labels):
                return sample.value
    return None


def collect_with(html):
    collector = server.SurfboardCollector("user", "pass")
    with patch("client.SurfboardClient.connection_status_get", return_value=html):
        return list(collector.collect())


def test__system_time():
    metrics = collect_with(HTML)

    assert (
        _get_sample_value(metrics, "surfboard_system_time")
        == datetime(2026, 3, 26, 14, 58, 2).timestamp()
    )


def test__system_time__missing_element():
    metrics = collect_with(HTML_NO_TIME)

    assert math.isnan(_get_sample_value(metrics, "surfboard_system_time"))


def test__system_time__invalid_format():
    metrics = collect_with(HTML_WITH_BAD_TIME)

    assert math.isnan(_get_sample_value(metrics, "surfboard_system_time"))


def test__downstream_gauges():
    metrics = collect_with(HTML)

    assert (
        _get_sample_value(metrics, "surfboard_downstream_frequency_hz", LABELS)
        == 387000000
    )
    assert _get_sample_value(metrics, "surfboard_downstream_power_dbmv", LABELS) == -8.2
    assert _get_sample_value(metrics, "surfboard_downstream_snr_db", LABELS) == 43.5


def test__upstream_gauges():
    metrics = collect_with(HTML)

    assert (
        _get_sample_value(metrics, "surfboard_upstream_frequency_hz", LABELS)
        == 16400000
    )
    assert _get_sample_value(metrics, "surfboard_upstream_width_hz", LABELS) == 6400000
    assert _get_sample_value(metrics, "surfboard_upstream_power_dbmv", LABELS) == 46.0


def test__downstream_counters():
    metrics = collect_with(HTML)

    assert (
        _get_sample_value(metrics, "surfboard_downstream_corrected_total", LABELS)
        == 100
    )
    assert (
        _get_sample_value(metrics, "surfboard_downstream_uncorrectables_total", LABELS)
        == 200
    )
