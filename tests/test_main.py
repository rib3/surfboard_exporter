import logging
import tempfile

import pytest

from surfboard_exporter.instance import instance_dir_get
from surfboard_exporter.main import tempfile_config
from surfboard_exporter.settings import Settings

logger = logging.getLogger(__name__)


def test__tempfile_config__instance_dir_already_cached(
    env_surfboard_password, monkeypatch, tmp_path
):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    settings = Settings(_cli_parse_args=[])
    instance_dir_get()

    with pytest.raises(RuntimeError, match="tempfile_config must run before"):
        tempfile_config(settings)


def test__tempfile_config__tmpdir(
    caplog, env_surfboard_password, monkeypatch, tmp_path
):
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    monkeypatch.setenv("TMPDIR", str(other))
    settings = Settings(_cli_parse_args=[])

    tempfile_config(settings)

    assert tempfile.tempdir == str(other)
    expected_log_tuple = (
        "surfboard_exporter.main",
        logging.INFO,
        f"tempfile.tempdir={str(other)!r} (was {str(tmp_path)!r})",
    )
    assert expected_log_tuple in caplog.record_tuples
