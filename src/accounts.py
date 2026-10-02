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

def get_account_by_id(vault_data, account_id):
    """
    Busca una cuenta por su identificador unico.
    """

    for account in get_accounts(vault_data):
        if account.get("id") == account_id:
            return account

    return None


def update_account(
    vault_data,
    account_id,
    service=None,
    username=None,
    password=None,
    url=None,
    notes=None,
):
    """
    Actualiza una cuenta existente.
    """

    account = get_account_by_id(
        vault_data,
        account_id,
    )

    if account is None:
        return False

    if service is not None:
        account["service"] = service.strip()

    if username is not None:
        account["username"] = username.strip()

    if password is not None:
        account["password"] = password

    if url is not None:
        account["url"] = url.strip()

    if notes is not None:
        account["notes"] = notes.strip()

    return True


def delete_account(vault_data, account_id):
    """
    Elimina una cuenta de la boveda.
    """

    accounts = get_accounts(vault_data)

    for account in accounts:
        if account.get("id") == account_id:
            accounts.remove(account)
            return True

    return False