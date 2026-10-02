from pathlib import Path
import sys


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from paths import (
    APP_DATA_DIR,
    BACKUP_DIR,
    LEGACY_BACKUP_DIR,
    LEGACY_VAULT_PATH,
    PROJECT_ROOT,
    VAULT_PATH,
)


def yes_no(value):
    return "SI" if value else "NO"


def main():
    print()
    print("VaultGit - Ubicaciones de datos")
    print("===============================")
    print()

    print("Proyecto:")
    print(PROJECT_ROOT)
    print()

    print("Boveda antigua:")
    print(LEGACY_VAULT_PATH)
    print(
        "Existe:",
        yes_no(LEGACY_VAULT_PATH.exists()),
    )
    print()

    print("Backups antiguos:")
    print(LEGACY_BACKUP_DIR)
    print(
        "Existe:",
        yes_no(LEGACY_BACKUP_DIR.exists()),
    )
    print()

    print("Nueva carpeta privada de aplicacion:")
    print(APP_DATA_DIR)
    print()

    print("Nueva boveda:")
    print(VAULT_PATH)
    print(
        "Existe:",
        yes_no(VAULT_PATH.exists()),
    )
    print()

    print("Nuevos backups:")
    print(BACKUP_DIR)
    print(
        "Existe:",
        yes_no(BACKUP_DIR.exists()),
    )
    print()


if __name__ == "__main__":
    main()
