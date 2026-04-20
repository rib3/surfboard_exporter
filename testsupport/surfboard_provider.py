from collections import OrderedDict
from datetime import UTC, datetime

from faker.providers import BaseProvider

# DOCSIS downstream channels are 6 MHz wide.
# DOCSIS 3.0 downstream spectrum: 108 MHz to 1002 MHz.
# observed in captures: SC-QAM across 387-477 and 957-999 MHz; OFDM at 774 MHz.
_DOWNSTREAM__FREQUENCY__MHZ__MIN = 108
_DOWNSTREAM__FREQUENCY__MHZ__MAX = 1002
_DOWNSTREAM__FREQUENCY__MHZ__STEP = 6

# observed SC-QAM -10.8..-6.3 dBmV, OFDM -10.7..-8.5 dBmV; modems report 1 decimal.
# widen a little to exercise edge values while staying plausible.
_DOWNSTREAM__POWER_DBMV__MIN = -12.0
_DOWNSTREAM__POWER_DBMV__MAX = -5.0

# observed SC-QAM 29.6..44.0 dB, OFDM 10.2..21.2 dB; modems report 1 decimal.
# merged range covers both channel kinds.
_DOWNSTREAM__SNR_DB__MIN = 10.0
_DOWNSTREAM__SNR_DB__MAX = 45.0

# DOCSIS downstream error counters are 32-bit hardware registers.
# observed: corrected up to ~1.8e9 (OFDM), uncorrectables up to ~4.3e6 (SC-QAM).
# generate all the way to the hardware max to exercise large-counter code paths.
_DOWNSTREAM__CORRECTED__MAX = 2**32 - 1
# zero models freshly-reset counters / very clean channels
_DOWNSTREAM__CORRECTED__ZERO_PROBABILITY = 0.2

_DOWNSTREAM__UNCORRECTABLES__MAX = 2**32 - 1
# zero is common — healthy channels frequently report zero uncorrectables
_DOWNSTREAM__UNCORRECTABLES__ZERO_PROBABILITY = 0.4

# SB8200 supports 4 bonded upstream channels; observed 1..4 in captures.
_UPSTREAM__CHANNEL__MAX = 4

# channel_id is operator-assigned; captured values 1..4. DOCSIS 3.0 supports up to 8.
_UPSTREAM__CHANNEL_ID__MAX = 8

# DOCSIS 3.0 upstream spectrum: 5-85 MHz (sub-split); observed 16..36 MHz.
_UPSTREAM__FREQUENCY_HZ__MIN = 5_000_000
_UPSTREAM__FREQUENCY_HZ__MAX = 85_000_000

# observed 45.0..48.0 dBmV; DOCSIS upstream range roughly 17..55 dBmV.
# widened to exercise a broader plausible range in tests.
_UPSTREAM__POWER_DBMV__MIN = 35.0
_UPSTREAM__POWER_DBMV__MAX = 55.0


