from datetime import UTC, datetime

import pytest


def test__date_time_utc(faker):
    result = faker.date_time_utc()

    assert result.tzinfo == UTC


def test__date_time_utc__end_datetime__passthrough(faker):
    end = datetime(2020, 1, 1, tzinfo=UTC)

    result = faker.date_time_utc(end_datetime=end)

    assert result <= end
    assert result.tzinfo == UTC


def test__date_time_utc__tzinfo__raises(faker):
    with pytest.raises(TypeError, match="date_time_utc forces tzinfo=UTC"):
        faker.date_time_utc(tzinfo=UTC)


def test__surfboard_session_id(faker):
    result = faker.surfboard_session_id()

    assert len(result) == 31
    assert result.isalnum()


def test__surfboard_token(faker):
    result = faker.surfboard_token()

    assert len(result) == 31
    assert result.isalnum()
