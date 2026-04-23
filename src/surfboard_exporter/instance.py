import functools
import os
import tempfile


@functools.cache
def instance_dir_get() -> str:
    prefix = f"surfboard_exporter.{os.getpid()}."
    return tempfile.mkdtemp(prefix=prefix)
