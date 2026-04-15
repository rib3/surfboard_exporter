from datetime import datetime

import pytest

from testsupport.modem_html import ConnectionStatus

from ...test_shared import assert_attrs


def test__system_time__sets_system_time_str():
    dt = datetime(2026, 3, 26, 14, 58, 2)
    page = ConnectionStatus(system_time=dt)

    assert page.system_time_str == "Thu Mar 26 14:58:02 2026"


def test__system_time_str__sets_system_time_none():
    page = ConnectionStatus(system_time=None, system_time_str="not-a-date")

    assert_attrs(
        page,
        system_time=None,
        system_time_str="not-a-date",
    )


def test__both__raises():
    msg = "provide system_time or system_time_str, not both"
    with pytest.raises(ValueError, match=msg):
        ConnectionStatus(
            system_time=datetime(2026, 3, 26, 14, 58, 2),
            system_time_str="not-a-date",
        )


def test__neither__raises():
    with pytest.raises(ValueError, match="provide system_time or system_time_str"):
        ConnectionStatus(system_time=None, system_time_str=None)


def test__to_html(connection_status_factory):
    page = connection_status_factory.build()

    html = page.to_html()

    expected_html = (
        f"{page.downstream.to_html()}\n"
        f"{page.upstream.to_html()}\n"
        f'<p id="systime">'
        f"<strong>Current System Time:</strong> {page.system_time_str}"
        f"</p>"
    )
    assert html == expected_html
