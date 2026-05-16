import functools
import os
import tempfile


@functools.cache
def instance_dir_get() -> str:
    prefix = f"surfboard_exporter.{os.getpid()}."
    return tempfile.mkdtemp(prefix=prefix)


def instance_file_create(prefix: str):
    return tempfile.NamedTemporaryFile(
        prefix=prefix, delete=False, dir=instance_dir_get()
    )
