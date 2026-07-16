"""
Домашнее задание 2: Race Condition и Lock 🔒
"""

import threading
import time


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 2.1 — Имитация гонки
# ═══════════════════════════════════════════════════════════


def increment_with_race(counter: list[int], times: int) -> None:
    """Увеличить counter[0] на times, НО с гонкой."""
    for _ in range(times):
        current = counter[0]
        time.sleep(0.000001)
        counter[0] = current + 1


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 2.2 — Исправление через Lock
# ═══════════════════════════════════════════════════════════


def increment_safe(counter: list[int], times: int, lock: threading.Lock) -> None:
    """Увеличить counter[0] на times, БЕЗ гонки."""
    for _ in range(times):
        with lock:
            counter[0] += 1


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 2.3 — Банковский счёт (повышенная сложность)
# ═══════════════════════════════════════════════════════════


class InsufficientFundsError(Exception):
    """Исключение: недостаточно средств на счёте."""

    pass


class BankAccount:
    """Потокобезопасный банковский счёт."""

    def __init__(self, initial_balance: float = 0.0) -> None:
        self.balance = initial_balance
        self._lock = threading.Lock()

    def deposit(self, amount: float) -> None:
        with self._lock:
            self.balance += amount

    def withdraw(self, amount: float) -> None:
        with self._lock:
            if amount > self.balance:
                raise InsufficientFundsError(
                    f"Недостаточно средств: баланс {self.balance}, запрошено {amount}"
                )
            self.balance -= amount

    def get_balance(self) -> float:
        with self._lock:
            return self.balance
