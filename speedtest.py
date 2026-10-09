"""Замер скорости интернета: N последовательных загрузок файла по URL.

Пример:
    python speedtest.py https://example.com/big-image.jpg
    python speedtest.py https://example.com/big-image.jpg -n 5 -t 60
"""

import argparse
import sys
import time
import urllib.error
import urllib.request

CHUNK_SIZE = 64 * 1024
USER_AGENT = "Mozilla/5.0 (speedtest script)"


def download(url: str, timeout: float) -> tuple[int, float]:
    """Скачивает ресурс целиком. Возвращает (байт скачано, секунд затрачено)."""
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"},
    )
    total = 0
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        while chunk := response.read(CHUNK_SIZE):
            total += len(chunk)
    elapsed = time.perf_counter() - start
    return total, elapsed


def format_size(num_bytes: float) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if num_bytes < 1024 or unit == "ГБ":
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.2f} ГБ"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Замер скорости загрузки по URL")
    parser.add_argument("url", help="адрес тяжёлого файла (например, большой картинки)")
    parser.add_argument("-n", "--requests", type=int, default=10,
                        help="количество последовательных запросов (по умолчанию 10)")
    parser.add_argument("-t", "--timeout", type=float, default=30,
                        help="таймаут одного запроса в секундах (по умолчанию 30)")
    args = parser.parse_args()
    if args.requests < 1:
        parser.error("количество запросов должно быть >= 1")
    return args


def main() -> int:
    args = parse_args()
    print(f"URL: {args.url}")
    print(f"Запросов: {args.requests}\n")

    total_bytes = 0
    total_time = 0.0
    successful = 0

    for i in range(1, args.requests + 1):
        try:
            size, elapsed = download(args.url, args.timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"[{i:>2}/{args.requests}] ошибка: {exc}")
            continue

        successful += 1
        total_bytes += size
        total_time += elapsed
        speed = size / elapsed / 1024 / 1024 if elapsed > 0 else 0
        print(f"[{i:>2}/{args.requests}] {format_size(size):>12}  "
              f"{elapsed:7.3f} с  {speed:8.2f} МБ/с")

    if successful == 0 or total_time == 0:
        print("\nНи один запрос не завершился успешно.")
        return 1

    avg_time = total_time / successful
    speed_mbytes = total_bytes / total_time / 1024 / 1024
    speed_mbits = total_bytes * 8 / total_time / 1_000_000

    print("\n=== Итог ===")
    print(f"Успешных запросов:     {successful} из {args.requests}")
    print(f"Скачано всего:         {format_size(total_bytes)}")
    print(f"Среднее время запроса: {avg_time:.3f} с")
    print(f"Средняя скорость:      {speed_mbytes:.2f} МБ/с ({speed_mbits:.2f} Мбит/с)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
        sys.exit(130)
