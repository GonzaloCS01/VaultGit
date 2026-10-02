import hashlib
import os
import shutil
from pathlib import Path

from vault import load_vault


def sha256_file(path):
    """
    Calcula SHA-256 de un archivo para comprobar
    que una copia sea byte por byte equivalente.
    """
    path = Path(path)

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def migrate_legacy_data(
    legacy_vault_path,
    legacy_backup_dir,
    new_vault_path,
    new_backup_dir,
    master_password,
):
    """
    Copia la boveda y sus backups desde la ubicacion
    antigua del proyecto a la carpeta privada de datos
    de la aplicacion.

    Reglas de seguridad:
    - Verifica primero la contraseña sobre la boveda antigua.
    - Nunca elimina los archivos antiguos.
    - No sobrescribe una boveda nueva ya existente.
    - Copia primero a un archivo temporal.
    - Compara SHA-256 origen/destino.
    - Verifica que la copia nueva pueda desbloquearse.
    """

    legacy_vault_path = Path(
        legacy_vault_path
    )

    legacy_backup_dir = Path(
        legacy_backup_dir
    )

    new_vault_path = Path(
        new_vault_path
    )

    new_backup_dir = Path(
        new_backup_dir
    )

    if not legacy_vault_path.exists():
        raise FileNotFoundError(
            "No existe la boveda antigua."
        )

    if new_vault_path.exists():
        raise FileExistsError(
            "La nueva ubicacion ya contiene una boveda."
        )

    if (
        new_backup_dir.exists()
        and any(new_backup_dir.iterdir())
    ):
        raise FileExistsError(
            "La nueva carpeta de backups ya contiene archivos."
        )

    # 1. Verificar la contraseña antes de copiar nada.
    legacy_data = load_vault(
        legacy_vault_path,
        master_password,
    )

    new_vault_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    new_backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_vault = new_vault_path.with_suffix(
        new_vault_path.suffix + ".migration.tmp"
    )

    copied_backups = []

    try:
        # 2. Copiar la boveda a un archivo temporal.
        shutil.copy2(
            legacy_vault_path,
            temporary_vault,
        )

        # 3. Verificar integridad byte a byte mediante hash.
        source_hash = sha256_file(
            legacy_vault_path
        )

        copied_hash = sha256_file(
            temporary_vault
        )

        if source_hash != copied_hash:
            raise ValueError(
                "La copia de la boveda no coincide con el original."
            )

        # 4. Colocar la copia en su destino definitivo.
        os.replace(
            temporary_vault,
            new_vault_path,
        )

        # 5. Verificar que la nueva copia realmente abre.
        copied_data = load_vault(
            new_vault_path,
            master_password,
        )

        if copied_data != legacy_data:
            raise ValueError(
                "La boveda copiada no contiene los mismos datos."
            )

        # 6. Copiar backups cifrados sin eliminar los antiguos.
        if legacy_backup_dir.exists():
            for source_backup in sorted(
                legacy_backup_dir.glob("*.vault")
            ):
                destination_backup = (
                    new_backup_dir
                    / source_backup.name
                )

                if destination_backup.exists():
                    raise FileExistsError(
                        "Ya existe un backup con el mismo nombre "
                        f"en el destino: {source_backup.name}"
                    )

                shutil.copy2(
                    source_backup,
                    destination_backup,
                )

                if (
                    sha256_file(source_backup)
                    != sha256_file(destination_backup)
                ):
                    raise ValueError(
                        "Un backup copiado no coincide "
                        f"con el original: {source_backup.name}"
                    )

                copied_backups.append(
                    destination_backup
                )

    except Exception:
        # Rollback solo de la NUEVA ubicación.
        # Los archivos antiguos nunca se tocan.
        if temporary_vault.exists():
            temporary_vault.unlink()

        if new_vault_path.exists():
            new_vault_path.unlink()

        for backup_path in copied_backups:
            if backup_path.exists():
                backup_path.unlink()

        raise

    return {
        "vault_path": new_vault_path,
        "backup_dir": new_backup_dir,
        "backup_count": len(copied_backups),
        "vault_sha256": sha256_file(
            new_vault_path
        ),
    }
