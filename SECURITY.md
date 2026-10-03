# Security Policy

## Project Status

VaultGit 1.0.0 is a cybersecurity and software-development portfolio project.

It uses modern cryptographic primitives and includes automated security-oriented tests, but it has **not undergone an independent professional security audit**.

Do not describe VaultGit as impossible to hack or as suitable for every high-risk environment.

---

## Security Design

VaultGit currently uses:

- Argon2id for password-based key derivation
- XChaCha20-Poly1305 authenticated encryption
- Per-vault random salts
- Encrypted backups
- Versioned KDF parameters
- Automatic vault locking
- Progressive unlock throttling
- Temporary clipboard handling
- Local application-data storage outside the source repository

The master password is not intentionally stored on disk.

---

## Threat Model

VaultGit is primarily intended to defend against scenarios such as:

- Theft of the encrypted vault file
- Theft of encrypted backup files
- Accidental disclosure through source control
- Offline password-guessing attempts
- Modification of encrypted vault contents
- Accidental plaintext storage of account metadata

VaultGit does **not** claim to fully protect secrets when the operating system is already compromised.

Examples outside the strongest guarantees of the project include:

- Keyloggers
- Screen-capture malware
- Malware running with the user's privileges
- Process-memory inspection
- Compromised administrators
- Hardware-level compromise

---

## Reporting a Security Issue

If you discover a security issue, avoid publishing sensitive exploit details publicly before the issue has been reviewed.

For a public portfolio repository, open a minimal GitHub issue that states that a security problem was found without including real credentials or private data.

If a private reporting channel is added later, this section should be updated accordingly.

---

## Secrets and Test Data

Never include real credentials in:

- Git commits
- GitHub issues
- Screenshots
- Test fixtures
- Example vaults
- README examples
- Release archives

Use only fictitious credentials for development and demonstrations.
