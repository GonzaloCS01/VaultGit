from getpass import getpass
from pathlib import Path

from nacl.exceptions import CryptoError

from accounts import (
    add_account,
    get_accounts,
    search_accounts,
)

from vault import (
    create_vault,
    load_vault,
    save_vault,
)


VAULT_PATH = Path("data/vault.vault")


def create_new_vault():
    print("No existe una boveda.")
    print("Vamos a crear una nueva.")

    password = getpass(
        "Crea una contraseña maestra DE PRUEBA: "
    )

    confirmation = getpass(
        "Repite la contraseña maestra: "
    )

    if password != confirmation:
        print("Las contraseñas no coinciden.")
        return None, None

    vault_data = {
        "accounts": []
    }

    create_vault(
        VAULT_PATH,
        password,
        vault_data,
    )

    print("Boveda creada correctamente.")

    return password, vault_data


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
        return None, None

    print("Boveda desbloqueada correctamente.")

    return password, vault_data


def show_accounts(vault_data):
    accounts = get_accounts(vault_data)

    print()
    print("CUENTAS")
    print("=======")

    if not accounts:
        print("No hay cuentas almacenadas.")
        return

    for number, account in enumerate(
        accounts,
        start=1,
    ):
        print(
            f"{number}. "
            f"{account.get('service', 'Sin servicio')} "
            f"| "
            f"{account.get('username', '')}"
        )


def create_account(
    vault_data,
    master_password,
):
    print()
    print("NUEVA CUENTA")
    print("============")

    service = input(
        "Servicio: "
    ).strip()

    username = input(
        "Usuario o correo: "
    ).strip()

    password = getpass(
        "Contraseña: "
    )

    url = input(
        "URL (opcional): "
    ).strip()

    notes = input(
        "Notas (opcional): "
    ).strip()

    if not service:
        print("El servicio no puede estar vacio.")
        return

    add_account(
        vault_data,
        service,
        username,
        password,
        url,
        notes,
    )

    save_vault(
        VAULT_PATH,
        master_password,
        vault_data,
    )

    print("Cuenta guardada correctamente.")


def search_account(vault_data):
    query = input(
        "Buscar: "
    )

    results = search_accounts(
        vault_data,
        query,
    )

    print()
    print("RESULTADOS")
    print("==========")

    if not results:
        print("No se encontraron cuentas.")
        return

    for account in results:
        print(
            "-",
            account.get("service", ""),
            "|",
            account.get("username", ""),
        )


def vault_menu(
    master_password,
    vault_data,
):
    while True:
        print()
        print("VaultGit")
        print("====================")
        print("[1] Ver cuentas")
        print("[2] Añadir cuenta")
        print("[3] Buscar cuenta")
        print("[4] Bloquear y salir")
        print()

        option = input(
            "Selecciona una opcion: "
        ).strip()

        if option == "1":
            show_accounts(vault_data)

        elif option == "2":
            create_account(
                vault_data,
                master_password,
            )

        elif option == "3":
            search_account(vault_data)

        elif option == "4":
            print("VaultGit bloqueado.")
            break

        else:
            print("Opcion no valida.")


def main():
    print()
    print("VaultGit")
    print("========")

    if VAULT_PATH.exists():
        master_password, vault_data = (
            open_existing_vault()
        )

    else:
        master_password, vault_data = (
            create_new_vault()
        )

    if master_password is None:
        return

    vault_menu(
        master_password,
        vault_data,
    )


if __name__ == "__main__":
    main()