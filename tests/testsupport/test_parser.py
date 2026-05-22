import math

from testsupport.parser import expected_system_time_get


def test__expected_system_time_get(connection_status_factory, faker):
    dt = faker.date_time_utc()
    page = connection_status_factory.build(system_time=dt)

    result = expected_system_time_get(page)

    expected = dt.timestamp()
    assert result == expected


def test__expected_system_time_get__system_time__none(connection_status_factory):
    page = connection_status_factory.build(system_time_str="not-a-date")

    result = expected_system_time_get(page)

    assert math.isnan(result)
