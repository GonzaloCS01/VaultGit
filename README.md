# VaultGit

<p align="center">
  <img src="assets/vaultgit-logo.png" alt="VaultGit logo" width="180">
</p>

<p align="center">
  <strong>Encrypted Credential Manager</strong><br>
  Local-first password vault for Windows, built with Python.
</p>

---

## Overview

VaultGit is a desktop credential manager designed to store account credentials inside an encrypted local vault rather than in plaintext files, notes, spreadsheets, chats, or source code.

The project was built from scratch as a cybersecurity and software-development portfolio project, with a focus on practical defensive controls, maintainable architecture, encrypted backups, secure key derivation, tamper detection, and automated testing.

VaultGit 1.0.0 is currently designed for local Windows use.

> **Security note:** VaultGit is an educational and portfolio project. It has not undergone an independent professional security audit. It should not be presented as “unhackable” or as a replacement for a professionally audited enterprise password manager.

---

## Features

- Encrypted local credential vault
- Argon2id password-based key derivation
- XChaCha20-Poly1305 authenticated encryption
- Configurable KDF parameters stored per vault
- Secure KDF migration for older vaults
- Encrypted manual and automatic backups
- Safe restore flow with pre-restore backup
- Password generator
- Account search, add, edit, view, and delete operations
- Automatic vault locking after inactivity
- Progressive delay after failed unlock attempts
- Temporary clipboard handling for copied passwords
- Tamper detection for encrypted vault data
- Local application-data storage outside the Git repository
- Windows ACL hardening workflow
- Branded Windows desktop interface
- Reproducible PyInstaller release build
- Automated security and regression tests

---

## Security Architecture

VaultGit never stores the master password directly on disk.

```text
Master Password
      |
      v
   Argon2id
      |
      v
Derived Encryption Key
      |
      v
XChaCha20-Poly1305
      |
      v
Encrypted vault.vault
```

The vault file stores only the public cryptographic metadata required to unlock the vault plus the encrypted payload.

### Public metadata

The following values are intentionally stored outside the encrypted payload:

- Vault format version
- KDF name
- Argon2id operation limit
- Argon2id memory limit
- Random salt
- Cipher identifier
- Ciphertext

The following account information remains inside the encrypted payload:

- Internal account IDs
- Service names
- Usernames / email addresses
- Passwords
- URLs
- Notes

---

## Cryptography

### Key derivation

VaultGit 1.0.0 uses:

```text
Argon2id
Operations: 4
Memory:     512 MiB
```

The parameters were selected after benchmarking multiple Argon2id profiles on the development machine.

Measured development-machine results:

| Profile | Memory | Operations | Average |
|---|---:|---:|---:|
| Moderate | 256 MiB | 3 | ~0.268 s |
| VaultGit V1 | 512 MiB | 4 | ~0.761 s |
| Sensitive | 1024 MiB | 4 | ~1.608 s |

These timings are hardware-dependent.

Each vault stores its own KDF parameters, allowing VaultGit to open older vaults and migrate them to stronger parameters later.

### Authenticated encryption

VaultGit uses XChaCha20-Poly1305 authenticated encryption through PyNaCl/libsodium.

This provides both:

- Confidentiality: encrypted credentials are not readable without the correct key.
- Integrity/authentication: modified ciphertext is rejected rather than silently accepted.

---

## Vault Location

Private user data is stored outside the repository.

On Windows:

```text
%LOCALAPPDATA%\VaultGit\
├── vault.vault
└── backups\
```

The Git repository contains application source code, tests, assets, and packaging configuration, but not the user's vault or backups.

---

## Backups and Recovery

VaultGit backups are encrypted copies of the vault.

Supported workflows include:

- Manual encrypted backups
- Automatic backup before selected sensitive changes
- Pre-restore backup creation
- KDF-upgrade safety backup
- Password verification before restore
- Validation before replacing the active vault

Backups do not contain plaintext credentials.

---

## Desktop Security Controls

VaultGit includes several controls intended to reduce accidental exposure during normal use:

