from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_packaging_files_exist():
    packaging = PROJECT_ROOT / "packaging"

    assert (
        packaging
        / "VaultGit.spec"
    ).is_file()

    assert (
        packaging
        / "version_info.txt"
    ).is_file()

    assert (
        packaging
        / "build_release.ps1"
    ).is_file()


def test_spec_contains_required_security_dependencies():
    spec = (
        PROJECT_ROOT
        / "packaging"
        / "VaultGit.spec"
    ).read_text(
        encoding="utf-8"
    )

    assert '"_cffi_backend"' in spec
    assert 'collect_all(' in spec
    assert '"nacl"' in spec


def test_spec_embeds_brand_assets_and_version_resource():
    spec = (
        PROJECT_ROOT
        / "packaging"
        / "VaultGit.spec"
    ).read_text(
        encoding="utf-8"
    )

    assert '"assets"' in spec
    assert '"vaultgit.ico"' in spec
    assert '"version_info.txt"' in spec
    assert 'console=False' in spec


def test_build_script_runs_tests_before_packaging():
    script = (
        PROJECT_ROOT
        / "packaging"
        / "build_release.ps1"
    ).read_text(
        encoding="utf-8"
    )

    pytest_position = script.find(
        "-m pytest"
    )

    pyinstaller_position = script.find(
        "-m PyInstaller"
    )

    assert pytest_position != -1
    assert pyinstaller_position != -1
    assert pytest_position < pyinstaller_position
