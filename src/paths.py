import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Ubicación antigua usada durante el desarrollo inicial.
LEGACY_DATA_DIR = PROJECT_ROOT / "data"
LEGACY_VAULT_PATH = LEGACY_DATA_DIR / "vault.vault"
LEGACY_BACKUP_DIR = LEGACY_DATA_DIR / "backups"


def get_app_data_dir():
    """
    Devuelve una carpeta de datos apropiada para el sistema operativo.

    En Windows usamos LOCALAPPDATA para separar:
    - codigo del proyecto
    - datos privados de la aplicacion

    Esto evita depender de que el repositorio este en GitHub,
    OneDrive, Documentos u otra carpeta sincronizada.
    """

    if os.name == "nt":
        local_appdata = os.environ.get(
            "LOCALAPPDATA"
        )

        if local_appdata:
            return (
                Path(local_appdata)
                / "VaultGit"
            )

        # Fallback para instalaciones poco habituales.
        return (
            Path.home()
            / "AppData"
            / "Local"
            / "VaultGit"
        )

    if sys.platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "VaultGit"
        )

    xdg_data_home = os.environ.get(
        "XDG_DATA_HOME"
    )

    if xdg_data_home:
        return (
            Path(xdg_data_home)
            / "VaultGit"
        )

    return (
        Path.home()
        / ".local"
        / "share"
        / "VaultGit"
    )


APP_DATA_DIR = get_app_data_dir()
VAULT_PATH = APP_DATA_DIR / "vault.vault"
BACKUP_DIR = APP_DATA_DIR / "backups"
