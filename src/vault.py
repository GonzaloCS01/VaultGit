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

KDF_OPSLIMIT = pwhash.argon2id.OPSLIMIT_MODERATE
KDF_MEMLIMIT = pwhash.argon2id.MEMLIMIT_MODERATE


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
    Crea una nueva boveda y deriva una nueva clave.
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

    Devuelve:
        vault_data
        session
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

    No necesita conservar la contraseña maestra.
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

    Esta funcion sigue siendo utilizada por
    nuestra version de terminal.
    """

    create_vault(
        path,
        master_password,
        vault_data,
    )