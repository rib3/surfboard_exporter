import pytest


@pytest.mark.repeat(10)
def test__no_args(connection_status_factory):
    page = connection_status_factory.build()

    assert page.system_time is not None
    assert page.system_time_str == page.system_time.strftime("%a %b %d %H:%M:%S %Y")


def test__system_time_str(connection_status_factory):
    page = connection_status_factory.build(system_time_str="not-a-date")

    assert page.system_time is None
    assert page.system_time_str == "not-a-date"


def test__system_time__none(connection_status_factory):
    with pytest.raises((ValueError, AttributeError)):
        connection_status_factory.build(system_time=None)


def test__system_time__none__system_time_str__none(connection_status_factory):
    with pytest.raises((ValueError, AttributeError)):
        connection_status_factory.build(system_time=None, system_time_str=None)


def test__system_time__system_time_str(connection_status_factory, mimesis):
    msg = "provide system_time or system_time_str, not both"
    with pytest.raises(ValueError, match=msg):
        connection_status_factory.build(
            system_time=mimesis("datetime.datetime"),
            system_time_str="not-a-date",
        )
