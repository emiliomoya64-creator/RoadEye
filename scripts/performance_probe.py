#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path


APP_PATTERN = "/home/emilio/PiDash/app.py"


def find_pid() -> int:
    result = subprocess.run(
        ["pgrep", "-f", APP_PATTERN],
        capture_output=True,
        text=True,
        check=False,
    )

    pids = [
        int(line)
        for line in result.stdout.splitlines()
        if line.strip().isdigit()
    ]

    if not pids:
        raise SystemExit(
            "No se encontró el proceso RoadEye."
        )

    return pids[0]


def read_thread_cpu(pid: int) -> dict[int, tuple[str, int]]:
    tasks = Path(f"/proc/{pid}/task")
    result: dict[int, tuple[str, int]] = {}

    for task in tasks.iterdir():
        if not task.name.isdigit():
            continue

        tid = int(task.name)

        try:
            name = (
                task.joinpath("comm")
                .read_text(encoding="utf-8")
                .strip()
            )

            stat = (
                task.joinpath("stat")
                .read_text(encoding="utf-8")
            )

            closing = stat.rfind(")")
            fields = stat[closing + 2:].split()

            # Después del nombre:
            # estado=0, ppid=1... utime=11, stime=12
            ticks = int(fields[11]) + int(fields[12])

            result[tid] = (name, ticks)

        except (
            OSError,
            ValueError,
            IndexError,
        ):
            continue

    return result


def main() -> None:
    pid = find_pid()
    clock_ticks = os.sysconf(
        os.sysconf_names["SC_CLK_TCK"]
    )

    print()
    print("=" * 66)
    print("        RoadEye · Medición de hilos durante 15 segundos")
    print("=" * 66)
    print()
    print(f"PID RoadEye: {pid}")
    print()

    before = read_thread_cpu(pid)
    started = time.monotonic()

    time.sleep(15)

    elapsed = time.monotonic() - started
    after = read_thread_cpu(pid)

    rows = []

    for tid, (name, ticks_after) in after.items():
        ticks_before = before.get(
            tid,
            (name, ticks_after),
        )[1]

        used_seconds = (
            ticks_after - ticks_before
        ) / clock_ticks

        cpu_percent = (
            used_seconds
            / elapsed
            * 100
        )

        rows.append(
            (
                cpu_percent,
                tid,
                name,
                used_seconds,
            )
        )

    rows.sort(reverse=True)

    print(
        f"{'TID':>8}  {'CPU %':>8}  "
        f"{'CPU s':>8}  HILO"
    )
    print("-" * 66)

    for cpu, tid, name, seconds in rows:
        print(
            f"{tid:>8}  "
            f"{cpu:>8.1f}  "
            f"{seconds:>8.2f}  "
            f"{name}"
        )

    total = sum(
        row[0]
        for row in rows
    )

    print("-" * 66)
    print(
        f"Consumo total aproximado: "
        f"{total:.1f} %"
    )
    print()


if __name__ == "__main__":
    main()
