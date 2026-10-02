import sys
from pathlib import Path

import pytest
from nacl.exceptions import CryptoError


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from backup import create_backup
from data_migration import (
    migrate_legacy_data,
    sha256_file,
)
from vault import create_vault, load_vault


TEST_PASSWORD = (
    "Frase-maestra-de-prueba-2026!"
)


def test_data_migration_copies_and_preserves_vault(
    tmp_path,
):
    legacy_data = tmp_path / "project" / "data"
    old_vault = legacy_data / "vault.vault"
    old_backups = legacy_data / "backups"

    new_data = tmp_path / "appdata"
    new_vault = new_data / "vault.vault"
    new_backups = new_data / "backups"

    original_data = {
        "accounts": [
            {
                "id": "demo",
                "service": "GitHub Demo",
                "username": "demo@example.com",
                "password": "Demo-123!",
                "url": "",
                "notes": "",
            }
        ]
    }

    create_vault(
        old_vault,
        TEST_PASSWORD,
        original_data,
    )

    create_backup(
        old_vault,
        old_backups,
        prefix="test-backup",
        keep=None,
    )

    old_hash = sha256_file(
        old_vault
    )

    result = migrate_legacy_data(
        old_vault,
        old_backups,
        new_vault,
        new_backups,
        TEST_PASSWORD,
    )

    assert old_vault.exists()
    assert new_vault.exists()

    assert sha256_file(old_vault) == old_hash
    assert sha256_file(new_vault) == old_hash

    assert (
        load_vault(
            new_vault,
            TEST_PASSWORD,
        )
        == original_data
    )

    assert result["backup_count"] == 1
    assert len(
        list(new_backups.glob("*.vault"))
    ) == 1


def test_wrong_password_does_not_create_new_vault(
    tmp_path,
):
    old_vault = (
        tmp_path
        / "project"
        / "data"
        / "vault.vault"
    )

    old_backups = old_vault.parent / "backups"

    new_vault = (
        tmp_path
        / "appdata"
        / "vault.vault"
    )

    new_backups = new_vault.parent / "backups"

    create_vault(
        old_vault,
        TEST_PASSWORD,
        {
            "accounts": []
        },
    )

    with pytest.raises(CryptoError):
        migrate_legacy_data(
            old_vault,
            old_backups,
            new_vault,
            new_backups,
            "Frase-maestra-incorrecta!",
        )

    assert old_vault.exists()
    assert not new_vault.exists()


def test_existing_destination_is_never_overwritten(
    tmp_path,
):
    old_vault = (
        tmp_path
        / "project"
        / "data"
        / "vault.vault"
    )

    new_vault = (
        tmp_path
        / "appdata"
        / "vault.vault"
    )

    old_backups = old_vault.parent / "backups"
    new_backups = new_vault.parent / "backups"

    create_vault(
        old_vault,
        TEST_PASSWORD,
        {
            "accounts": []
        },
    )

    create_vault(
        new_vault,
        "Otra-frase-maestra-2026!",
        {
            "accounts": []
        },
    )

    before = new_vault.read_bytes()

    with pytest.raises(FileExistsError):
        migrate_legacy_data(
            old_vault,
            old_backups,
            new_vault,
            new_backups,
            TEST_PASSWORD,
        )

    after = new_vault.read_bytes()

    assert after == before
