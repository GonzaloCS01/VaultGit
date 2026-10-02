import ast
from pathlib import Path


def test_gui_includes_backup_controls():
    """
    Comprueba que gui.py incluya la integración visual
    del sistema de backups, no solo el módulo backend.
    """
    gui_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "gui.py"
    )

    source = gui_path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    class_node = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "VaultGitGUI"
        ),
        None,
    )

    assert class_node is not None

    method_names = {
        node.name
        for node in class_node.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }

    assert "open_backups_window" in method_names
    assert '"Backups"' in source
    assert "create_backup" in source
    assert "list_backups" in source
    assert "restore_backup" in source
