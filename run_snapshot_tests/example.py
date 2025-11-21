from inline_snapshot import outsource, snapshot


def test():
    assert "value" == snapshot()
    assert 5 <= snapshot()
    assert 5 in snapshot([5])
    a = snapshot()
    assert a["key"] == "value"

    assert (
        outsource(
            "Long data" * 1000,
        )
        == snapshot()
    )


if __name__ == "__main__":
    from run_snapshot_tests._run_snapshot_tests import run_snapshot_tests

    run_snapshot_tests()
