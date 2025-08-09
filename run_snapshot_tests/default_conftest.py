import sys

import pytest


def pytest_report_teststatus(report):
    """
    Override the default test status reporting to prevent any output.
    """
    if report.passed and report.when == "call":
        return ("Passed", None, None)


@pytest.hookimpl(tryfirst=True)
def pytest_exception_interact(node, call, report):
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


def pytest_sessionstart(session):
    # - Get terminal reporter

    terminal_reporter = session.config.pluginmanager.getplugin("terminalreporter")

    # - Monkey patch the write method of the terminal reporter to prevent any output

    original_write = terminal_reporter._tw.write

    def custom_write(s, **kwargs):
        if "::" in s and not s.startswith("FAILED"):  # test names
            original_write("-" * 80 + "\n[" + s.strip() + "]\n", **kwargs)

    terminal_reporter._tw.write = custom_write
