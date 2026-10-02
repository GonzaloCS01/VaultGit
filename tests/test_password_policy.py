import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from password_policy import (
    MAX_MASTER_PASSWORD_LENGTH,
    MIN_MASTER_PASSWORD_LENGTH,
    validate_master_password,
)


def test_master_password_minimum_length_is_15():
    assert MIN_MASTER_PASSWORD_LENGTH == 15


def test_short_master_password_is_rejected():
    valid, message = validate_master_password(
        "Corta-123!"
    )

    assert valid is False
    assert "15" in message


def test_long_passphrase_is_accepted():
    valid, message = validate_master_password(
        "bosque luna cafe volcan 2026"
    )

    assert valid is True
    assert message == ""


def test_spaces_are_allowed():
    valid, _message = validate_master_password(
        "esta es una frase maestra unica"
    )

    assert valid is True


def test_common_long_password_is_rejected():
    valid, message = validate_master_password(
        "PasswordPassword"
    )

    assert valid is False
    assert "común" in message or "predecible" in message


def test_excessively_long_password_is_rejected():
    valid, message = validate_master_password(
        "A" * (MAX_MASTER_PASSWORD_LENGTH + 1)
    )

    assert valid is False
    assert "Máximo" in message
