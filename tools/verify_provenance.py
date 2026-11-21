#!/usr/bin/env python3
"""Проверяет манифест провенанса, хеши снапшотов и отсутствие приватных файлов в git."""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "provenance" / "sources.json"
PRIVATE = (ROOT / "provenance" / ".private").resolve()


def main() -> int:
    errors = []
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sources = data.get("sources", [])
    ids = set()

    if len(sources) != len({source.get("id") for source in sources}):
        errors.append("повторяющиеся ID источников")

    for source in sources:
        sid = source.get("id")
        if not sid:
            errors.append("источник без id")
            continue
        if sid in ids:
            continue
        ids.add(sid)
        url = source.get("url", "")
        if not url.startswith(("http://", "https://")):
            errors.append(f"{sid}: URL должен начинаться с http(s)")
        if not source.get("published"):
            errors.append(f"{sid}: нет даты публикации")

        for item in source.get("snapshots", []):
            if not item.get("sha256"):
                continue
            path = (ROOT / item.get("path", "")).resolve()
            if PRIVATE != path.parent:
                errors.append(f"{sid}: снапшот вне provenance/.private: {item.get('path')}")
                continue
            if not path.exists():
                errors.append(f"{sid}: нет файла {item.get('path')}")
                continue
            body = path.read_bytes()
            if len(body) != item.get("bytes"):
                errors.append(f"{sid}: размер не совпадает: {item.get('path')}")
            if hashlib.sha256(body).hexdigest() != item.get("sha256"):
                errors.append(f"{sid}: хеш не совпадает: {item.get('path')}")

    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--", "provenance/.private"],
        capture_output=True, text=True,
    )
    if tracked.stdout.strip():
        errors.append("приватные снапшоты отслеживаются git:\n  " + tracked.stdout.strip().replace("\n", "\n  "))

    if errors:
        print("провенанс: ошибки")
        for error in errors:
            print("  -", error)
        return 1

    total = sum(len(source.get("snapshots", [])) for source in sources)
    print(f"провенанс: ок, источников {len(sources)}, записей снапшотов {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
