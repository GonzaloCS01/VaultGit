import os
import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from paths import (
    APP_DATA_DIR,
    BACKUP_DIR,
    LEGACY_BACKUP_DIR,
    LEGACY_DATA_DIR,
    LEGACY_VAULT_PATH,
    PROJECT_ROOT,
    VAULT_PATH,
    get_app_data_dir,
)


def test_vault_and_backups_share_app_data_root():
    assert VAULT_PATH.parent == APP_DATA_DIR
    assert BACKUP_DIR.parent == APP_DATA_DIR


def test_legacy_paths_stay_inside_project_data():
    assert LEGACY_DATA_DIR == PROJECT_ROOT / "data"
    assert (
        LEGACY_VAULT_PATH
        == LEGACY_DATA_DIR / "vault.vault"
    )
    assert (
        LEGACY_BACKUP_DIR
        == LEGACY_DATA_DIR / "backups"
    )


def test_app_data_is_outside_project_on_windows():
    if os.name != "nt":
        return

    local_appdata = os.environ.get(
        "LOCALAPPDATA"
    )

    if local_appdata:
        expected = (
            Path(local_appdata)
            / "VaultGit"
        )

        assert get_app_data_dir() == expected
        assert APP_DATA_DIR == expected

    # El objetivo de seguridad es que la ubicacion nueva
    # no sea la carpeta data del repositorio.
    assert APP_DATA_DIR != LEGACY_DATA_DIR
