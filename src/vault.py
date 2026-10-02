import base64
import json
import os
from pathlib import Path

from nacl import pwhash

from crypto import (
    generate_salt,
    derive_key,
    encrypt_text,
    decrypt_text,
)


VAULT_VERSION = 1

# Perfil por defecto de VaultGit V1.
#
# Elegido después de medir en el equipo de desarrollo:
# - 4 operaciones
# - 512 MiB de memoria
#
# Las bóvedas guardan sus propios parámetros KDF,
# por lo que las bóvedas antiguas siguen siendo compatibles.
MIB = 1024 * 1024
KDF_OPSLIMIT = 4
KDF_MEMLIMIT = 512 * MIB


def encode_base64(data):
    """
    Convierte bytes en texto Base64.
    """
    return base64.b64encode(
        data
    ).decode("ascii")


def decode_base64(data):
    """
    Convierte Base64 nuevamente en bytes.
    """
    return base64.b64decode(
        data,
        validate=True,
    )


def serialize_vault_data(vault_data):
    """
    Convierte los datos de la boveda en JSON.
    """
    return json.dumps(
        vault_data,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def write_vault_file(path, vault_file):
    """
    Escribe la boveda mediante un archivo temporal
    y despues reemplaza el archivo anterior.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            vault_file,
            indent=2,
        ),
        encoding="utf-8",
    )

    os.replace(
        temporary_path,
        path,
    )


def validate_vault_file(vault_file):
    """
    Comprueba que el formato basico de la boveda
    sea compatible con VaultGit.
    """

    if vault_file.get("version") != VAULT_VERSION:
        raise ValueError(
            "Version de boveda no compatible."
        )

    kdf = vault_file.get("kdf")

    if not isinstance(kdf, dict):
        raise ValueError(
            "Configuracion KDF invalida."
        )

    if kdf.get("name") != "argon2id":
        raise ValueError(
            "KDF no compatible."
        )

    if (
        vault_file.get("cipher")
        != "xchacha20-poly1305"
    ):
        raise ValueError(
            "Cifrado no compatible."
        )

    if "ciphertext" not in vault_file:
        raise ValueError(
            "La boveda no contiene ciphertext."
        )


def read_vault_file(path):
    """
    Lee y valida la estructura externa de una boveda.
    No descifra credenciales.
    """

    path = Path(path)

    vault_file = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    validate_vault_file(
        vault_file
    )

    return vault_file


def get_vault_kdf_profile(path):
    """
    Devuelve los parametros Argon2id almacenados
    dentro de una boveda sin descifrarla.
    """

    vault_file = read_vault_file(
        path
    )

    kdf = vault_file["kdf"]

    return {
        "name": kdf["name"],
        "opslimit": int(
            kdf["opslimit"]
        ),
        "memlimit": int(
            kdf["memlimit"]
        ),
    }


def needs_kdf_upgrade(path):
    """
    Indica si la boveda usa parametros inferiores
    al perfil por defecto actual de VaultGit.
    """

    profile = get_vault_kdf_profile(
        path
    )

    return (
        profile["opslimit"] < KDF_OPSLIMIT
        or profile["memlimit"] < KDF_MEMLIMIT
    )


def build_vault_file(
    vault_data,
    key,
    salt,
    opslimit,
    memlimit,
):
    """
    Construye la estructura cifrada que sera
    almacenada en disco.
    """

    plaintext = serialize_vault_data(
        vault_data
    )

    encrypted = encrypt_text(
        key,
        plaintext,
    )

    return {
        "version": VAULT_VERSION,
        "kdf": {
            "name": "argon2id",
            "opslimit": opslimit,
            "memlimit": memlimit,
            "salt": encode_base64(salt),
        },
        "cipher": "xchacha20-poly1305",
        "ciphertext": encode_base64(
            encrypted
        ),
    }


def create_vault(
    path,
    master_password,
    vault_data,
):
    """
    Crea una nueva boveda usando el perfil KDF
    por defecto actual de VaultGit.
    """

    salt = generate_salt()

    key = derive_key(
        master_password,
        salt,
        opslimit=KDF_OPSLIMIT,
        memlimit=KDF_MEMLIMIT,
    )

    vault_file = build_vault_file(
        vault_data,
        key,
        salt,
        KDF_OPSLIMIT,
        KDF_MEMLIMIT,
    )

    write_vault_file(
        path,
        vault_file,
    )


def unlock_vault(
    path,
    master_password,
):
    """
    Desbloquea la boveda.

    Los parametros Argon2id se leen del propio archivo,
    permitiendo abrir bovedas creadas con perfiles antiguos.

    Devuelve:
        vault_data
        session
    """

    vault_file = read_vault_file(
        path
    )

    kdf = vault_file["kdf"]

    salt = decode_base64(
        kdf["salt"]
    )

    encrypted = decode_base64(
        vault_file["ciphertext"]
    )

    opslimit = int(
        kdf["opslimit"]
    )

    memlimit = int(
        kdf["memlimit"]
    )

    key = derive_key(
        master_password,
        salt,
        opslimit=opslimit,
        memlimit=memlimit,
    )

    plaintext = decrypt_text(
        key,
        encrypted,
    )

    vault_data = json.loads(
        plaintext
    )

    session = {
        "key": key,
        "salt": salt,
        "opslimit": opslimit,
        "memlimit": memlimit,
    }

    return vault_data, session


def load_vault(
    path,
    master_password,
):
    """
    Abre una boveda y devuelve solamente sus datos.

    Se conserva para compatibilidad con la version
    de terminal de VaultGit.
    """

    vault_data, _session = unlock_vault(
        path,
        master_password,
    )

    return vault_data


def save_vault_with_session(
    path,
    session,
    vault_data,
):
    """
    Guarda cambios usando la clave derivada que
    ya existe mientras VaultGit esta desbloqueado.

    Conserva los parametros KDF de esa misma boveda.
    """

    vault_file = build_vault_file(
        vault_data,
        session["key"],
        session["salt"],
        session["opslimit"],
        session["memlimit"],
    )

    write_vault_file(
        path,
        vault_file,
    )


def save_vault(
    path,
    master_password,
    vault_data,
):
    """
    Guarda una boveda usando nuevamente
    la contraseña maestra.

    Esta funcion crea un nuevo salt y usa
    el perfil KDF por defecto actual.
    """

    create_vault(
        path,
        master_password,
        vault_data,
    )


def migrate_vault_kdf(
    path,
    master_password,
):
    """
    Migra una boveda existente al perfil KDF
    por defecto actual.

    Flujo:
    1. Desbloquea con los parametros antiguos.
    2. Genera un salt nuevo.
    3. Deriva una clave nueva con el perfil actual.
    4. Vuelve a cifrar toda la boveda.
    5. Verifica que la boveda migrada pueda abrirse.

    Devuelve:
        vault_data
        session
    """

    path = Path(path)

    original_bytes = path.read_bytes()

    # La contraseña se valida ANTES de modificar
    # cualquier byte del archivo.
    vault_data, _old_session = unlock_vault(
        path,
        master_password,
    )

    new_salt = generate_salt()

    new_key = derive_key(
        master_password,
        new_salt,
        opslimit=KDF_OPSLIMIT,
        memlimit=KDF_MEMLIMIT,
    )

    migrated_file = build_vault_file(
        vault_data,
        new_key,
        new_salt,
        KDF_OPSLIMIT,
        KDF_MEMLIMIT,
    )

    try:
        write_vault_file(
            path,
            migrated_file,
        )

        # Verificacion posterior a la escritura.
        reopened_data, session = unlock_vault(
            path,
            master_password,
        )

    except Exception:
        # Si algo falla durante la migracion/verificacion,
        # intentamos devolver el archivo a su estado exacto anterior.
        temporary_path = path.with_suffix(
            path.suffix + ".rollback.tmp"
        )

        temporary_path.write_bytes(
            original_bytes
        )

        os.replace(
            temporary_path,
            path,
        )

        raise

    return reopened_data, session
