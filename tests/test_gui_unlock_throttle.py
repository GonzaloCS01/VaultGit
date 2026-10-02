import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_gui():
    gui_path = PROJECT_ROOT / "src" / "gui.py"

    source = gui_path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    return source, tree


def test_gui_integrates_unlock_throttle():
    source, tree = load_gui()

    imported = False

    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "auth_guard"
        ):
            imported = any(
                alias.name == "UnlockThrottle"
                for alias in node.names
            )

    assert imported is True

    assert "self.unlock_throttle = UnlockThrottle()" in source
    assert "self.unlock_throttle.record_failure()" in source
    assert "self.unlock_throttle.record_success()" in source
    assert "self.update_unlock_throttle_ui()" in source
    assert "self.after(" in source


def test_gui_unlock_throttle_does_not_use_blocking_sleep():
    _source, tree = load_gui()

    sleep_calls = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        function = node.func

        if (
            isinstance(function, ast.Attribute)
            and function.attr == "sleep"
        ):
            sleep_calls.append(node)

        elif (
            isinstance(function, ast.Name)
            and function.id == "sleep"
        ):
            sleep_calls.append(node)

    assert sleep_calls == []
