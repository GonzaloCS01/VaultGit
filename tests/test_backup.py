import sys
from pathlib import Path

import pytest
from nacl.exceptions import CryptoError


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from backup import (
    create_backup,
    restore_backup,
)
from vault import (
    create_vault,
    load_vault,
)


PASSWORD = "Password-De-Prueba-2026!"


def make_data(service, password):
    return {
        "accounts": [
            {
                "id": "demo-id",
                "service": service,
                "username": "demo@example.com",
                "password": password,
                "url": "https://example.com",
                "notes": "Datos ficticios",
            }
        ]
    }


def test_backup_is_encrypted_copy(tmp_path):
    vault_path = tmp_path / "vault.vault"
    backup_dir = tmp_path / "backups"

    vault_data = make_data(
        "GitHub Demo",
        "Demo-123!",
    )

    create_vault(
        vault_path,
        PASSWORD,
        vault_data,
    )

    backup_path = create_backup(
        vault_path,
        backup_dir,
    )

    assert backup_path.read_bytes() == vault_path.read_bytes()
    assert b"Demo-123!" not in backup_path.read_bytes()
    assert b"demo@example.com" not in backup_path.read_bytes()


def test_restore_backup_recovers_old_data(tmp_path):
    vault_path = tmp_path / "vault.vault"
    backup_dir = tmp_path / "backups"

    old_data = make_data(
        "Cuenta Antigua",
        "Old-Password!",
    )

    create_vault(
        vault_path,
        PASSWORD,
        old_data,
    )

    backup_path = create_backup(
        vault_path,
        backup_dir,
    )

    new_data = make_data(
        "Cuenta Nueva",
        "New-Password!",
    )

    create_vault(
        vault_path,
        PASSWORD,
        new_data,
    )

    restored_data, session, safety_backup = restore_backup(
        backup_path,
        vault_path,
        PASSWORD,
        backup_dir,
    )

    assert restored_data == old_data
    assert len(session["key"]) == 32
    assert safety_backup is not None
    assert safety_backup.exists()
    assert load_vault(vault_path, PASSWORD) == old_data


def test_wrong_password_does_not_replace_current_vault(tmp_path):
    vault_path = tmp_path / "vault.vault"
    backup_dir = tmp_path / "backups"

    backup_data = make_data(
        "Backup",
        "Backup-Password!",
    )

    create_vault(
        vault_path,
        PASSWORD,
        backup_data,
    )

    backup_path = create_backup(
        vault_path,
        backup_dir,
    )

    current_data = make_data(
        "Actual",
        "Current-Password!",
    )

    create_vault(
        vault_path,
        PASSWORD,
        current_data,
    )

    current_bytes = vault_path.read_bytes()

    with pytest.raises(CryptoError):
        restore_backup(
            backup_path,
            vault_path,
            "Password-Incorrecta!",
            backup_dir,
        )

    assert vault_path.read_bytes() == current_bytes
    assert load_vault(vault_path, PASSWORD) == current_data
