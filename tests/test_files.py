import logging
import os
import re
import tempfile
from pathlib import Path

import pytest
from re_assert import Matches

from surfboard_exporter.files import (
    instance_dir_get,
    instance_file_create,
    tempfile_config,
)
from surfboard_exporter.settings import Settings


def test__tempfile_config__instance_dir_already_cached(
    env_surfboard_password, monkeypatch, tmp_path
):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    settings = Settings()
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
    settings = Settings()

    tempfile_config(settings)

    assert tempfile.tempdir == str(other)
    expected_log_tuple = (
        "surfboard_exporter.files",
        logging.INFO,
        f"tempfile.tempdir={str(other)!r} (was {str(tmp_path)!r})",
    )
    assert expected_log_tuple in caplog.record_tuples


def test__instance_dir_get(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))

    result = instance_dir_get()

    expected = Matches(
        rf"{re.escape(str(tmp_path))}/surfboard_exporter\.{os.getpid()}\."
    )
    assert result == expected
    assert Path(result).is_dir()
    dirs = list(tmp_path.iterdir())
    assert dirs[0].name == Matches(rf"surfboard_exporter\.{os.getpid()}\.")
    assert str(dirs[0]) == expected


def test__instance_dir_get__once(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))

    result1 = instance_dir_get()
    result2 = instance_dir_get()

    assert result1 == result2
    dirs = list(tmp_path.iterdir())
    dirs[0]
    assert not dirs[1:]


def test__instance_file_create(tmp_path, monkeypatch):
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))
    prefix = "thing."

    with instance_file_create(prefix=prefix) as f:
        path = Path(f.name)

    assert path.parent == Path(instance_dir_get())
    assert path.name.startswith(prefix)
    assert path.is_file()
