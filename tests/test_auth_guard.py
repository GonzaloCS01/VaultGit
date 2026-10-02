import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


from auth_guard import UnlockThrottle


class FakeClock:
    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def test_initial_state_allows_attempt():
    clock = FakeClock()
    guard = UnlockThrottle(
        clock=clock
    )

    assert guard.can_attempt() is True
    assert guard.remaining_seconds() == 0
    assert guard.failures == 0


def test_first_failure_blocks_for_one_second():
    clock = FakeClock()
    guard = UnlockThrottle(
        clock=clock
    )

    delay = guard.record_failure()

    assert delay == 1
    assert guard.can_attempt() is False
    assert guard.remaining_seconds() == 1
    assert guard.failures == 1


def test_delays_increase_progressively():
    clock = FakeClock()
    guard = UnlockThrottle(
        clock=clock
    )

    observed_delays = []

    for _ in range(6):
        delay = guard.record_failure()
        observed_delays.append(
            delay
        )

        clock.advance(
            delay
        )

    assert observed_delays == [
        1,
        2,
        5,
        10,
        30,
        60,
    ]


def test_delay_is_capped_at_sixty_seconds():
    clock = FakeClock()
    guard = UnlockThrottle(
        clock=clock
    )

    for _ in range(10):
        delay = guard.record_failure()
        clock.advance(
            delay
        )

    assert delay == 60


def test_wait_expires_without_resetting_failure_count():
    clock = FakeClock()
    guard = UnlockThrottle(
        clock=clock
    )

    guard.record_failure()

    assert guard.can_attempt() is False

    clock.advance(1)

    assert guard.can_attempt() is True
    assert guard.failures == 1


def test_success_resets_throttle():
    clock = FakeClock()
    guard = UnlockThrottle(
        clock=clock
    )

    guard.record_failure()
    clock.advance(1)

    guard.record_failure()

    assert guard.failures == 2

    guard.record_success()

    assert guard.failures == 0
    assert guard.can_attempt() is True
    assert guard.remaining_seconds() == 0

    # Tras un éxito, el próximo fallo vuelve a 1 segundo.
    assert guard.record_failure() == 1
