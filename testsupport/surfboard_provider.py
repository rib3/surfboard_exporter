from datetime import UTC, datetime

from faker.providers import BaseProvider


class SurfboardProvider(BaseProvider):
    def date_time_utc(self, *args, **kwargs) -> datetime:
        if "tzinfo" in kwargs:
            raise TypeError("date_time_utc forces tzinfo=UTC; do not pass tzinfo")
        return self.generator.date_time(*args, tzinfo=UTC, **kwargs)

    def surfboard_session_id(self) -> str:
        return self.generator.password(length=31, special_chars=False)

    def surfboard_token(self) -> str:
        return self.generator.password(length=31, special_chars=False)
