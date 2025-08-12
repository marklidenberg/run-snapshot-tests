import ast
import inspect

from executing import Source
from inline_snapshot._inline_snapshot import (
    Snapshot,
    _active,
    _files_with_snapshots,
    _update_flags,
    found_snapshots,
    repr_wrapper,
    snapshots,
)
from inline_snapshot._sentinels import undefined


@repr_wrapper
def fixed_snapshot(obj=undefined):
    """Fork of original inline-snapshot snapshot.

    Adds this snippet:
    ```
        if obj != undefined and not _update_flags.update and not _update_flags.fix and not _update_flags.trim:
        return obj
    ```

    This way in create mode comparison will raise an error if snapshot value is different from the actual value.

    """
    if not _active:
        if obj is undefined:
            raise AssertionError(
                "your snapshot is missing a value run pytest with --inline-snapshot=create"
            )
        else:
            return obj

    if (
        obj != undefined
        and not _update_flags.update
        and not _update_flags.fix
        and not _update_flags.trim
    ):
        return obj

    frame = inspect.currentframe().f_back.f_back
    expr = Source.executing(frame)

    module = inspect.getmodule(frame)
    if module is not None:
        _files_with_snapshots.add(module.__file__)

    key = id(frame.f_code), frame.f_lasti

    if key not in snapshots:
        node = expr.node
        if node is None:
            # we can run without knowing of the calling expression but we will not be able to fix code
            snapshots[key] = Snapshot(obj, None)
        else:
            assert isinstance(node.func, ast.Name)
            assert node.func.id == "snapshot"
            snapshots[key] = Snapshot(obj, expr)
        found_snapshots.append(snapshots[key])

    return snapshots[key]._value
