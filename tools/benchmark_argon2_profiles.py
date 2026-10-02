import statistics
import time

from nacl import pwhash, secret, utils


TEST_PASSWORD = (
    "VaultGit-Benchmark-Password-2026!"
)

RUNS = 3

MIB = 1024 * 1024


PROFILES = [
    {
        "name": "MODERATE",
        "opslimit": (
            pwhash.argon2id.OPSLIMIT_MODERATE
        ),
        "memlimit": (
            pwhash.argon2id.MEMLIMIT_MODERATE
        ),
    },
    {
        "name": "CUSTOM_512",
        "opslimit": 4,
        "memlimit": 512 * MIB,
    },
    {
        "name": "SENSITIVE",
        "opslimit": (
            pwhash.argon2id.OPSLIMIT_SENSITIVE
        ),
        "memlimit": (
            pwhash.argon2id.MEMLIMIT_SENSITIVE
        ),
    },
]


def benchmark_profile(profile):
    salt = utils.random(
        pwhash.argon2id.SALTBYTES
    )

    times = []

    print()
    print(
        f"Perfil: {profile['name']}"
    )

    print(
        "OPSLIMIT:",
        profile["opslimit"],
    )

    print(
        "MEMLIMIT:",
        profile["memlimit"],
        "bytes",
    )

    print(
        "Memoria aproximada:",
        round(
            profile["memlimit"] / MIB
        ),
        "MiB",
    )

    print()

    for run_number in range(
        1,
        RUNS + 1,
    ):
        start = time.perf_counter()

        pwhash.argon2id.kdf(
            secret.Aead.KEY_SIZE,
            TEST_PASSWORD.encode(
                "utf-8"
            ),
            salt,
            opslimit=(
                profile["opslimit"]
            ),
            memlimit=(
                profile["memlimit"]
            ),
        )

        elapsed = (
            time.perf_counter()
            - start
        )

        times.append(
            elapsed
        )

        print(
            f"Ejecucion {run_number}: "
            f"{elapsed:.3f} segundos"
        )

    print()

    print(
        "Promedio:",
        f"{statistics.mean(times):.3f}",
        "segundos",
    )

    print(
        "Mediana:",
        f"{statistics.median(times):.3f}",
        "segundos",
    )

    print(
        "-" * 40
    )


def main():
    print()
    print(
        "VaultGit - Comparacion Argon2id"
    )

    print(
        "=" * 40
    )

    for profile in PROFILES:
        benchmark_profile(
            profile
        )


if __name__ == "__main__":
    main()