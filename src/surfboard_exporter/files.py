import functools
import logging
import os
import tempfile

from .settings import Settings

logger = logging.getLogger(__name__)


def tempfile_config(settings: Settings) -> None:
    if instance_dir_get.cache_info().currsize != 0:
        raise RuntimeError("tempfile_config must run before instance_dir_get is called")
    if settings.tmpdir is None:
        return
    tmpdir = str(settings.tmpdir)
    if tmpdir != tempfile.tempdir:
        logger.info("tempfile.tempdir=%r (was %r)", tmpdir, tempfile.tempdir)
        tempfile.tempdir = tmpdir


@functools.cache
def instance_dir_get() -> str:
    prefix = f"surfboard_exporter.{os.getpid()}."
    return tempfile.mkdtemp(prefix=prefix)


def instance_file_create(prefix: str):
    return tempfile.NamedTemporaryFile(
        prefix=prefix, delete=False, dir=instance_dir_get()
    )
