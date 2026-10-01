import sys
from pathlib import Path

import pytest
from nacl.exceptions import CryptoError


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from crypto import (
    generate_salt,
    derive_key,
    encrypt_text,
    decrypt_text,
)


def test_encrypt_and_decrypt():
    password = "Password-De-Prueba-2026!"

    salt = generate_salt()
    key = derive_key(password, salt)

    original_text = "VaultGit test data"

    encrypted = encrypt_text(
        key,
        original_text,
    )

    decrypted = decrypt_text(
        key,
        encrypted,
    )

    assert decrypted == original_text


def test_wrong_password_cannot_decrypt():
    salt = generate_salt()

    correct_key = derive_key(
        "Password-Correcta!",
        salt,
    )

    wrong_key = derive_key(
        "Password-Incorrecta!",
        salt,
    )

    encrypted = encrypt_text(
        correct_key,
        "Informacion secreta de prueba",
    )

    with pytest.raises(CryptoError):
        decrypt_text(
            wrong_key,
            encrypted,
        )