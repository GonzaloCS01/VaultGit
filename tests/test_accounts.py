import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from accounts import (
    add_account,
    delete_account,
    get_accounts,
    get_account_by_id,
    search_accounts,
    update_account,
)


def test_add_account():
    vault_data = {
        "accounts": []
    }

    account = add_account(
        vault_data,
        "GitHub",
        "usuario@ejemplo.com",
        "Demo-123!",
        "https://github.com",
        "Cuenta de prueba",
    )

    accounts = get_accounts(vault_data)

    assert len(accounts) == 1
    assert account["service"] == "GitHub"
    assert account["username"] == "usuario@ejemplo.com"
    assert account["password"] == "Demo-123!"
    assert "id" in account


def test_search_accounts():
    vault_data = {
        "accounts": []
    }

    add_account(
        vault_data,
        "GitHub",
        "github@ejemplo.com",
        "Password-1!",
    )

    add_account(
        vault_data,
        "Netflix",
        "netflix@ejemplo.com",
        "Password-2!",
    )

    results = search_accounts(
        vault_data,
        "github",
    )

    assert len(results) == 1
    assert results[0]["service"] == "GitHub"


def test_update_account():
    vault_data = {
        "accounts": []
    }

    account = add_account(
        vault_data,
        "GitHub",
        "viejo@ejemplo.com",
        "Password-Vieja!",
    )

    result = update_account(
        vault_data,
        account["id"],
        service="GitHub Personal",
        username="nuevo@ejemplo.com",
    )

    updated = get_account_by_id(
        vault_data,
        account["id"],
    )

    assert result is True
    assert updated["service"] == "GitHub Personal"
    assert updated["username"] == "nuevo@ejemplo.com"
    assert updated["password"] == "Password-Vieja!"


def test_delete_account():
    vault_data = {
        "accounts": []
    }

    account = add_account(
        vault_data,
        "Cuenta Temporal",
        "demo@ejemplo.com",
        "Temporal-123!",
    )

    result = delete_account(
        vault_data,
        account["id"],
    )

    assert result is True
    assert len(get_accounts(vault_data)) == 0


def test_invalid_account_id():
    vault_data = {
        "accounts": []
    }

    result = delete_account(
        vault_data,
        "id-que-no-existe",
    )

    assert result is False