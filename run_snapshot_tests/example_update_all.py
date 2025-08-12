from inline_snapshot import outsource, snapshot

from datetime import datetime


def test():
    assert str(datetime.now()) == snapshot()


if __name__ == "__main__":
    from run_snapshot_tests import run_snapshot_tests

    run_snapshot_tests(mode="update_all")
