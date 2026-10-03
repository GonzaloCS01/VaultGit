import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_gui():
    gui_path = PROJECT_ROOT / "src" / "gui.py"

    source = gui_path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    return source, tree


def get_gui_class(tree):
    return next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "VaultGitGUI"
        ),
        None,
    )


def test_gui_imports_central_branding_configuration():
    _source, tree = load_gui()

    imported = set()

    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "app_config"
        ):
            imported.update(
                alias.name
                for alias in node.names
            )

    assert {
        "APP_NAME",
        "APP_VERSION",
        "APP_TAGLINE",
        "APP_AUTHOR",
        "APP_AUTHOR_ROLE",
        "APP_ICON_ICO_PATH",
        "APP_ICON_PNG_PATH",
        "get_window_title",
    }.issubset(imported)


def test_gui_includes_about_window_and_brand_images():
    source, tree = load_gui()

    gui_class = get_gui_class(tree)

    assert gui_class is not None

    method_names = {
        node.name
        for node in gui_class.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }

    assert "load_brand_assets" in method_names
    assert "apply_window_branding" in method_names
    assert "open_about_window" in method_names
    assert '"Acerca de"' in source
    assert "brand_icon_small" in source
    assert "brand_logo_large" in source


def test_old_emoji_header_is_removed():
    source, _tree = load_gui()

    assert "🔐 VaultGit" not in source
    assert "text=APP_NAME" in source
    assert "APP_VERSION" in source
