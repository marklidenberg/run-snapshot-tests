# run-snapshot-tests

Runner for Python [inline-snapshot](https://github.com/15r10nk/inline-snapshot/) tests with a better interface and cleaner terminal output.

To run pytest with async functions, install python-asyncio (`uv add python-asyncio`) and add this setting to the `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function" # prevents noisy warning message for some python-asyncio plugin versions
```

Note: only compatible with `inline-snapshot==0.8.0`.

# Interface

```python

def run_snapshot_tests(
    path: Union[str, Path, None] = None, # tests path. Defaults to current file if not set
    mode: Literal[
        "assert",
        "create_missing",
        "fix_broken",
        "update_all"
    ] = "create_missing",
    python_functions: Optional[str] = None, # Space-separated globs for function name patterns to collect as tests. Default is "test_*"
) -> None:
```

# Example

```python
from inline_snapshot import snapshot, outsource
from run_snapshot_tests import run_snapshot_tests

def test():
    assert "value" == snapshot()
    assert 5 <= snapshot()
    assert 5 in snapshot()
    a = snapshot()
    assert a["key"] == "value"

    assert (
        outsource(
            "Long data" * 1000,
        )
        == snapshot()
    )


if __name__ == "__main__":
    run_snapshot_tests()
```

↓

```python
from inline_snapshot import snapshot, outsource, external
from run_snapshot_tests import run_snapshot_tests


def test():
    assert "value" == snapshot('value')
    assert 5 <= snapshot(5)
    assert 5 in snapshot([5])
    a = snapshot({'key': 'value'})
    assert a["key"] == "value"

    assert (
        outsource(
            "Long data" * 1000,
        )
        == snapshot(external("hash:dc9b148c966a*.txt"))
    )


if __name__ == "__main__":
    run_snapshot_tests()

```
