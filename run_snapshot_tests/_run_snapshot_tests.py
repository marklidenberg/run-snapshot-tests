from collections.abc import Callable
import logging
import os
import shutil
from typing import Any, Literal, Union

import pytest

import inspect

from inspect import FrameInfo
from pathlib import Path

# - Dependent utils


def read_file(
    path: Union[str, Path],
    as_bytes: bool = False,
    reader: Callable = lambda file: file.read(),
    default: Any = ...,  # if file does not exist
    open_kwargs: dict = {},  # extra kwargs for open
) -> Any:
    """A simple file reader helper, as it should have been in the first place. Useful for one-liners and nested function calls."""

    # - Convert Path to str

    path = str(path)

    # - Check if file exists

    if not os.path.exists(path) and default is not Ellipsis:
        return default

    # - Read file

    with open(path, "rb" if as_bytes else "r", **open_kwargs) as file:
        return reader(file)


def write_file(
    data: Any,
    path: Union[str, Path],
    as_bytes: bool = False,
    writer: Callable = lambda data, file: file.write(data),
    open_kwargs: dict = {},
    ensure_path: bool = True,
) -> Any:
    """A simple file writer helper, as it should have been in the first place. Useful for one-liners or nested function calls."""

    # - Ensure path

    if ensure_path:
        os.makedirs(os.path.dirname(os.path.abspath(str(path))), exist_ok=True)

    # - Write file

    with open(str(path), "wb" if as_bytes else "w", **open_kwargs) as file:
        return writer(data, file)


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
) -> None:
    """Run test with inline snapshots.

    A helper over inline-snapshot library with better interface + prettier logs.

    Parameters
    ----------
    path : str, optional
        Path to the file to run tests from. If not provided, the current file is used.
    """

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

    # - Create `conftest.py` file with hook to show traceback on failures

    # todo later: put into a plugin [@marklidenberg]

    # -- Copy old conftest.py to conftest.py.bak if it exists

    old_contents = read_file(
        "conftest.py",
        default="",
    )
    if os.path.exists("conftest.py"):
        write_file(
            path="conftest.py.bak",
            data=old_contents,
        )

    write_file(
        path="conftest.py",
        data="\n".join(
            [
                old_contents,
                read_file(
                    os.path.join(os.path.dirname(__file__), "default_conftest.py")
                ),
            ]
        ),
    )

    # - Create a fake /tests directory to silence inline-snapshot log
    """
    ══════════════════════════════════════════════════ inline-snapshot ══════════════════════════════════════════════════
INFO: inline-snapshot can not trim your external snapshots, because there is no tests/ folder in your repository root
and no test-dir defined in your pyproject.toml.
    """

    tests_existed = os.path.exists("tests")
    os.makedirs("tests", exist_ok=True)

    # - Run tests

    pytest.main(
        args=[
            path or get_parent_frame_path(),
            f"--inline-snapshot={','.join(flags)}"
            if flags
            else "--inline-snapshot-disable",
            "--capture=no",  # disables capturing of print calls
            "--log-cli-level=INFO",  # enables "live logs": logging records are shown immediately as they happen
            "--disable-warnings",
            "--no-header",
            # "--no-summary",  # inline-snapshot works ONLY with the summary
            "--tb=no",  # disable traceback in the summary
            "--quiet",  # even less noise
        ]
    )

    # - Remove fake /tests directory

    if not tests_existed:
        shutil.rmtree("tests")

    # - Restore old conftest.py

    os.remove("conftest.py")
    if old_contents:
        write_file(
            path="conftest.py",
            data=old_contents,
        )

    if os.path.exists("conftest.py.bak"):
        os.remove("conftest.py.bak")
