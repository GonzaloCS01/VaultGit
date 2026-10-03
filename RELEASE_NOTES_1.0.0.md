# VaultGit 1.0.0

## First Public Portfolio Release

VaultGit 1.0.0 is the first packaged Windows release of the VaultGit encrypted credential manager.

### Highlights

- Local encrypted credential vault
- Argon2id master-password key derivation
- XChaCha20-Poly1305 authenticated encryption
- Account management interface
- Password generator
- Encrypted backup and recovery system
- KDF migration support
- Automatic inactivity locking
- Progressive failed-unlock delays
- Temporary clipboard handling
- Private `%LOCALAPPDATA%` storage
- Vault metadata privacy tests
- Windows branding and application icon
- Reproducible PyInstaller build
- 69 automated tests passing at release preparation

### Windows Build

Expected binary:

```text
VaultGit.exe
```

User data remains outside the executable under:

```text
%LOCALAPPDATA%\VaultGit
```

### Important

VaultGit is a security-focused portfolio project and has not undergone an independent professional security audit.

Do not distribute real vault data, backups, or master passwords with the application.
