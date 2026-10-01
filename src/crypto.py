from nacl import pwhash, secret, utils


AAD = b"VaultGit:v1"


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


def encrypt_text(key, plaintext):
    """
    Cifra texto utilizando XChaCha20-Poly1305.
    """
    box = secret.Aead(key)

    plaintext_bytes = plaintext.encode("utf-8")

    encrypted = box.encrypt(
        plaintext_bytes,
        AAD,
    )

    return bytes(encrypted)


def decrypt_text(key, encrypted):
    """
    Descifra información previamente cifrada.
    """
    box = secret.Aead(key)

    plaintext_bytes = box.decrypt(
        encrypted,
        AAD,
    )

    return plaintext_bytes.decode("utf-8")