import math
import time


class UnlockThrottle:
    """
    Controla intentos repetidos de desbloqueo dentro
    de una sesion de VaultGit.

    No almacena contraseñas ni hashes.
    No sustituye Argon2id.
    Solo añade una espera progresiva en la interfaz
    después de intentos fallidos.
    """

    DELAYS = (
        1,
        2,
        5,
        10,
        30,
        60,
    )

    def __init__(self, clock=None):
        self._clock = clock or time.monotonic
        self.failures = 0
        self.blocked_until = 0.0

    def can_attempt(self):
        """
        True si ya puede realizarse otro intento.
        """
        return self._clock() >= self.blocked_until

    def remaining_seconds(self):
        """
        Segundos enteros restantes de espera.
        """
        remaining = (
            self.blocked_until
            - self._clock()
        )

        if remaining <= 0:
            return 0

        return math.ceil(
            remaining
        )

    def next_delay(self):
        """
        Devuelve el retardo correspondiente al próximo
        fallo según el número de fallos acumulados.
        """

        index = min(
            self.failures,
            len(self.DELAYS) - 1,
        )

        return self.DELAYS[
            index
        ]

    def record_failure(self):
        """
        Registra un intento incorrecto y activa
        el siguiente retardo progresivo.
        """

        delay = self.next_delay()

        self.failures += 1

        self.blocked_until = (
            self._clock()
            + delay
        )

        return delay

    def record_success(self):
        """
        Un desbloqueo correcto reinicia completamente
        el contador de fallos.
        """

        self.failures = 0
        self.blocked_until = 0.0

    def reset(self):
        """
        Reinicio explícito del estado.
        """

        self.record_success()
