import os
from datetime import datetime
from pathlib import Path

from vault import unlock_vault


def _atomic_copy(source, destination):
    """
    Copia un archivo utilizando un archivo temporal y un reemplazo atomico.
    """
    source = Path(source)
    destination = Path(destination)

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = destination.with_suffix(
        destination.suffix + ".tmp"
    )

    temporary_path.write_bytes(
        source.read_bytes()
    )

    os.replace(
        temporary_path,
        destination,
    )


def list_backups(backup_dir):
    """
    Devuelve los backups disponibles, del mas reciente al mas antiguo.
    """
    backup_dir = Path(backup_dir)

    if not backup_dir.exists():
        return []

    return sorted(
        backup_dir.glob("*.vault"),
        key=lambda path: path.name,
        reverse=True,
    )


def prune_backups(backup_dir, keep=10):
    """
    Conserva solamente una cantidad limitada de backups automaticos.
    """
    if keep is None:
        return

    if keep < 1:
        raise ValueError(
            "La cantidad de backups a conservar debe ser al menos 1."
        )

    automatic_backups = sorted(
        Path(backup_dir).glob("vault-backup-*.vault"),
        key=lambda path: path.name,
        reverse=True,
    )

    for old_backup in automatic_backups[keep:]:
        old_backup.unlink(missing_ok=True)


def create_backup(
    vault_path,
    backup_dir,
    prefix="vault-backup",
    keep=10,
):
    """
    Crea una copia del archivo de boveda ya cifrado.

    No descifra ni vuelve a cifrar credenciales.
    """
    vault_path = Path(vault_path)
    backup_dir = Path(backup_dir)

    if not vault_path.is_file():
        raise FileNotFoundError(
            "No existe una boveda para respaldar."
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )

    backup_path = backup_dir / (
        f"{prefix}-{timestamp}.vault"
    )

    _atomic_copy(
        vault_path,
        backup_path,
    )

    if prefix == "vault-backup":
        prune_backups(
            backup_dir,
            keep=keep,
        )

    return backup_path


def restore_backup(
    backup_path,
    vault_path,
    master_password,
    backup_dir,
):
    """
    Verifica un backup con su contraseña maestra y luego lo restaura.

    Antes de reemplazar la boveda actual crea una copia de seguridad
    de su estado presente.
    """
    backup_path = Path(backup_path)
    vault_path = Path(vault_path)
    backup_dir = Path(backup_dir)

    if not backup_path.is_file():
        raise FileNotFoundError(
            "El backup seleccionado no existe."
        )

    # Verificamos primero el backup. Si la contraseña es incorrecta,
    # esta llamada falla y la boveda actual permanece intacta.
    unlock_vault(
        backup_path,
        master_password,
    )

    safety_backup = None

    if vault_path.is_file():
        safety_backup = create_backup(
            vault_path,
            backup_dir,
            prefix="pre-restore",
            keep=None,
        )

    _atomic_copy(
        backup_path,
        vault_path,
    )

    # Volvemos a abrir el destino restaurado para comprobar que la copia
    # final es valida y obtener una sesion que corresponda a ese backup.
    vault_data, session = unlock_vault(
        vault_path,
        master_password,
    )

    return vault_data, session, safety_backup
