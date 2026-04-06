import math
from datetime import datetime

import pytest

from parser import (
    parse_downstream_channels,
    parse_system_time,
    parse_upstream_channels,
)

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
  <td>1</td>
  <td>Locked</td>
  <td>QAM256</td>
  <td>387000000 Hz</td>
  <td>-8.2 dBmV</td>
  <td>43.5 dB</td>
  <td>100</td>
  <td>200</td>
</tr>
<tr align="left">
  <td>2</td>
  <td>Locked</td>
  <td>QAM256</td>
  <td>393000000 Hz</td>
  <td>-9.1 dBmV</td>
  <td>42.0 dB</td>
  <td>300</td>
  <td>400</td>
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
  <td>1</td>
  <td>1</td>
  <td>Locked</td>
  <td>SC-QAM Upstream</td>
  <td>16400000 Hz</td>
  <td>6400000 Hz</td>
  <td>46.0 dBmV</td>
</tr>
<tr align="left">
  <td>2</td>
  <td>2</td>
  <td>Locked</td>
  <td>SC-QAM Upstream</td>
  <td>22800000 Hz</td>
  <td>6400000 Hz</td>
  <td>48.0 dBmV</td>
</tr>
</tbody>
</table>
<p id="systime"><strong>Current System Time:</strong> Thu Mar 26 14:58:02 2026</p>
"""


def test__upstream_channel_fields():
    channels = parse_upstream_channels(HTML)

    assert channels[0].channel_id == 1
    assert channels[0].lock_status == "Locked"
    assert channels[0].locked is True
    assert channels[0].channel_type == "SC-QAM Upstream"
    assert channels[0].frequency_hz == 16400000
    assert channels[0].width_hz == 6400000
    assert channels[0].power_dbmv == 46.0

    assert channels[1].channel_id == 2
    assert channels[1].lock_status == "Locked"
    assert channels[1].locked is True
    assert channels[1].channel_type == "SC-QAM Upstream"
    assert channels[1].frequency_hz == 22800000
    assert channels[1].width_hz == 6400000
    assert channels[1].power_dbmv == 48.0

    assert not channels[2:]


@pytest.mark.parametrize(
    ("lock_status", "expected_locked"),
    [("Locked", True), ("Not Locked", False), ("", False), ("BOGUS", False)],
)
def test__parse_upstream_channels__lock_status(
    lock_status,
    expected_locked,
    upstream_bonded_channels_factory,
    upstream_bonded_channels_row_factory,
):
    row = upstream_bonded_channels_row_factory.build(lock_status=lock_status)
    html = upstream_bonded_channels_factory.build(rows=[row]).to_html()

    channels = parse_upstream_channels(html)

    assert channels[0].lock_status == lock_status
    assert channels[0].locked is expected_locked


def test__parse_system_time():
    assert parse_system_time(HTML) == datetime(2026, 3, 26, 14, 58, 2).timestamp()


def test__parse_system_time__missing_element():
    assert math.isnan(parse_system_time("<html></html>"))


def test__parse_system_time__invalid_format():
    html = '<p id="systime">Current System Time: not-a-date</p>'

    assert math.isnan(parse_system_time(html))


def test__channel_fields():
    channels = parse_downstream_channels(HTML)

    assert channels[0].channel_id == 1
    assert channels[0].lock_status == "Locked"
    assert channels[0].locked is True
    assert channels[0].modulation == "QAM256"
    assert channels[0].frequency_hz == 387000000
    assert channels[0].power_dbmv == -8.2
    assert channels[0].snr_db == 43.5
    assert channels[0].corrected == 100
    assert channels[0].uncorrectables == 200

    assert channels[1].channel_id == 2
    assert channels[1].lock_status == "Locked"
    assert channels[1].locked is True
    assert channels[1].modulation == "QAM256"
    assert channels[1].frequency_hz == 393000000
    assert channels[1].power_dbmv == -9.1
    assert channels[1].snr_db == 42.0
    assert channels[1].corrected == 300
    assert channels[1].uncorrectables == 400

    assert not channels[2:]


@pytest.mark.parametrize(
    ("lock_status", "expected_locked"),
    [("Locked", True), ("Not Locked", False), ("", False), ("BOGUS", False)],
)
def test__parse_downstream_channels__lock_status(
    lock_status,
    expected_locked,
    downstream_bonded_channels_factory,
    downstream_bonded_channels_row_factory,
):
    row = downstream_bonded_channels_row_factory.build(lock_status=lock_status)
    html = downstream_bonded_channels_factory.build(rows=[row]).to_html()

    channels = parse_downstream_channels(html)

    assert channels[0].lock_status == lock_status
    assert channels[0].locked is expected_locked
