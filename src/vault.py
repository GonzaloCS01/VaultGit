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
    Convierte bytes en texto Base64 para poder guardarlos en JSON.
    """
    return base64.b64encode(data).decode("ascii")


def decode_base64(data):
    """
    Convierte texto Base64 nuevamente en bytes.
    """
    return base64.b64decode(data, validate=True)


def create_vault(path, master_password, vault_data):
    """
    Crea una nueva boveda cifrada.
    """
    path = Path(path)

    salt = generate_salt()

    key = derive_key(
        master_password,
        salt,
        opslimit=KDF_OPSLIMIT,
        memlimit=KDF_MEMLIMIT,
    )

    plaintext = json.dumps(
        vault_data,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    encrypted = encrypt_text(key, plaintext)

    vault_file = {
        "version": VAULT_VERSION,
        "kdf": {
            "name": "argon2id",
            "opslimit": KDF_OPSLIMIT,
            "memlimit": KDF_MEMLIMIT,
            "salt": encode_base64(salt),
        },
        "cipher": "xchacha20-poly1305",
        "ciphertext": encode_base64(encrypted),
    }

    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(path.suffix + ".tmp")

    temporary_path.write_text(
        json.dumps(vault_file, indent=2),
        encoding="utf-8",
    )

    os.replace(temporary_path, path)


def load_vault(path, master_password):
    """
    Abre y descifra una boveda existente.
    """
    path = Path(path)

    vault_file = json.loads(
        path.read_text(encoding="utf-8")
    )

    if vault_file.get("version") != VAULT_VERSION:
        raise ValueError("Version de boveda no compatible.")

    if vault_file["kdf"]["name"] != "argon2id":
        raise ValueError("KDF no compatible.")

    if vault_file["cipher"] != "xchacha20-poly1305":
        raise ValueError("Cifrado no compatible.")

    salt = decode_base64(
        vault_file["kdf"]["salt"]
    )

    encrypted = decode_base64(
        vault_file["ciphertext"]
    )

    key = derive_key(
        master_password,
        salt,
        opslimit=int(vault_file["kdf"]["opslimit"]),
        memlimit=int(vault_file["kdf"]["memlimit"]),
    )

    plaintext = decrypt_text(
        key,
        encrypted,
    )

    return json.loads(plaintext)