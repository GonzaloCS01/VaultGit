from crypto import generate_salt, derive_key


def main():
    master_password = "ClaveDePrueba123!"

    salt = generate_salt()
    key = derive_key(master_password, salt)

    print("VaultGit iniciado correctamente.")
    print("Salt generado:", salt.hex())
    print("Longitud de la clave:", len(key), "bytes")


if __name__ == "__main__":
    main()