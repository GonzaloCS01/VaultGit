import uuid


def add_account(
    vault_data,
    service,
    username,
    password,
    url="",
    notes="",
):
    """
    Añade una nueva cuenta a la boveda.
    """

    account = {
        "id": uuid.uuid4().hex,
        "service": service.strip(),
        "username": username.strip(),
        "password": password,
        "url": url.strip(),
        "notes": notes.strip(),
    }

    vault_data.setdefault("accounts", []).append(account)

    return account


def get_accounts(vault_data):
    """
    Devuelve todas las cuentas almacenadas.
    """

    return vault_data.get("accounts", [])


def search_accounts(vault_data, query):
    """
    Busca cuentas por servicio o usuario.
    """

    query = query.strip().lower()

    results = []

    for account in get_accounts(vault_data):
        service = account.get(
            "service",
            "",
        ).lower()

        username = account.get(
            "username",
            "",
        ).lower()

        if query in service or query in username:
            results.append(account)

    return results