import secrets
import string


SAFE_SYMBOLS = "!@#$%^&*()-_=+[]{}:,.?"


def generate_password(
    length=20,
    use_uppercase=True,
    use_lowercase=True,
    use_digits=True,
    use_symbols=True,
):
    """
    Genera una contraseña utilizando aleatoriedad
    criptograficamente segura.
    """

    character_sets = []

    if use_uppercase:
        character_sets.append(
            string.ascii_uppercase
        )

    if use_lowercase:
        character_sets.append(
            string.ascii_lowercase
        )

    if use_digits:
        character_sets.append(
            string.digits
        )

    if use_symbols:
        character_sets.append(
            SAFE_SYMBOLS
        )

    if not character_sets:
        raise ValueError(
            "Debe seleccionarse al menos "
            "un tipo de caracter."
        )

    if length < len(character_sets):
        raise ValueError(
            "La longitud es demasiado corta "
            "para los tipos seleccionados."
        )

    password_characters = []

    # Garantizamos al menos un caracter
    # de cada grupo seleccionado.
    for characters in character_sets:
        password_characters.append(
            secrets.choice(characters)
        )

    all_characters = "".join(
        character_sets
    )

    remaining_length = (
        length - len(password_characters)
    )

    for _ in range(remaining_length):
        password_characters.append(
            secrets.choice(all_characters)
        )

    # Mezclamos la posicion de todos los caracteres.
    secure_random = secrets.SystemRandom()

    secure_random.shuffle(
        password_characters
    )

    return "".join(password_characters)