- Passwords hidden by default
- Temporary clipboard cleanup
- Automatic locking after inactivity
- Progressive unlock throttling after incorrect passwords
- Data storage under the user's local application-data directory
- Windows filesystem permission review/hardening
- Encrypted backups
- No master-password storage on disk

### Threat-model limitation

VaultGit is primarily designed to protect credentials **at rest** and to reduce exposure while the application is in use.

If the operating system is already fully compromised by malware running with the user's privileges, an attacker may still be able to perform keylogging, screen capture, process-memory inspection, or similar attacks.

No local password manager can make secrets impossible to obtain from a fully compromised endpoint.

---

## Password Policy

New vaults require a master password of at least 15 characters.

VaultGit favors long, unique passphrases rather than forcing arbitrary composition rules such as mandatory uppercase letters, numbers, and symbols.

The master password should:

- Be unique to VaultGit
- Never be reused on another website or application
- Be long and memorable
- Never be committed to Git
- Never be stored in plaintext alongside the vault

---

## Automated Tests

The VaultGit test suite currently covers areas such as:

- Encryption and decryption
- Incorrect-password rejection
- Ciphertext tampering
- Invalid vault format handling
- Account CRUD operations
- Password generation
- Backup creation and restoration
- KDF-profile compatibility
- KDF migration
- Private application-data paths
- Metadata privacy
- Progressive unlock throttling
- GUI integration
- Branding configuration
- Windows packaging configuration

At the VaultGit 1.0.0 release-preparation stage, the project reached:

```text
69 automated tests passing
```

Run the complete suite with:

```powershell
python -m pytest -v
```

---

## Development Setup

### Requirements

- Windows 10 or Windows 11
- Python 3
- Git

Clone the repository and enter the project directory:

```powershell
git clone <YOUR-REPOSITORY-URL>
cd VaultGit
```

Create a virtual environment:

```powershell
py -m venv .venv
```

If PowerShell blocks environment activation for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the desktop application:

```powershell
python .\src\gui.py
```

Run tests:

```powershell
python -m pytest -v
```

---

## Building the Windows Executable

VaultGit includes reproducible PyInstaller packaging configuration.

Build the release with:

```powershell
.\packaging\build_release.ps1
```

The script:

1. Runs the automated test suite
2. Removes old build artifacts
3. Builds the Windows executable
4. Verifies that the executable was produced
5. Prints the executable size
6. Calculates its SHA-256 hash

Expected output:

```text
dist\VaultGit.exe
```

The encrypted user vault and backups are **not embedded in the executable**.

---

## Project Structure

```text
VaultGit/
├── assets/
│   ├── vaultgit-logo.png
│   ├── vaultgit-icon-256.png
│   └── vaultgit.ico
│
├── packaging/
│   ├── VaultGit.spec
│   ├── build_release.ps1
│   └── version_info.txt
│
├── src/
│   ├── accounts.py
│   ├── app_config.py
│   ├── auth_guard.py
│   ├── backup.py
│   ├── crypto.py
│   ├── data_migration.py
│   ├── generator.py
│   ├── gui.py
│   ├── main.py
│   ├── password_policy.py
│   ├── paths.py
│   └── vault.py
│
├── tests/
├── tools/
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Design Goals

VaultGit was designed around the following principles:

1. Never store account passwords in plaintext.
2. Never store the master password on disk.
3. Keep sensitive user data outside the source repository.
4. Use authenticated encryption rather than encryption alone.
5. Make cryptographic parameters upgradeable.
6. Keep backups encrypted.
7. Test security-sensitive behavior automatically.
8. Prefer clear failure over silent corruption.
9. Separate application code from private user data.
10. Document limitations instead of claiming perfect security.

---

## Roadmap

Possible future improvements after the 1.0.0 release include:

- Windows Hello integration
- Additional memory-hardening techniques
- Import/export workflows
- Password-health analysis
- Optional breach-check integration
- Better accessibility and UI scaling
- Installer/MSIX packaging
- Code signing
- Additional platform support
- Independent security review

---

## Author

**Gonzalo Cessua**  
Cybersecurity & Software Development

VaultGit was created as a security-focused portfolio project demonstrating practical cryptography, defensive software design, secure local storage, automated testing, and Windows application packaging.

© 2026 Gonzalo Cessua
