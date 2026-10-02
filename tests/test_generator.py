import sys
from pathlib import Path

import pytest


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from generator import (
    SAFE_SYMBOLS,
    generate_password,
)


def test_default_password_length():
    password = generate_password()

    assert len(password) == 20


def test_password_contains_all_character_types():
    password = generate_password(
        length=32
    )

    assert any(
        character.isupper()
        for character in password
    )

    assert any(
        character.islower()
        for character in password
    )

    assert any(
        character.isdigit()
        for character in password
    )

    assert any(
        character in SAFE_SYMBOLS
        for character in password
    )


def test_custom_password_length():
    password = generate_password(
        length=40
    )

    assert len(password) == 40


def test_no_character_types_raises_error():
    with pytest.raises(ValueError):
        generate_password(
            use_uppercase=False,
            use_lowercase=False,
            use_digits=False,
            use_symbols=False,
        )


def test_too_short_password_raises_error():
    with pytest.raises(ValueError):
        generate_password(
            length=3,
            use_uppercase=True,
            use_lowercase=True,
            use_digits=True,
            use_symbols=True,
        )