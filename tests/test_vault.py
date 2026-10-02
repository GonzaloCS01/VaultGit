import sys
from pathlib import Path

from nacl.exceptions import CryptoError
import pytest


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from vault import (
    create_vault,
    load_vault,
    save_vault_with_session,
    unlock_vault,
)


def test_unlock_returns_session_key(tmp_path):
    vault_path = tmp_path / "test.vault"

    original_data = {
        "accounts": []
    }

    password = "Password-De-Prueba-2026!"

    create_vault(
        vault_path,
        password,
        original_data,
    )

    vault_data, session = unlock_vault(
        vault_path,
        password,
    )

    assert vault_data == original_data

    assert "key" in session
    assert len(session["key"]) == 32

    assert "salt" in session

    assert "opslimit" in session
    assert "memlimit" in session


def test_save_with_session_persists_changes(
    tmp_path,
):
    vault_path = tmp_path / "test.vault"

    password = "Password-De-Prueba-2026!"

    original_data = {
        "accounts": []
    }

    create_vault(
        vault_path,
        password,
        original_data,
    )

    vault_data, session = unlock_vault(
        vault_path,
        password,
    )

    vault_data["accounts"].append(
        {
            "id": "demo-id",
            "service": "GitHub Demo",
            "username": "demo@example.com",
            "password": "Demo-123!",
            "url": "",
            "notes": "",
        }
    )

    save_vault_with_session(
        vault_path,
        session,
        vault_data,
    )

    reopened = load_vault(
        vault_path,
        password,
    )

    assert len(
        reopened["accounts"]
    ) == 1

    assert (
        reopened["accounts"][0]["service"]
        == "GitHub Demo"
    )


def test_wrong_password_after_session_save_fails(
    tmp_path,
):
    vault_path = tmp_path / "test.vault"

    correct_password = (
        "Password-Correcta-2026!"
    )

    create_vault(
        vault_path,
        correct_password,
        {
            "accounts": []
        },
    )

    vault_data, session = unlock_vault(
        vault_path,
        correct_password,
    )

    vault_data["accounts"].append(
        {
            "id": "demo-id",
            "service": "Example",
            "username": "demo@example.com",
            "password": "Demo!",
            "url": "",
            "notes": "",
        }
    )

    save_vault_with_session(
        vault_path,
        session,
        vault_data,
    )

    with pytest.raises(CryptoError):
        load_vault(
            vault_path,
            "Password-Incorrecta!",
        )