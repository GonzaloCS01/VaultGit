import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_file(relative_path):
    path = PROJECT_ROOT / relative_path

    source = path.read_text(
        encoding="utf-8"
    )

    return source, ast.parse(source)


def imported_names_from_paths(tree):
    names = set()

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "paths"
        ):
            names.update(
                alias.name
                for alias in node.names
            )

    return names


def test_gui_uses_central_private_paths():
    source, tree = parse_file(
        "src/gui.py"
    )

    imported = imported_names_from_paths(
        tree
    )

    assert "VAULT_PATH" in imported
    assert "BACKUP_DIR" in imported

    assert (
        'PROJECT_ROOT / "data" / "vault.vault"'
        not in source
    )

    assert (
        'PROJECT_ROOT / "data" / "backups"'
        not in source
    )


def test_terminal_main_uses_private_vault_path():
    source, tree = parse_file(
        "src/main.py"
    )

    imported = imported_names_from_paths(
        tree
    )

    assert "VAULT_PATH" in imported

    assert 'Path("data/vault.vault")' not in source
    assert '"data/vault.vault"' not in source
