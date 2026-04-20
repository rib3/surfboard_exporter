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


@pytest.mark.repeat(20)
def test__surfboard_connectivity_state(faker):
    result = faker.surfboard_connectivity_state()

    assert result in {"OK", "BOGUS_TEST_VALUE"}


@pytest.mark.repeat(20)
def test__surfboard_downstream_corrected(faker):
    result = faker.surfboard_downstream_corrected()

    assert isinstance(result, int)
    assert 0 <= result <= 2**32 - 1


@pytest.mark.repeat(20)
def test__surfboard_downstream_frequency_hz(faker):
    result = faker.surfboard_downstream_frequency_hz()

    assert isinstance(result, int)
    assert 108_000_000 <= result <= 1_002_000_000
    assert result % 6_000_000 == 0


@pytest.mark.repeat(20)
def test__surfboard_downstream_lock_status(faker):
    result = faker.surfboard_downstream_lock_status()

    assert result in {"Locked", "BOGUS_TEST_VALUE"}


@pytest.mark.repeat(20)
def test__surfboard_downstream_modulation(faker):
    result = faker.surfboard_downstream_modulation()

    assert result in {"QAM256", "Other"}


@pytest.mark.repeat(20)
def test__surfboard_downstream_power_dbmv(faker):
    result = faker.surfboard_downstream_power_dbmv()

    assert isinstance(result, float)
    assert -12.0 <= result <= -5.0
    assert round(result, 1) == result


@pytest.mark.repeat(20)
def test__surfboard_downstream_snr_db(faker):
    result = faker.surfboard_downstream_snr_db()

    assert isinstance(result, float)
    assert 10.0 <= result <= 45.0
    assert round(result, 1) == result


@pytest.mark.repeat(20)
def test__surfboard_downstream_uncorrectables(faker):
    result = faker.surfboard_downstream_uncorrectables()

    assert isinstance(result, int)
    assert 0 <= result <= 2**32 - 1


@pytest.mark.repeat(20)
def test__surfboard_upstream_channel(faker):
    result = faker.surfboard_upstream_channel()

    assert isinstance(result, int)
    assert 1 <= result <= 4


@pytest.mark.repeat(20)
def test__surfboard_upstream_channel_id(faker):
    result = faker.surfboard_upstream_channel_id()

    assert isinstance(result, int)
    assert 1 <= result <= 8


@pytest.mark.repeat(20)
def test__surfboard_upstream_channel_type(faker):
    result = faker.surfboard_upstream_channel_type()

    assert result in {
        "SC-QAM Upstream",
        "OFDMA Upstream (TEST MAYBE)",
        "BOGUS TEST Upstream",
    }


@pytest.mark.repeat(20)
def test__surfboard_upstream_frequency_hz(faker):
    result = faker.surfboard_upstream_frequency_hz()

    assert isinstance(result, int)
    assert 5_000_000 <= result <= 85_000_000


@pytest.mark.repeat(20)
def test__surfboard_upstream_lock_status(faker):
    result = faker.surfboard_upstream_lock_status()

    assert result in {"Locked", "BOGUS_TEST_VALUE"}


@pytest.mark.repeat(20)
def test__surfboard_upstream_power_dbmv(faker):
    result = faker.surfboard_upstream_power_dbmv()

    assert isinstance(result, float)
    assert 35.0 <= result <= 55.0
    assert round(result, 1) == result


@pytest.mark.repeat(20)
def test__surfboard_upstream_width_hz(faker):
    result = faker.surfboard_upstream_width_hz()

    assert result in {3_200_000, 6_400_000}


def test__surfboard_session_id(faker):
    result = faker.surfboard_session_id()

    assert len(result) == 31
    assert result.isalnum()


def test__surfboard_token(faker):
    result = faker.surfboard_token()

    assert len(result) == 31
    assert result.isalnum()
