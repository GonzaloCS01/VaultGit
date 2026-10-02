import base64
import binascii
import json
import sys
from pathlib import Path

import pytest
from nacl.exceptions import CryptoError


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from vault import (
    create_vault,
    load_vault,
)


TEST_PASSWORD = "Password-De-Prueba-2026!"


def create_test_vault(tmp_path):
    vault_path = tmp_path / "security-test.vault"

    vault_data = {
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

    create_vault(
        vault_path,
        TEST_PASSWORD,
        vault_data,
    )

    return vault_path


def test_modified_ciphertext_is_rejected(tmp_path):
    vault_path = create_test_vault(
        tmp_path
    )

    vault_file = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    encrypted = bytearray(
        base64.b64decode(
            vault_file["ciphertext"]
        )
    )

    encrypted[-1] ^= 1

    vault_file["ciphertext"] = (
        base64.b64encode(
            bytes(encrypted)
        ).decode("ascii")
    )

    vault_path.write_text(
        json.dumps(
            vault_file,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(CryptoError):
        load_vault(
            vault_path,
            TEST_PASSWORD,
        )


def test_invalid_base64_is_rejected(tmp_path):
    vault_path = create_test_vault(
        tmp_path
    )

    vault_file = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    vault_file["ciphertext"] = (
        "ESTO-NO-ES-BASE64!!!"
    )

    vault_path.write_text(
        json.dumps(
            vault_file,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        binascii.Error
    ):
        load_vault(
            vault_path,
            TEST_PASSWORD,
        )


def test_unknown_vault_version_is_rejected(
    tmp_path,
):
    vault_path = create_test_vault(
        tmp_path
    )

    vault_file = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    vault_file["version"] = 999

    vault_path.write_text(
        json.dumps(
            vault_file,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Version",
    ):
        load_vault(
            vault_path,
            TEST_PASSWORD,
        )


def test_missing_ciphertext_is_rejected(
    tmp_path,
):
    vault_path = create_test_vault(
        tmp_path
    )

    vault_file = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    del vault_file["ciphertext"]

    vault_path.write_text(
        json.dumps(
            vault_file,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="ciphertext",
    ):
        load_vault(
            vault_path,
            TEST_PASSWORD,
        )