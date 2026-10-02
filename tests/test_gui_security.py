import ast
from pathlib import Path


def test_gui_includes_kdf_security_controls():
    """
    Comprueba que la GUI incluya la sección de seguridad
    y la integración de migración Argon2id.
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

    assert "open_security_window" in method_names

    assert '"Seguridad"' in source
    assert "get_vault_kdf_profile" in source
    assert "needs_kdf_upgrade" in source
    assert "migrate_vault_kdf" in source
    assert 'prefix="pre-kdf-upgrade"' in source
