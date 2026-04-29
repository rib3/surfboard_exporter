import logging
import math
from datetime import datetime

import pytest

from surfboard_exporter.parser import (
    parse_connectivity_state,
    parse_docsis_network_access,
    parse_downstream_channels,
    parse_security,
    parse_system_time,
    parse_upstream_channels,
)
from testsupport.modem_html import (
    DOWNSTREAM__BEGIN_TITLE_HEADERS,
    DOWNSTREAM__TABLE_BEGIN,
    DOWNSTREAM__TABLE_END,
    DOWNSTREAM__TITLE_ROW,
    STARTUP_PROCEDURE__BEGIN_TITLE_HEADERS,
    STARTUP_PROCEDURE__TABLE_BEGIN,
    STARTUP_PROCEDURE__TABLE_END,
    STARTUP_PROCEDURE__TITLE_ROW,
    UPSTREAM__BEGIN_TITLE_HEADERS,
    UPSTREAM__TABLE_BEGIN,
    UPSTREAM__TABLE_END,
    UPSTREAM__TITLE_ROW,
)

from .test_shared import assert_attrs, assert_attrs_list

HTML = f"""
{STARTUP_PROCEDURE__BEGIN_TITLE_HEADERS}
   <tr>
      <td>Connectivity State</td>
      <td>OK</td>
      <td>Operational</td>
   </tr>
   <tr>
      <td>Security</td>
      <td>Enabled</td>
      <td>BPI+</td>
   </tr>
   <tr>
      <td>DOCSIS Network Access Enabled</td>
      <td>Allowed</td>
      <td></td>
   </tr>
{STARTUP_PROCEDURE__TABLE_END}
{DOWNSTREAM__BEGIN_TITLE_HEADERS}
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
{DOWNSTREAM__TABLE_END}
{UPSTREAM__BEGIN_TITLE_HEADERS}
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
{UPSTREAM__TABLE_END}
<p id="systime"><strong>Current System Time:</strong> Thu Mar 26 14:58:02 2026</p>
"""


def _expected_system_time_from_dt(dt: datetime) -> float:
    return dt.replace(microsecond=0).timestamp()


def test__parse_system_time__static_html():
    assert parse_system_time(HTML) == datetime(2026, 3, 26, 14, 58, 2).timestamp()


def test__parse_system_time__factory(connection_status_factory):
    page = connection_status_factory.build()
    html = page.to_html()

    assert parse_system_time(html) == _expected_system_time_from_dt(page.system_time)


def test__parse_system_time__missing_element(caplog):
    html = "<html></html>"

    result = parse_system_time(html)

    assert math.isnan(result)
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        "systime tag not found",
    )
    assert expected_log in caplog.record_tuples


def test__parse_system_time__invalid_format(caplog, connection_status_factory):
    html = connection_status_factory.build(system_time_str="not-a-date").to_html()

    result = parse_system_time(html)

    assert math.isnan(result)
    expected_log = (
        "surfboard_exporter.parser",
        logging.ERROR,
        "failed to parse system time",
    )
    assert expected_log in caplog.record_tuples


def test__parse_connectivity_state__static_html():
    state = parse_connectivity_state(HTML)

    assert_attrs(
        state,
        ok=1.0,
        comment="Operational",
    )


@pytest.mark.parametrize(
    ("connectivity_state", "expected_ok"),
    [("OK", 1.0), ("Not Synchronized", 0.0), ("", 0.0), ("BOGUS", 0.0)],
)
def test__parse_connectivity_state__factory(
    connectivity_state,
    expected_ok,
    connection_status_factory,
    startup_procedure_factory,
):
    startup = startup_procedure_factory.build(connectivity_state=connectivity_state)
    html = connection_status_factory.build(startup=startup).to_html()

    state = parse_connectivity_state(html)

    assert_attrs(
        state,
        ok=expected_ok,
        comment=startup.connectivity_state_comment,
    )


def test__parse_connectivity_state__missing_table(caplog):
    html = "<html></html>"

    state = parse_connectivity_state(html)

    assert math.isnan(state.ok)
    assert state.comment == ""
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        "table with th content 'Startup Procedure' not found",
    )
    assert expected_log in caplog.record_tuples


