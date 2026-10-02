import base64
import json
import sys
from pathlib import Path

import pytest
from nacl import pwhash, secret, utils
from nacl.exceptions import CryptoError


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from crypto import (
    derive_key,
    encrypt_text,
)
from vault import (
    KDF_MEMLIMIT,
    KDF_OPSLIMIT,
    get_vault_kdf_profile,
    load_vault,
    migrate_vault_kdf,
    needs_kdf_upgrade,
)


def create_legacy_vault(
    path,
    password,
    vault_data,
):
    """
    Crea manualmente una boveda con el antiguo perfil
    MODERATE: 3 operaciones / 256 MiB.
    """

    salt = utils.random(
        pwhash.argon2id.SALTBYTES
    )

    opslimit = (
        pwhash.argon2id.OPSLIMIT_MODERATE
    )

    memlimit = (
        pwhash.argon2id.MEMLIMIT_MODERATE
    )

    key = derive_key(
        password,
        salt,
        opslimit=opslimit,
        memlimit=memlimit,
    )

    plaintext = json.dumps(
        vault_data,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    encrypted = encrypt_text(
        key,
        plaintext,
    )

    vault_file = {
        "version": 1,
        "kdf": {
            "name": "argon2id",
            "opslimit": opslimit,
            "memlimit": memlimit,
            "salt": base64.b64encode(
                salt
            ).decode("ascii"),
        },
        "cipher": "xchacha20-poly1305",
        "ciphertext": base64.b64encode(
            encrypted
        ).decode("ascii"),
    }

    Path(path).write_text(
        json.dumps(
            vault_file,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_legacy_vault_reports_upgrade_needed(
    tmp_path,
):
    vault_path = tmp_path / "legacy.vault"

    create_legacy_vault(
        vault_path,
        "Frase-maestra-de-prueba-2026!",
        {
            "accounts": []
        },
    )

    assert needs_kdf_upgrade(
        vault_path
    ) is True


def test_kdf_migration_preserves_data_and_upgrades_profile(
    tmp_path,
):
    vault_path = tmp_path / "legacy.vault"

    password = (
        "Frase-maestra-de-prueba-2026!"
    )

    original_data = {
        "accounts": [
            {
                "id": "demo-id",
                "service": "GitHub Demo",
                "username": "demo@example.com",
                "password": "Demo-123!",
                "url": "https://github.com",
                "notes": "Datos ficticios",
            }
        ]
    }

    create_legacy_vault(
        vault_path,
        password,
        original_data,
    )

    before = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    old_salt = before["kdf"]["salt"]

    migrated_data, session = migrate_vault_kdf(
        vault_path,
        password,
    )

    profile = get_vault_kdf_profile(
        vault_path
    )

    after = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    assert migrated_data == original_data

    assert profile["opslimit"] == KDF_OPSLIMIT
    assert profile["memlimit"] == KDF_MEMLIMIT

    assert session["opslimit"] == KDF_OPSLIMIT
    assert session["memlimit"] == KDF_MEMLIMIT

    # La migracion debe usar un salt nuevo.
    assert after["kdf"]["salt"] != old_salt

    # Y la contraseña original debe seguir abriendo la boveda.
    reopened = load_vault(
        vault_path,
        password,
    )

    assert reopened == original_data

    assert needs_kdf_upgrade(
        vault_path
    ) is False


def test_wrong_password_does_not_modify_vault_during_migration(
    tmp_path,
):
    vault_path = tmp_path / "legacy.vault"

    correct_password = (
        "Frase-maestra-correcta-2026!"
    )

    create_legacy_vault(
        vault_path,
        correct_password,
        {
            "accounts": []
        },
    )

    before = vault_path.read_bytes()

    with pytest.raises(CryptoError):
        migrate_vault_kdf(
            vault_path,
            "Frase-maestra-incorrecta!",
        )

    after = vault_path.read_bytes()

    # Ni un solo byte debe cambiar si la contraseña falla.
    assert after == before
