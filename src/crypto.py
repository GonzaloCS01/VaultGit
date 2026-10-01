from nacl import pwhash, secret, utils


def generate_salt():
    """
    Genera un salt aleatorio para Argon2id.
    """
    return utils.random(pwhash.argon2id.SALTBYTES)


def derive_key(master_password, salt):
    """
    Deriva una clave criptografica de 32 bytes
    desde la contraseña maestra usando Argon2id.
    """

    password_bytes = master_password.encode("utf-8")

    key = pwhash.argon2id.kdf(
        secret.Aead.KEY_SIZE,
        password_bytes,
        salt,
        opslimit=pwhash.argon2id.OPSLIMIT_MODERATE,
        memlimit=pwhash.argon2id.MEMLIMIT_MODERATE,
    )

    return key