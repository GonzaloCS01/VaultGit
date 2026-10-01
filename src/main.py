from nacl.exceptions import CryptoError

from crypto import (
    generate_salt,
    derive_key,
    encrypt_text,
    decrypt_text,
)


def main():
    master_password = "ClaveDePrueba123!"

    salt = generate_salt()
    key = derive_key(master_password, salt)

    test_data = (
        "Servicio: ExampleMail | "
        "Usuario: usuario@ejemplo.com | "
        "Password: Demo-8472!"
    )

    encrypted = encrypt_text(key, test_data)
    decrypted = decrypt_text(key, encrypted)

    print("VaultGit - prueba criptografica")
    print("--------------------------------")
    print("Salt generado:", salt.hex())
    print("Longitud de clave:", len(key), "bytes")
    print("Datos originales:", test_data)
    print("Datos cifrados:", encrypted.hex()[:80] + "...")
    print("Datos descifrados:", decrypted)

    wrong_key = derive_key(
        "PasswordIncorrecta!",
        salt,
    )

    try:
        decrypt_text(wrong_key, encrypted)

        print("ERROR: La clave incorrecta pudo descifrar los datos.")

    except CryptoError:
        print("Prueba correcta: una contraseña incorrecta NO puede descifrar la información.")


if __name__ == "__main__":
    main()