def test__parse_connectivity_state__missing_row(caplog):
    html = (
        f"{STARTUP_PROCEDURE__TABLE_BEGIN}\n"
        f"{STARTUP_PROCEDURE__TITLE_ROW}\n"
        f"{STARTUP_PROCEDURE__TABLE_END}"
    )

    state = parse_connectivity_state(html)

    assert math.isnan(state.ok)
    assert state.comment == ""
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        f"Connectivity State row not found:\n{html!r}",
    )
    assert expected_log in caplog.record_tuples


def test__parse_security__static_html():
    security = parse_security(HTML)

    assert_attrs(
        security,
        enabled=1.0,
        comment="BPI+",
    )


@pytest.mark.parametrize(
    ("security", "expected_enabled"),
    [("Enabled", 1.0), ("Disabled", 0.0), ("", 0.0), ("BOGUS", 0.0)],
)
def test__parse_security__factory(
    security,
    expected_enabled,
    connection_status_factory,
    startup_procedure_factory,
):
    startup = startup_procedure_factory.build(security=security)
    html = connection_status_factory.build(startup=startup).to_html()

    parsed = parse_security(html)

    assert_attrs(
        parsed,
        enabled=expected_enabled,
        comment=startup.security_comment,
    )


def test__parse_security__missing_table(caplog):
    html = "<html></html>"

    security = parse_security(html)

    assert math.isnan(security.enabled)
    assert security.comment == ""
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        "table with th content 'Startup Procedure' not found",
    )
    assert expected_log in caplog.record_tuples


def test__parse_security__missing_row(caplog):
    html = (
        f"{STARTUP_PROCEDURE__TABLE_BEGIN}\n"
        f"{STARTUP_PROCEDURE__TITLE_ROW}\n"
        f"{STARTUP_PROCEDURE__TABLE_END}"
    )

    security = parse_security(html)

    assert math.isnan(security.enabled)
    assert security.comment == ""
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        f"Security row not found:\n{html!r}",
    )
    assert expected_log in caplog.record_tuples


def test__parse_docsis_network_access__static_html():
    docsis = parse_docsis_network_access(HTML)

    assert_attrs(
        docsis,
        allowed=1.0,
        comment="",
    )


@pytest.mark.parametrize(
    ("docsis_network_access_enabled", "expected_allowed"),
    [("Allowed", 1.0), ("Denied", 0.0), ("", 0.0), ("BOGUS", 0.0)],
)
def test__parse_docsis_network_access__factory(
    docsis_network_access_enabled,
    expected_allowed,
    connection_status_factory,
    startup_procedure_factory,
):
    startup = startup_procedure_factory.build(
        docsis_network_access_enabled=docsis_network_access_enabled
    )
    html = connection_status_factory.build(startup=startup).to_html()

    parsed = parse_docsis_network_access(html)

    assert_attrs(
        parsed,
        allowed=expected_allowed,
        comment=startup.docsis_network_access_enabled_comment,
    )


def test__parse_docsis_network_access__missing_table(caplog):
    html = "<html></html>"

    docsis = parse_docsis_network_access(html)

    assert math.isnan(docsis.allowed)
    assert docsis.comment == ""
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        "table with th content 'Startup Procedure' not found",
    )
    assert expected_log in caplog.record_tuples


def test__parse_docsis_network_access__missing_row(caplog):
    html = (
        f"{STARTUP_PROCEDURE__TABLE_BEGIN}\n"
        f"{STARTUP_PROCEDURE__TITLE_ROW}\n"
        f"{STARTUP_PROCEDURE__TABLE_END}"
    )

    docsis = parse_docsis_network_access(html)

    assert math.isnan(docsis.allowed)
    assert docsis.comment == ""
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        f"DOCSIS Network Access Enabled row not found:\n{html!r}",
    )
    assert expected_log in caplog.record_tuples


def test__parse_downstream_channels__fields__static_html():
    channels = parse_downstream_channels(HTML)

    assert_attrs_list(
        channels,
        dict(
            channel_id=1,
            lock_status="Locked",
            locked=True,
            modulation="QAM256",
            frequency_hz=387000000,
            power_dbmv=-8.2,
            snr_db=43.5,
            corrected=100,
            uncorrectables=200,
        ),
        dict(
            channel_id=2,
            lock_status="Locked",
            locked=True,
            modulation="QAM256",
            frequency_hz=393000000,
            power_dbmv=-9.1,
            snr_db=42.0,
            corrected=300,
            uncorrectables=400,
        ),
    )


