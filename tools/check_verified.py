#!/usr/bin/env python3
"""Ищет страницы, изменённые позже даты проверки: бейдж может врать.

Сравнивает дату в site/data/verified.json с датой последнего коммита страницы.
Нужен полный клон (в CI — fetch-depth: 0), иначе git отдаст дату чекаута.
Проверяет только закоммиченное: незакоммиченная правка страницы не видна.
"""
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "site" / "content"


def last_commit(slug: str):
    res = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", f"site/content/{slug}.md"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return res.stdout.strip() or None


def main() -> None:
    verified = json.loads((ROOT / "site" / "data" / "verified.json").read_text())["pages"]
    drift = []
    for slug, iso in sorted(verified.items()):
        if not (CONTENT / f"{slug}.md").exists():
            drift.append(f"{slug}: страницы нет — лишний ключ в verified.json")
            continue
        last = last_commit(slug)
        if last and last > iso:
            drift.append(f"{slug}: страница менялась {last}, дата проверки {iso}")
    if drift:
        print("дата проверки старше правки — подтвердите, что факты не изменились,")
        print("или обновите site/data/verified.json:")
        for item in drift:
            print("  -", item)
        raise SystemExit(1)
    print(f"даты проверки согласованы: {len(verified)} страниц")


if __name__ == "__main__":
    main()
