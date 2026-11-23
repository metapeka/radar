#!/usr/bin/env python3
"""Ищет страницы, изменённые позже даты проверки: бейдж может врать.

Сравнивает дату в site/data/verified.json с датой последнего коммита страницы.
Если текст статьи между прошлой правкой и текущей сборкой не изменился
(например, пункты перенесли в services.json), расхождение не считается.
Нужен полный клон (в CI — fetch-depth: 0), иначе git отдаст дату чекаута.
Проверяет только закоммиченное: незакоммиченная правка страницы не видна.
"""
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "site" / "content"


def history(slug: str, n: int = 2):
    res = subprocess.run(
        ["git", "log", f"-{n}", "--format=%h %cs", "--", f"site/content/{slug}.md"],
        cwd=ROOT, capture_output=True, text=True,
    )
    return [line.split() for line in res.stdout.splitlines() if line.strip()]


def article_text(source: str):
    m = re.search(r"<article>(.*?)</article>", source, re.S)
    if not m:
        return None
    body = re.sub(r'<p class="verified">.*?</p>', "", m.group(1), flags=re.S)
    body = re.sub(r'<div class="crumbs">.*?</div>', "", body, flags=re.S)
    body = re.sub(r'<a class="anchor"[^>]*>.*?</a>', "", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def text_unchanged(slug: str, prev: str) -> bool:
    old = subprocess.run(["git", "show", f"{prev}:docs/{slug}.html"],
                         cwd=ROOT, capture_output=True, text=True)
    current = ROOT / "docs" / f"{slug}.html"
    if old.returncode != 0 or not current.exists():
        return False
    before, after = article_text(old.stdout), article_text(current.read_text(encoding="utf-8"))
    return before is not None and before == after


def main() -> None:
    verified = json.loads((ROOT / "site" / "data" / "verified.json").read_text())["pages"]
    drift = []
    for slug, iso in sorted(verified.items()):
        if not (CONTENT / f"{slug}.md").exists():
            drift.append(f"{slug}: страницы нет — лишний ключ в verified.json")
            continue
        commits = history(slug)
        if not commits:
            continue
        last_date = commits[0][1]
        if last_date > iso:
            prev = commits[1][0] if len(commits) > 1 else None
            if not (prev and text_unchanged(slug, prev)):
                drift.append(f"{slug}: страница менялась {last_date}, дата проверки {iso}")
    if drift:
        print("дата проверки старше правки — подтвердите, что факты не изменились,")
        print("или обновите site/data/verified.json:")
        for item in drift:
            print("  -", item)
        raise SystemExit(1)
    print(f"даты проверки согласованы: {len(verified)} страниц")


if __name__ == "__main__":
    main()
