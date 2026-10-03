import sys
from pathlib import Path


SRC_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
)

sys.path.insert(
    0,
    str(SRC_PATH),
)


from app_config import (
    APP_AUTHOR,
    APP_AUTHOR_ROLE,
    APP_ICON_ICO_PATH,
    APP_ICON_PNG_PATH,
    APP_LOGO_PATH,
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    ASSETS_DIR,
    PROJECT_ROOT,
    get_about_text,
    get_window_title,
)


def test_application_identity_is_centralized():
    assert APP_NAME == "VaultGit"
    assert APP_VERSION == "1.0.0"

    assert (
        APP_TAGLINE
        == "Encrypted Credential Manager"
    )

    assert APP_AUTHOR == "Gonzalo Cessua"

    assert (
        APP_AUTHOR_ROLE
        == "Cybersecurity & Software Development"
    )


def test_window_title_uses_name_and_version():
    assert (
        get_window_title()
        == "VaultGit 1.0.0"
    )


def test_about_text_contains_branding_and_credits():
    text = get_about_text()

    assert "VaultGit 1.0.0" in text

    assert (
        "Encrypted Credential Manager"
        in text
    )

    assert "Gonzalo Cessua" in text

    assert (
        "Cybersecurity & Software Development"
        in text
    )

    assert "2026" in text


def test_assets_directory_is_inside_project_during_development():
    expected = (
        PROJECT_ROOT
        / "assets"
    )

    assert ASSETS_DIR == expected


def test_brand_asset_filenames_are_stable():
    assert (
        APP_LOGO_PATH.name
        == "vaultgit-logo.png"
    )

    assert (
        APP_ICON_PNG_PATH.name
        == "vaultgit-icon-256.png"
    )

    assert (
        APP_ICON_ICO_PATH.name
        == "vaultgit.ico"
    )


def test_brand_assets_exist():
    assert APP_LOGO_PATH.is_file()
    assert APP_ICON_PNG_PATH.is_file()
    assert APP_ICON_ICO_PATH.is_file()
