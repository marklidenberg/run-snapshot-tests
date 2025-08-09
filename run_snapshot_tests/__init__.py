from importlib.metadata import version

try:
    __version__ = version("run-snapshot-tests")
except Exception:
    __version__ = "unknown"

from .run_snapshot_tests import run_snapshot_tests
