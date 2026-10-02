from getpass import getpass
import sys
from pathlib import Path

from nacl.exceptions import CryptoError


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from data_migration import migrate_legacy_data
from paths import (
    BACKUP_DIR,
    LEGACY_BACKUP_DIR,
    LEGACY_VAULT_PATH,
    VAULT_PATH,
)


def main():
    print()
    print("VaultGit - Migracion de datos privados")
    print("======================================")
    print()

    print("Origen:")
    print(LEGACY_VAULT_PATH)
    print()

    print("Destino:")
    print(VAULT_PATH)
    print()

    if VAULT_PATH.exists():
        print(
            "CANCELADO: la nueva ubicacion ya contiene "
            "una boveda."
        )
        return

    if not LEGACY_VAULT_PATH.exists():
        print(
            "CANCELADO: no se encontro la boveda antigua."
        )
        return

    print(
        "Esta operacion COPIA los datos. "
        "No elimina la boveda antigua."
    )
    print()

    confirmation = input(
        "Escribe MIGRAR para continuar: "
    ).strip()

    if confirmation != "MIGRAR":
        print("Migracion cancelada.")
        return

    password = getpass(
        "Contraseña maestra: "
    )

    try:
        result = migrate_legacy_data(
            LEGACY_VAULT_PATH,
            LEGACY_BACKUP_DIR,
            VAULT_PATH,
            BACKUP_DIR,
            password,
        )

    except CryptoError:
        print()
        print(
            "ERROR: contraseña incorrecta "
            "o boveda antigua manipulada."
        )
        return

    except Exception as error:
        print()
        print(
            "ERROR: la migracion no pudo completarse."
        )
        print(
            type(error).__name__ + ":",
            error,
        )
        print()
        print(
            "La copia antigua se conserva intacta."
        )
        return

    finally:
        password = None

    print()
    print("Migracion completada correctamente.")
    print()

    print("Nueva boveda:")
    print(result["vault_path"])
    print()

    print(
        "Backups copiados:",
        result["backup_count"],
    )

    print()
    print(
        "SHA-256 nueva boveda:",
        result["vault_sha256"],
    )

    print()
    print(
        "IMPORTANTE: la boveda antigua NO se elimino."
    )
    print(
        "Todavia no abras VaultGit desde la GUI; "
        "primero comprobaremos las rutas."
    )


if __name__ == "__main__":
    main()
