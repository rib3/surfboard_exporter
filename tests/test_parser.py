from parser import parse_downstream_channels


HTML = """
<table class="simpleTable">
<tbody>
<tr><th colspan="8"><strong>Downstream Bonded Channels</strong></th></tr>
<tr>
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
"""


def test_channel_fields():
    channels = parse_downstream_channels(HTML)

    assert channels[0].channel_id == 1
    assert channels[0].lock_status == "Locked"
    assert channels[0].modulation == "QAM256"
    assert channels[0].frequency_hz == 387000000
    assert channels[0].power_dbmv == -8.2
    assert channels[0].snr_db == 43.5
    assert channels[0].corrected == 100
    assert channels[0].uncorrectables == 200

    assert channels[1].channel_id == 2
    assert channels[1].lock_status == "Locked"
    assert channels[1].modulation == "QAM256"
    assert channels[1].frequency_hz == 393000000
    assert channels[1].power_dbmv == -9.1
    assert channels[1].snr_db == 42.0
    assert channels[1].corrected == 300
    assert channels[1].uncorrectables == 400

    assert not channels[2:]
