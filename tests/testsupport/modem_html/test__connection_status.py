from datetime import datetime

import pytest

from testsupport.modem_html import ConnectionStatus


def test__system_time__sets_system_time_str():
    dt = datetime(2026, 3, 26, 14, 58, 2)
    page = ConnectionStatus(system_time=dt)

    assert page.system_time_str == "Thu Mar 26 14:58:02 2026"


def test__system_time_str__sets_system_time_none():
    page = ConnectionStatus(system_time=None, system_time_str="not-a-date")

    assert page.system_time is None
    assert page.system_time_str == "not-a-date"


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