class SurfboardProvider(BaseProvider):
    def _random_int_zero_or_positive_max(
        self, zero_probability: float, max: int
    ) -> int:
        if self.generator.random.random() < zero_probability:
            return 0
        return self.generator.random_int(1, max)

    def date_time_utc(self, *args, **kwargs) -> datetime:
        if "tzinfo" in kwargs:
            raise TypeError("date_time_utc forces tzinfo=UTC; do not pass tzinfo")
        return self.generator.date_time(*args, tzinfo=UTC, **kwargs)

    def surfboard_connectivity_state(self) -> str:
        # real modems effectively always report "OK"; keep BOGUS rare but
        # non-zero so non-OK code paths still get exercised in batches.
        return self.generator.random_element(
            OrderedDict(
                [
                    ("OK", 0.9),  # observed: only value seen in captures
                    (
                        "BOGUS_TEST_VALUE",
                        0.1,
                    ),  # synthetic sentinel for non-OK paths
                ]
            )
        )

    def surfboard_downstream_channel_id(self) -> int:
        return self.generator.random_element([*range(1, 25), 193])

    def surfboard_downstream_corrected(self) -> int:
        return self._random_int_zero_or_positive_max(
            _DOWNSTREAM__CORRECTED__ZERO_PROBABILITY,
            _DOWNSTREAM__CORRECTED__MAX,
        )

    def surfboard_downstream_frequency_hz(self) -> int:
        step = _DOWNSTREAM__FREQUENCY__MHZ__STEP
        n = self.generator.random_int(
            _DOWNSTREAM__FREQUENCY__MHZ__MIN // step,
            _DOWNSTREAM__FREQUENCY__MHZ__MAX // step,
        )
        return n * step * 1_000_000

    def surfboard_downstream_lock_status(self) -> str:
        # real modems effectively always report "Locked"; keep BOGUS rare but
        # non-zero so non-Locked code paths still get exercised in batches.
        return self.generator.random_element(
            OrderedDict(
                [
                    ("Locked", 0.9),  # observed: only value seen in captures
                    (
                        "BOGUS_TEST_VALUE",
                        0.1,
                    ),  # synthetic sentinel for non-Locked paths
                ]
            )
        )

    def surfboard_downstream_modulation(self) -> str:
        return self.generator.random_element(
            [
                "QAM256",  # SC-QAM channels (ids 1..24)
                "Other",  # OFDM channel (id 193)
            ]
        )

    def surfboard_downstream_power_dbmv(self) -> float:
        value = self.generator.random.uniform(
            _DOWNSTREAM__POWER_DBMV__MIN, _DOWNSTREAM__POWER_DBMV__MAX
        )
        return round(value, 1)

    def surfboard_downstream_snr_db(self) -> float:
        value = self.generator.random.uniform(
            _DOWNSTREAM__SNR_DB__MIN, _DOWNSTREAM__SNR_DB__MAX
        )
        return round(value, 1)

    def surfboard_downstream_uncorrectables(self) -> int:
        return self._random_int_zero_or_positive_max(
            _DOWNSTREAM__UNCORRECTABLES__ZERO_PROBABILITY,
            _DOWNSTREAM__UNCORRECTABLES__MAX,
        )

    def surfboard_session_id(self) -> str:
        return self.generator.password(length=31, special_chars=False)

    def surfboard_token(self) -> str:
        return self.generator.password(length=31, special_chars=False)

    def surfboard_upstream_channel(self) -> int:
        return self.generator.random_int(1, _UPSTREAM__CHANNEL__MAX)

    def surfboard_upstream_channel_id(self) -> int:
        return self.generator.random_int(1, _UPSTREAM__CHANNEL_ID__MAX)

    def surfboard_upstream_channel_type(self) -> str:
        return self.generator.random_element(
            OrderedDict(
                [
                    # observed: only value seen in captures
                    ("SC-QAM Upstream", 0.7),
                    # DOCSIS 3.1 real value, but not observed in our captures —
                    # suffix flags it as unverified.
                    ("OFDMA Upstream (TEST MAYBE)", 0.2),
                    # synthetic sentinel; signals there may be other unobserved values.
                    ("BOGUS TEST Upstream", 0.1),
                ]
            )
        )

    def surfboard_upstream_frequency_hz(self) -> int:
        return self.generator.random_int(
            _UPSTREAM__FREQUENCY_HZ__MIN, _UPSTREAM__FREQUENCY_HZ__MAX
        )

    def surfboard_upstream_lock_status(self) -> str:
        # same pattern as downstream; real modems effectively always "Locked".
        return self.generator.random_element(
            OrderedDict(
                [
                    ("Locked", 0.9),  # observed: only value seen in captures
                    (
                        "BOGUS_TEST_VALUE",
                        0.1,
                    ),  # synthetic sentinel for non-Locked paths
                ]
            )
        )

    def surfboard_upstream_power_dbmv(self) -> float:
        value = self.generator.random.uniform(
            _UPSTREAM__POWER_DBMV__MIN, _UPSTREAM__POWER_DBMV__MAX
        )
        return round(value, 1)

    def surfboard_upstream_width_hz(self) -> int:
        # DOCSIS 3.0 SC-QAM widths: 1.6 / 3.2 / 6.4 MHz.
        return self.generator.random_element(
            OrderedDict(
                [
                    (6_400_000, 0.85),  # observed: only value seen in captures
                    (3_200_000, 0.15),  # realistic alternative for narrower channels
                ]
            )
        )
