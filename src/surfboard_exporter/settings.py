import logging
from pathlib import Path

from pydantic import AliasChoices, Field, FilePath, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

DEFAULT__HOST = "0.0.0.0"
DEFAULT__PORT = 9779


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SURFBOARD_",
        env_file=".env",
        cli_parse_args=True,
        cli_kebab_case=True,
        cli_implicit_flags=True,
    )

    username: str = "admin"
    password: SecretStr | None = None
    password_file: Path | None = None
    modem_host: str = "192.168.100.1"
    modem_certificate_verify: bool = True
    modem_certificate_path: FilePath | None = None  # FilePath validates file exists

    listen_host: str = Field(DEFAULT__HOST, description="HTTP bind address")
    listen_port: int = Field(DEFAULT__PORT, description="HTTP port")
    log_file: bool = False
    response_save: bool = False
    tmpdir: Path | None = Field(
        default=None,
        # no SURFBOARD_ prefix; defer to python/OS TMPDIR convention
        validation_alias=AliasChoices("tmpdir", "TMPDIR"),
    )
    verbose: bool = Field(
        default=False,
        validation_alias=AliasChoices("v", "verbose"),
    )

    @model_validator(mode="after")
    def _tmpdir_expanduser(self) -> "Settings":
        if self.tmpdir is not None:
            self.tmpdir = self.tmpdir.expanduser()
        return self

    @model_validator(mode="after")
    def _password_file_load(self) -> "Settings":
        if self.password_file is not None:
            logger.info("loading password from %r", str(self.password_file))
            self.password = SecretStr(self.password_file.read_text().rstrip("\n"))
        return self

    @model_validator(mode="after")
    def _password_required(self) -> "Settings":
        if self.password is None:
            raise ValueError(
                "password required:"
                " SURFBOARD_PASSWORD/--password"
                " or SURFBOARD_PASSWORD_FILE/--password-file"
            )
        return self
