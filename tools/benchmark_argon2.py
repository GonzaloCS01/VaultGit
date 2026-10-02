import statistics
import sys
import time
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from nacl import pwhash, secret, utils


TEST_PASSWORD = (
    "VaultGit-Benchmark-Password-2026!"
)

RUNS = 5


def benchmark_argon2id():
    salt = utils.random(
        pwhash.argon2id.SALTBYTES
    )

    times = []

    print()
    print("VaultGit - Argon2id Benchmark")
    print("============================")
    print()

    print(
        "OPSLIMIT:",
        pwhash.argon2id.OPSLIMIT_MODERATE,
    )

    print(
        "MEMLIMIT:",
        pwhash.argon2id.MEMLIMIT_MODERATE,
        "bytes",
    )

    print()

    for run_number in range(
        1,
        RUNS + 1,
    ):
        start = time.perf_counter()

        pwhash.argon2id.kdf(
            secret.Aead.KEY_SIZE,
            TEST_PASSWORD.encode("utf-8"),
            salt,
            opslimit=(
                pwhash.argon2id.OPSLIMIT_MODERATE
            ),
            memlimit=(
                pwhash.argon2id.MEMLIMIT_MODERATE
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

    average = statistics.mean(
        times
    )

    median = statistics.median(
        times
    )

    print()
    print("----------------------------")

    print(
        f"Promedio: {average:.3f} segundos"
    )

    print(
        f"Mediana:  {median:.3f} segundos"
    )

    print()


if __name__ == "__main__":
    benchmark_argon2id()