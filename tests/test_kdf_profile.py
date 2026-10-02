import base64
import json
import sys
from pathlib import Path

from nacl import pwhash, secret, utils


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from crypto import (
    encrypt_text,
    derive_key,
)
from vault import (
    KDF_MEMLIMIT,
    KDF_OPSLIMIT,
    create_vault,
    load_vault,
)


MIB = 1024 * 1024


def test_new_vault_uses_v1_kdf_profile(tmp_path):
    vault_path = tmp_path / "new-profile.vault"

    create_vault(
        vault_path,
        "Frase-maestra-de-prueba-2026!",
        {
            "accounts": []
        },
    )

    raw = json.loads(
        vault_path.read_text(
            encoding="utf-8"
        )
    )

    assert KDF_OPSLIMIT == 4
    assert KDF_MEMLIMIT == 512 * MIB

    assert raw["kdf"]["opslimit"] == 4
    assert raw["kdf"]["memlimit"] == 512 * MIB


def test_old_moderate_vault_remains_compatible(
    tmp_path,
):
    """
    Simula una boveda antigua creada con el perfil
    MODERATE (3 operaciones / 256 MiB) y comprueba
    que la nueva version de VaultGit aun puede abrirla.
    """

    vault_path = tmp_path / "old-profile.vault"

    password = "Frase-maestra-antigua-de-prueba!"
    password_bytes = password.encode("utf-8")

    salt = utils.random(
        pwhash.argon2id.SALTBYTES
    )

    old_opslimit = (
        pwhash.argon2id.OPSLIMIT_MODERATE
    )

    old_memlimit = (
        pwhash.argon2id.MEMLIMIT_MODERATE
    )

    key = derive_key(
        password,
        salt,
        opslimit=old_opslimit,
        memlimit=old_memlimit,
    )

    plaintext = (
        '{"accounts":[{"id":"demo","service":"Legacy",'
        '"username":"legacy@example.com","password":"Demo!",'
        '"url":"","notes":""}]}'
    )

    encrypted = encrypt_text(
        key,
        plaintext,
    )

    old_vault = {
        "version": 1,
        "kdf": {
            "name": "argon2id",
            "opslimit": old_opslimit,
            "memlimit": old_memlimit,
            "salt": base64.b64encode(
                salt
            ).decode("ascii"),
        },
        "cipher": "xchacha20-poly1305",
        "ciphertext": base64.b64encode(
            encrypted
        ).decode("ascii"),
    }

    vault_path.write_text(
        json.dumps(
            old_vault,
            indent=2,
        ),
        encoding="utf-8",
    )

    reopened = load_vault(
        vault_path,
        password,
    )

    assert (
        reopened["accounts"][0]["service"]
        == "Legacy"
    )
