import logging
import os
import sys
from typing import Any, Literal, Optional, Union

import pytest

import inspect

from inspect import FrameInfo
from pathlib import Path
import inline_snapshot
from run_snapshot_tests.fixed_format_code import fixed_format_code
from run_snapshot_tests.fixed_snapshot import fixed_snapshot

# - Plugin class


class SnapshotTestPlugin:
    """Plugin to customize pytest output for snapshot tests."""

    def pytest_report_teststatus(self, report):
        """Override the default test status reporting to prevent any output."""
        if report.passed and report.when == "call":
            return ("Passed", None, None)

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(self, node, call, report):
        if report.failed:
            # - Get report output

            traceback = str(call.excinfo.getrepr(style="short"))

            # - Find first line starting with test name and crop to it

            test_name = report.location[-1]
            lines = traceback.split("\n")
            line_with_test_name = [line for line in lines if test_name in line][0]
            traceback = "\n".join(lines[lines.index(line_with_test_name) :])

            # - Print cropped traceback

            print("\n" + traceback, file=sys.stderr)

    def pytest_sessionstart(self, session):
        # - Get terminal reporter

        terminal_reporter = session.config.pluginmanager.getplugin("terminalreporter")

        # - Monkey patch the write method of the terminal reporter to prevent any output

        original_write = terminal_reporter._tw.write

        def custom_write(s, **kwargs):
            if "::" in s and not s.startswith("FAILED"):  # test names
                original_write("-" * 80 + "\n[" + s.strip() + "]\n", **kwargs)

        terminal_reporter._tw.write = custom_write


# - Dependent utils


# todo later: use file-primitives when ready
def read_file(
    path: Union[str, Path],
    default: Any = ...,  # if file does not exist
) -> str:
    """A simple file reader helper, as it should have been in the first place. Useful for one-liners and nested function calls."""

    # - Check if file exists

    if not os.path.exists(path) and default is not Ellipsis:
        return default

    # - Read file

    with open(str(path), "r") as file:
        return file.read()


def write_file(
    data: str,
    path: Union[str, Path],
) -> None:
    """A simple file writer helper, as it should have been in the first place. Useful for one-liners or nested function calls."""

    # - Ensure path

    os.makedirs(os.path.dirname(os.path.abspath(str(path))), exist_ok=True)

    # - Write file

    with open(str(path), "w") as file:
        file.write(data)


def get_frame_path(
    frame_num: int,  # 0 - current frame, 1 - parent frame, ...
) -> Path:
    """Get the path of the frame that called this function. Useful to get caller's path."""

    # - Get the current frame

    current_frame = inspect.currentframe()

    # - Get the frame

    caller_frame: FrameInfo = inspect.getouterframes(current_frame)[frame_num + 1]

    # - Extract the file name from the frame

    return Path(caller_frame.filename)


def get_parent_frame_path():
    return get_frame_path(frame_num=2)


def run_snapshot_tests(
    path: Union[str, Path, None] = None,
    mode: Literal[
        "assert", "create_missing", "fix_broken", "update_all"
    ] = "create_missing",
    python_functions: Optional[str] = None,
) -> None:
    """Run test with inline snapshots.

    A helper over inline-snapshot library with better interface + prettier logs.

    Parameters
    ----------
    path : str, optional
        Path to the file to run tests from. If not provided, the current file is used.
    python_functions : str, optional
        Space-separated globs for function name patterns to collect as tests.
        Default is "test_*". Example: "test_* example_*" to collect both test_ and example_ functions.
    """

    # - Monkey patch inline_snapshot.snapshot

    inline_snapshot.snapshot.func.__code__ = fixed_snapshot.func.__code__  # type: ignore[attr-defined]
    inline_snapshot._format.format_code.__code__ = fixed_format_code.__code__  # type: ignore[attr-defined]

    # - Send warning if inline_snapshot version is not tested

    if inline_snapshot.__version__ != "0.8.0":
        logging.warning(
            f"inline_snapshot version is not supported: {inline_snapshot.__version__}. The only supported version for now is 0.8.0"
        )

    # - Log warning if ran from __init__.py file

    if not path and str(get_parent_frame_path()).endswith("__init__.py"):
        logging.warning(
            "Snapshot tests don't run from `__init__.py` files, needs investigation"
        )

    # - Collect flags

    if mode == "assert":
        flags = []
    elif mode == "create_missing":
        flags = ["create"]
    elif mode == "fix_broken":
        flags = ["create", "fix"]
    elif mode == "update_all":
        flags = ["create", "fix", "update", "trim"]
    else:
        raise Exception(
            f"Unknown mode: {mode}. Use one of ['assert', 'create_missing', 'fix_broken', 'update_all']"
        )

    # - Disable ugly logs from inline_snapshot

    class _Filter(logging.Filter):
        def filter(self, record):
            return not record.module.startswith("_")

    logging.getLogger().addFilter(_Filter())

    # - Run tests

    pytest.main(
        args=[
            str(path or get_parent_frame_path()),
            f"--inline-snapshot={','.join(flags)}"
            if flags
            else "--inline-snapshot-disable",
            "--capture=no",  # disables capturing of print calls
            "--log-cli-level=INFO",  # enables "live logs": logging records are shown immediately as they happen
            "--disable-warnings",
            "--no-header",
            # "--no-summary",  # inline-snapshot 0.8.0 works ONLY with the summary
            "--tb=no",  # disable traceback in the summary
            "--quiet",  # even less noise
        ]
        + (
            [
                "--override-ini",
                f"python_functions={python_functions}",
            ]
            if python_functions
            else []
        ),
        plugins=[SnapshotTestPlugin()],
    )
