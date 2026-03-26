from unittest.mock import mock_open, patch

from prometheus_client import REGISTRY

import main

HTML_100 = """
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
"""

HTML_150 = HTML_100.replace("<td>100</td>", "<td>150</td>").replace("<td>200</td>", "<td>250</td>")

LABELS = {"channel_id": "1"}


def scrape_with(html):
    with patch("builtins.open", mock_open(read_data=html)):
        main.scrape()


def setup_function():
    main._prev_corrected.clear()
    main._prev_uncorrectables.clear()


def test_gauges():
    scrape_with(HTML_100)
    assert REGISTRY.get_sample_value("downstream_frequency_hz", LABELS) == 387000000
    assert REGISTRY.get_sample_value("downstream_power_dbmv", LABELS) == -8.2
    assert REGISTRY.get_sample_value("downstream_snr_db", LABELS) == 43.5


def test_counter_first_scrape_is_zero():
    scrape_with(HTML_100)
    assert REGISTRY.get_sample_value("downstream_corrected_total", LABELS) == 0.0
    assert REGISTRY.get_sample_value("downstream_uncorrectables_total", LABELS) == 0.0


def test_counter_delta():
    scrape_with(HTML_100)
    before_corrected = REGISTRY.get_sample_value("downstream_corrected_total", LABELS)
    before_uncorrectables = REGISTRY.get_sample_value("downstream_uncorrectables_total", LABELS)

    scrape_with(HTML_150)
    assert REGISTRY.get_sample_value("downstream_corrected_total", LABELS) == before_corrected + 50
    assert REGISTRY.get_sample_value("downstream_uncorrectables_total", LABELS) == before_uncorrectables + 50
