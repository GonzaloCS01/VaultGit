from getpass import getpass
from pathlib import Path

from nacl.exceptions import CryptoError

from accounts import (
    add_account,
    delete_account,
    get_accounts,
    search_accounts,
    update_account,
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


def select_account(vault_data):
    accounts = get_accounts(vault_data)

    if not accounts:
        print("No hay cuentas almacenadas.")
        return None

    show_accounts(vault_data)

    choice = input(
        "Selecciona el numero de cuenta: "
    ).strip()

    if not choice.isdigit():
        print("Seleccion no valida.")
        return None

    index = int(choice) - 1

    if index < 0 or index >= len(accounts):
        print("Cuenta no valida.")
        return None

    return accounts[index]


def show_account_details(vault_data):
    print()
    print("DETALLES DE CUENTA")
    print("==================")

    account = select_account(vault_data)

    if account is None:
        return

    print()
    print(
        "Servicio:",
        account.get("service", ""),
    )

    print(
        "Usuario:",
        account.get("username", ""),
    )

    print(
        "Contraseña:",
        "************",
    )

    print(
        "URL:",
        account.get("url", "") or "Sin URL",
    )

    print(
        "Notas:",
        account.get("notes", "") or "Sin notas",
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


def edit_account(
    vault_data,
    master_password,
):
    print()
    print("EDITAR CUENTA")
    print("=============")

    account = select_account(vault_data)

    if account is None:
        return

    print()
    print(
        "Deja un campo vacio para conservar su valor."
    )

    service = input(
        f"Servicio [{account.get('service', '')}]: "
    ).strip()

    username = input(
        f"Usuario [{account.get('username', '')}]: "
    ).strip()

    new_password = getpass(
        "Nueva contraseña "
        "(Enter para conservar la actual): "
    )

    url = input(
        f"URL [{account.get('url', '')}]: "
    ).strip()

    notes = input(
        f"Notas [{account.get('notes', '')}]: "
    ).strip()

    update_account(
        vault_data,
        account["id"],
        service=service if service else None,
        username=username if username else None,
        password=new_password if new_password else None,
        url=url if url else None,
        notes=notes if notes else None,
    )

    save_vault(
        VAULT_PATH,
        master_password,
        vault_data,
    )

    print("Cuenta actualizada correctamente.")


def remove_account(
    vault_data,
    master_password,
):
    print()
    print("ELIMINAR CUENTA")
    print("===============")

    account = select_account(vault_data)

    if account is None:
        return

    print()
    print(
        "Vas a eliminar:",
        account.get("service", ""),
    )

    confirmation = input(
        "Escribe ELIMINAR para confirmar: "
    ).strip()

    if confirmation != "ELIMINAR":
        print("Eliminacion cancelada.")
        return

    delete_account(
        vault_data,
        account["id"],
    )

    save_vault(
        VAULT_PATH,
        master_password,
        vault_data,
    )

    print("Cuenta eliminada correctamente.")


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
        print("[4] Ver detalles")
        print("[5] Editar cuenta")
        print("[6] Eliminar cuenta")
        print("[7] Bloquear y salir")
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
            show_account_details(vault_data)

        elif option == "5":
            edit_account(
                vault_data,
                master_password,
            )

        elif option == "6":
            remove_account(
                vault_data,
                master_password,
            )

        elif option == "7":
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