def test__parse_downstream_channels__fields__factory(
    downstream_bonded_channels_factory,
    downstream_bonded_channels_row_factory,
):
    rows = downstream_bonded_channels_row_factory.batch(2)
    html = downstream_bonded_channels_factory.build(rows=rows).to_html()

    channels = parse_downstream_channels(html)

    expected_attrs_list = [
        dict(
            channel_id=row.channel_id,
            lock_status=row.lock_status,
            modulation=row.modulation,
            frequency_hz=row.frequency_hz,
            power_dbmv=row.power_dbmv,
            snr_db=row.snr_db,
            corrected=row.corrected,
            uncorrectables=row.uncorrectables,
        )
        for row in rows
    ]
    assert_attrs_list(channels, *expected_attrs_list)


@pytest.mark.parametrize("cell_count", [0, 7, 9])
def test__parse_downstream_channels__wrong_cell_count(cell_count, caplog):
    cells_html = "".join(f"<td>x{i}</td>" for i in range(cell_count))
    malformed_row = f"<tr>{cells_html}</tr>"
    html = (
        f"{DOWNSTREAM__TABLE_BEGIN}"
        f"{DOWNSTREAM__TITLE_ROW}"
        f"{malformed_row}"
        f"{DOWNSTREAM__TABLE_END}"
    )

    channels = parse_downstream_channels(html)

    assert not channels
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        f"skipping row, len(tds)={cell_count} != 8:\n{malformed_row!r}",
    )
    assert expected_log in caplog.record_tuples


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

    assert_attrs_list(
        channels,
        dict(
            lock_status=lock_status,
            locked=expected_locked,
        ),
    )


def test__parse_upstream_channels__fields__static_html():
    channels = parse_upstream_channels(HTML)

    assert_attrs_list(
        channels,
        dict(
            channel_id=1,
            lock_status="Locked",
            locked=True,
            channel_type="SC-QAM Upstream",
            frequency_hz=16400000,
            width_hz=6400000,
            power_dbmv=46.0,
        ),
        dict(
            channel_id=2,
            lock_status="Locked",
            locked=True,
            channel_type="SC-QAM Upstream",
            frequency_hz=22800000,
            width_hz=6400000,
            power_dbmv=48.0,
        ),
    )


def test__parse_upstream_channels__fields__factory(
    upstream_bonded_channels_factory,
    upstream_bonded_channels_row_factory,
):
    rows = upstream_bonded_channels_row_factory.batch(2)
    html = upstream_bonded_channels_factory.build(rows=rows).to_html()

    channels = parse_upstream_channels(html)

    expected_attrs_list = [
        dict(
            channel_id=row.channel_id,
            lock_status=row.lock_status,
            channel_type=row.channel_type,
            frequency_hz=row.frequency_hz,
            width_hz=row.width_hz,
            power_dbmv=row.power_dbmv,
        )
        for row in rows
    ]
    assert_attrs_list(channels, *expected_attrs_list)


@pytest.mark.parametrize("cell_count", [0, 6, 8])
def test__parse_upstream_channels__wrong_cell_count(cell_count, caplog):
    cells_html = "".join(f"<td>x{i}</td>" for i in range(cell_count))
    malformed_row = f"<tr>{cells_html}</tr>"
    html = (
        f"{UPSTREAM__TABLE_BEGIN}"
        f"{UPSTREAM__TITLE_ROW}"
        f"{malformed_row}"
        f"{UPSTREAM__TABLE_END}"
    )

    channels = parse_upstream_channels(html)

    assert not channels
    expected_log = (
        "surfboard_exporter.parser",
        logging.WARNING,
        f"skipping row, len(tds)={cell_count} != 7:\n{malformed_row!r}",
    )
    assert expected_log in caplog.record_tuples


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

    assert_attrs(
        channels[0],
        lock_status=lock_status,
        locked=expected_locked,
    )
