import py_compile
from pathlib import Path


def test_gui_compiles():
    """
    Impide que errores de sintaxis o indentación
    en gui.py pasen desapercibidos por pytest.
    """

    gui_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "gui.py"
    )

    py_compile.compile(
        str(gui_path),
        doraise=True,
    )
