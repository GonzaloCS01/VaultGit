import json
import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from backup import create_backup
from vault import create_vault


TEST_PASSWORD = (
    "Frase-maestra-de-prueba-para-metadata-2026!"
)


SENSITIVE_VALUES = {
    "id": "vaultgit-secret-id-8f3c2d5e7a91",
    "service": "ServicioSuperSecreto-VaultGit-2026",
    "username": "correo-secreto-vaultgit-2026@example.invalid",
    "password": "ClaveSuperSecreta-VaultGit-2026!#987654",
    "url": "https://ejemplo.invalid/ruta-super-secreta-vaultgit",
    "notes": (
        "NOTA-PRIVADA-VAULTGIT-"
        "este-texto-no-debe-aparecer-fuera-del-ciphertext"
    ),
}


def build_sensitive_vault_data():
    return {
        "accounts": [
            dict(SENSITIVE_VALUES)
        ]
    }


def assert_sensitive_values_not_visible(raw_text):
    for field_name, value in SENSITIVE_VALUES.items():
        assert value not in raw_text, (
            f"El campo sensible '{field_name}' "
            "aparecio en texto visible."
        )


def test_vault_does_not_expose_sensitive_account_metadata(
    tmp_path,
):
    vault_path = tmp_path / "privacy-test.vault"

    create_vault(
        vault_path,
        TEST_PASSWORD,
        build_sensitive_vault_data(),
    )

    raw_text = vault_path.read_text(
        encoding="utf-8"
    )

    assert_sensitive_values_not_visible(
        raw_text
    )


def test_backup_does_not_expose_sensitive_account_metadata(
    tmp_path,
):
    vault_path = tmp_path / "privacy-test.vault"
    backup_dir = tmp_path / "backups"

    create_vault(
        vault_path,
        TEST_PASSWORD,
        build_sensitive_vault_data(),
    )

    backup_path = create_backup(
        vault_path,
        backup_dir,
        prefix="privacy-test",
        keep=None,
    )

    raw_text = backup_path.read_text(
        encoding="utf-8"
    )

    assert_sensitive_values_not_visible(
        raw_text
    )


def test_vault_public_metadata_is_limited_to_expected_fields(
    tmp_path,
):
    vault_path = tmp_path / "privacy-test.vault"

    create_vault(
        vault_path,
        TEST_PASSWORD,
        build_sensitive_vault_data(),
    )

    raw_vault = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    assert set(raw_vault.keys()) == {
        "version",
        "kdf",
        "cipher",
        "ciphertext",
    }

    assert set(raw_vault["kdf"].keys()) == {
        "name",
        "opslimit",
        "memlimit",
        "salt",
    }

    assert raw_vault["kdf"]["name"] == "argon2id"
    assert raw_vault["cipher"] == "xchacha20-poly1305"

    assert isinstance(
        raw_vault["ciphertext"],
        str,
    )

    assert raw_vault["ciphertext"]


def test_ciphertext_changes_when_same_data_is_encrypted_twice(
    tmp_path,
):
    """
    Dos bovedas creadas con exactamente los mismos datos
    y la misma contraseña no deben producir el mismo
    ciphertext, porque cada creación usa aleatoriedad nueva.
    """

    first_vault = tmp_path / "first.vault"
    second_vault = tmp_path / "second.vault"

    vault_data = build_sensitive_vault_data()

    create_vault(
        first_vault,
        TEST_PASSWORD,
        vault_data,
    )

    create_vault(
        second_vault,
        TEST_PASSWORD,
        vault_data,
    )

    first_raw = json.loads(
        first_vault.read_text(
            encoding="utf-8"
        )
    )

    second_raw = json.loads(
        second_vault.read_text(
            encoding="utf-8"
        )
    )

    assert (
        first_raw["kdf"]["salt"]
        != second_raw["kdf"]["salt"]
    )

    assert (
        first_raw["ciphertext"]
        != second_raw["ciphertext"]
    )
