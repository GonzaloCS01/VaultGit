from getpass import getpass
from pathlib import Path

from nacl.exceptions import CryptoError

from vault import create_vault, load_vault


VAULT_PATH = Path("data/vault.vault")


def create_new_vault():
    print("No existe una boveda. Vamos a crearla.")

    password = getpass(
        "Crea una contraseña maestra DE PRUEBA: "
    )

    confirmation = getpass(
        "Repite la contraseña maestra: "
    )

    if password != confirmation:
        print("Las contraseñas no coinciden.")
        return

    demo_data = {
        "accounts": [
            {
                "service": "ExampleMail",
                "username": "usuario@ejemplo.com",
                "password": "Demo-8472!",
            }
        ]
    }

    create_vault(
        VAULT_PATH,
        password,
        demo_data,
    )

    print("Boveda cifrada creada correctamente.")


def open_existing_vault():
    password = getpass(
        "Contraseña maestra: "
    )

    try:
        vault_data = load_vault(
            VAULT_PATH,
            password,
        )

    except CryptoError:
        print(
            "Contraseña incorrecta o boveda manipulada."
        )
        return

    print("Boveda desbloqueada correctamente.")

    accounts = vault_data.get("accounts", [])

    print(
        "Cuentas almacenadas:",
        len(accounts),
    )

    for account in accounts:
        print(
            "-",
            account["service"],
            "|",
            account["username"],
        )


def main():
    print("VaultGit")
    print("--------")

    if VAULT_PATH.exists():
        open_existing_vault()
    else:
        create_new_vault()


if __name__ == "__main__":
    main()