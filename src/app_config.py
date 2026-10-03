import sys
from pathlib import Path


APP_NAME = "VaultGit"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Encrypted Credential Manager"

APP_AUTHOR = "Gonzalo Cessua"
APP_AUTHOR_ROLE = "Cybersecurity & Software Development"
APP_YEAR = "2026"

APP_COPYRIGHT = (
    f"© {APP_YEAR} {APP_AUTHOR}"
)


def get_project_root():
    """
    Devuelve la raíz del proyecto durante el desarrollo.
    """
    return Path(__file__).resolve().parents[1]


def get_resource_root():
    """
    Devuelve la carpeta desde la que se deben cargar
    recursos visuales.

    Durante el desarrollo:
        <proyecto>/

    Cuando VaultGit se empaquete con PyInstaller:
        sys._MEIPASS

    Esto permite usar los mismos paths antes y después
    de generar el ejecutable.
    """

    if (
        getattr(sys, "frozen", False)
        and hasattr(sys, "_MEIPASS")
    ):
        return Path(sys._MEIPASS)

    return get_project_root()


PROJECT_ROOT = get_project_root()
RESOURCE_ROOT = get_resource_root()

ASSETS_DIR = RESOURCE_ROOT / "assets"

APP_LOGO_PATH = (
    ASSETS_DIR
    / "vaultgit-logo.png"
)

APP_ICON_PNG_PATH = (
    ASSETS_DIR
    / "vaultgit-icon-256.png"
)

APP_ICON_ICO_PATH = (
    ASSETS_DIR
    / "vaultgit.ico"
)


def get_window_title():
    """
    Título estándar para las ventanas principales.
    """
    return (
        f"{APP_NAME} {APP_VERSION}"
    )


def get_about_text():
    """
    Texto base de créditos para la ventana Acerca de.
    """
    return (
        f"{APP_NAME} {APP_VERSION}\n"
        f"{APP_TAGLINE}\n\n"
        f"Developed by {APP_AUTHOR}\n"
        f"{APP_AUTHOR_ROLE}\n\n"
        f"{APP_COPYRIGHT}"
    )
