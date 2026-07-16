"""
Домашнее задание 4: Asyncio 🔄
"""

import asyncio

# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.1 — Первая корутина
# ═══════════════════════════════════════════════════════════


async def fetch_one_async(url: str) -> str:
    """Асинхронно 'скачать' URL."""
    await asyncio.sleep(0.05)
    return f"data:{url}"


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.2 — Параллельный запуск
# ═══════════════════════════════════════════════════════════


async def fetch_all_async(urls: list[str]) -> list[str]:
    """Скачать все URL конкурентно через asyncio.gather."""
    return list(await asyncio.gather(*(fetch_one_async(url) for url in urls)))


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.3 — Групповой запуск (TaskGroup)
# ═══════════════════════════════════════════════════════════

# Вспомогательная функция — не менять


async def fetch_with_delay(name: str, delay: float, fail: bool = False) -> str:
    """Имитация асинхронной загрузки. НЕ МЕНЯТЬ."""
    await asyncio.sleep(delay)
    if fail:
        raise ValueError(f"Ошибка загрузки {name}")
    return f"data:{name}"


async def run_task_group(names: list[str]) -> dict[str, str | None]:
    """Запустить группу загрузок через asyncio.TaskGroup."""
    results: dict[str, str | None] = {}
    tasks: dict[str, asyncio.Task] = {}

    try:
        async with asyncio.TaskGroup() as tg:
            for name in names:
                fail = "bad" in name
                tasks[name] = tg.create_task(
                    fetch_with_delay(name, delay=0.1, fail=fail)
                )
    except* ValueError:
        pass

    for name, task in tasks.items():
        if task.cancelled():
            results[name] = None
            continue
        exc = task.exception()
        if exc is None:
            results[name] = task.result()
        else:
            results[name] = None

    # Если ни одной успешной задачи — вернуть пустой словарь
    if all(v is None for v in results.values()):
        return {}

    return results


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.4 — Таймауты
# ═══════════════════════════════════════════════════════════


async def fetch_with_timeout(url: str, delay: float, timeout: float) -> str:
    """Скачать URL с таймаутом."""

    async def _fetch() -> str:
        await asyncio.sleep(delay)
        return f"data:{url}"

    return await asyncio.wait_for(_fetch(), timeout=timeout)


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.5 — Отмена задач
# ═══════════════════════════════════════════════════════════


async def cancellable_worker(name: str, steps: int) -> str:
    """Корутина, которую можно отменить."""
    try:
        for step in range(steps):
            await asyncio.sleep(0.1)
            print(f"  {name}: шаг {step + 1}")
        return f"{name}: готов после {steps} шагов"
    except asyncio.CancelledError:
        print(f"  {name}: очищаю ресурсы...")
        raise


async def run_with_cancel(name: str, steps: int, cancel_after: float) -> str | None:
    """Запустить cancellable_worker и отменить через cancel_after секунд."""
    task = asyncio.create_task(cancellable_worker(name, steps))
    await asyncio.sleep(cancel_after)
    task.cancel()
    try:
        return await task
    except asyncio.CancelledError:
        return None


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.6 — Асинхронный as_completed
# ═══════════════════════════════════════════════════════════


async def fast_or_slow(name: str, delay: float) -> str:
    """Имитация быстрой или медленной загрузки. НЕ МЕНЯТЬ."""
    await asyncio.sleep(delay)
    return f"{name}: готов за {delay}с"


async def fetch_as_completed(tasks: list[tuple[str, float]]) -> list[str]:
    """Запустить загрузки и вернуть результаты по мере готовности."""
    coros = [fast_or_slow(name, delay) for name, delay in tasks]
    results: list[str] = []
    for coro in asyncio.as_completed(coros):
        result = await coro
        results.append(result)
    return results


# ═══════════════════════════════════════════════════════════
# ЗАДАНИЕ 4.7 — Смешивание sync и async (повышенная сложность)
# ═══════════════════════════════════════════════════════════


def blocking_compute(x: int) -> int:
    """CPU-bound функция: проверка на простоту. НЕ МЕНЯТЬ."""
    import math
    import time

    time.sleep(0.01)
    for i in range(2, int(math.sqrt(x)) + 1):
        if x % i == 0:
            return 0
    return x


async def async_process_numbers(numbers: list[int], max_workers: int = 4) -> list[int]:
    """Обработать числа, выгружая CPU-bound код в пул потоков."""
    from concurrent.futures import ThreadPoolExecutor

    if not numbers:
        return []

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            loop.run_in_executor(executor, blocking_compute, n) for n in numbers
        ]
        results = await asyncio.gather(*futures)
    return list(results)
