from inline_snapshot import outsource, snapshot

from inline_snapshot import external


def test():
    assert "value" == snapshot("value")
    assert 5 <= snapshot(5)
    assert 5 in snapshot([5])
    a = snapshot({"key": "value"})
    assert a["key"] == "value"

    assert outsource(
        "Long data" * 1000,
    ) == snapshot(external("dc9b148c966a*.txt"))


if __name__ == "__main__":
    from run_snapshot_tests import run_snapshot_tests

    run_snapshot_tests()
