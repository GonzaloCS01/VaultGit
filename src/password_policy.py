import unicodedata


MIN_MASTER_PASSWORD_LENGTH = 15
MAX_MASTER_PASSWORD_LENGTH = 128


COMMON_MASTER_PASSWORDS = {
    "123456789012345",
    "1234567890123456",
    "qwertyuiopasdfgh",
    "passwordpassword",
    "password123456",
    "password123456789",
    "letmeinletmein",
    "adminadminadmin",
    "iloveyouiloveyou",
    "contraseña123456",
    "contrasena123456",
}


def normalize_password_for_blocklist(password):
    """
    Normaliza el texto únicamente para compararlo
    con la pequeña lista local de contraseñas débiles.
    """
    return unicodedata.normalize(
        "NFKC",
        password,
    ).casefold()


def validate_master_password(password):
    """
    Valida la contraseña maestra de VaultGit.

    No obliga a usar mayúsculas, números o símbolos.
    Priorizamos longitud y evitamos algunas contraseñas
    extremadamente comunes y predecibles.

    Devuelve:
        (True, "") si es aceptable.
        (False, "mensaje") si debe rechazarse.
    """

    if not isinstance(password, str):
        return (
            False,
            "La contraseña maestra debe ser texto.",
        )

    if len(password) < MIN_MASTER_PASSWORD_LENGTH:
        return (
            False,
            (
                "Utiliza una contraseña maestra de al menos "
                f"{MIN_MASTER_PASSWORD_LENGTH} caracteres.\n\n"
                "Una frase larga y única suele ser más fácil "
                "de recordar que una contraseña corta y compleja."
            ),
        )

    if len(password) > MAX_MASTER_PASSWORD_LENGTH:
        return (
            False,
            (
                "La contraseña maestra es demasiado larga para "
                f"esta versión de VaultGit. Máximo: "
                f"{MAX_MASTER_PASSWORD_LENGTH} caracteres."
            ),
        )

    normalized = normalize_password_for_blocklist(
        password
    )

    if normalized in COMMON_MASTER_PASSWORDS:
        return (
            False,
            (
                "Esa contraseña maestra es demasiado común "
                "o predecible. Elige una frase larga, única "
                "y que no reutilices en ningún otro servicio."
            ),
        )

    return True, ""
