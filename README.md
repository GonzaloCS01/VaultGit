\# VaultGit



VaultGit is a personal encrypted password vault built with Python.



The objective of this project is to create a simple and secure application for storing personal credentials while learning practical concepts related to cybersecurity, cryptography, Python and Git.



\## Project Status



🚧 Currently under development.



\## Planned Features



\- Master password protection

\- Encrypted credential storage

\- Password generator

\- Search and manage accounts

\- Automatic clipboard clearing

\- Automatic vault locking

\- Encrypted backups

\- Optional GitHub synchronization



\## Security Goals



VaultGit will be designed so that sensitive credentials are never stored in plaintext.



Planned security mechanisms include:



\- Argon2id key derivation

\- XChaCha20-Poly1305 authenticated encryption

\- Random salts and nonces

\- Local encrypted vault

\- Protection against accidental secret commits



\## Current Structure



```text

VaultGit/

├── data/

├── src/

│   └── main.py

├── tests/

├── .gitignore

└── README.md



Disclaimer

VaultGit is an educational cybersecurity project currently under development.

Real credentials should not be stored in the application until the security implementation has been completed and tested.





