import os
import re
from pathlib import Path

from re_assert import Matches

from surfboard_exporter.instance import instance_dir_get, instance_file_create


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
