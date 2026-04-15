import math
from datetime import datetime
from unittest.mock import patch

import pytest

from collector import SurfboardCollector

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

HTML__BAD_TIME = HTML.replace("Thu Mar 26 14:58:02 2026", "not-a-date")
HTML__NO_TIME = HTML.replace(
    '<p id="systime">'
    "<strong>Current System Time:</strong> Thu Mar 26 14:58:02 2026"
    "</p>",
    "",
)

LABELS = {"channel_id": "1"}


def _get_sample(metrics, name, labels=None):
    label_items = (labels or {}).items()
    for metric in metrics:
        for sample in metric.samples:
            if sample.name == name and label_items <= sample.labels.items():
                return sample


def _get_sample_value(metrics, name, labels=None):
    sample = _get_sample(metrics, name, labels)
    if sample is not None:
        return sample.value


def collect_with(html):
    c = SurfboardCollector(username="user", password="pass")
    with patch("client.SurfboardClient.connection_status_get", return_value=html):
        return list(c.collect())


def test__system_time__static_html():
    metrics = collect_with(HTML)

    sample_value = _get_sample_value(metrics, "surfboard_system_time")
    assert sample_value == datetime(2026, 3, 26, 14, 58, 2).timestamp()


def test__system_time__missing_element__static_html__no_tome():
    metrics = collect_with(HTML__NO_TIME)

    assert math.isnan(_get_sample_value(metrics, "surfboard_system_time"))


def test__system_time__invalid_format__static_html_with_bad_time():
    metrics = collect_with(HTML__BAD_TIME)

    assert math.isnan(_get_sample_value(metrics, "surfboard_system_time"))


def test__downstream_gauges__static_html():
    metrics = collect_with(HTML)

    assert (
        _get_sample_value(metrics, "surfboard_downstream_frequency_hz", LABELS)
        == 387000000
    )
    assert _get_sample_value(metrics, "surfboard_downstream_power_dbmv", LABELS) == -8.2
    assert _get_sample_value(metrics, "surfboard_downstream_snr_db", LABELS) == 43.5


@pytest.mark.parametrize(
    ("lock_status", "expected_locked"),
    [("Locked", 1), ("Not Locked", 0), ("", 0), ("BOGUS", 0)],
)
def test__downstream_gauges__locked(
    lock_status,
    expected_locked,
    downstream_bonded_channels_factory,
    downstream_bonded_channels_row_factory,
):
    row = downstream_bonded_channels_row_factory.build(lock_status=lock_status)
    html = downstream_bonded_channels_factory.build(rows=[row]).to_html()

    metrics = collect_with(html)

    sample = _get_sample(
        metrics,
        "surfboard_downstream_locked",
        {"channel_id": str(row.channel_id)},
    )
    assert sample.labels["lock_status"] == lock_status
    assert sample.value == expected_locked


def test__upstream_gauges__static_html():
    metrics = collect_with(HTML)

    assert (
        _get_sample_value(metrics, "surfboard_upstream_frequency_hz", LABELS)
        == 16400000
    )
    assert _get_sample_value(metrics, "surfboard_upstream_width_hz", LABELS) == 6400000
    assert _get_sample_value(metrics, "surfboard_upstream_power_dbmv", LABELS) == 46.0


@pytest.mark.parametrize(
    ("lock_status", "expected_locked"),
    [("Locked", 1), ("Not Locked", 0), ("", 0), ("BOGUS", 0)],
)
def test__upstream_gauges__locked(
    lock_status,
    expected_locked,
    upstream_bonded_channels_factory,
    upstream_bonded_channels_row_factory,
):
    row = upstream_bonded_channels_row_factory.build(lock_status=lock_status)
    html = upstream_bonded_channels_factory.build(rows=[row]).to_html()

    metrics = collect_with(html)

    sample = _get_sample(
        metrics,
        "surfboard_upstream_locked",
        {"channel_id": str(row.channel_id)},
    )
    assert sample.labels["lock_status"] == lock_status
    assert sample.value == expected_locked


def test__downstream_counters__static_html():
    metrics = collect_with(HTML)

    corrected = _get_sample_value(
        metrics, "surfboard_downstream_corrected_total", LABELS
    )
    assert corrected == 100

    uncorrectables = _get_sample_value(
        metrics, "surfboard_downstream_uncorrectables_total", LABELS
    )
    assert uncorrectables == 200
