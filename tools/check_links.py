#!/usr/bin/env python3
"""Проверяет ссылки в собранном сайте docs/: файлы, якоря и внешние URL.

Внешние адреса нашего домена не проверяются: на PR они ещё не опубликованы.
Ответы 401, 403, 405 и 429 считаются блокировкой бота, а не битой ссылкой.
"""
import pathlib
import re
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OWN = "metapeka.github.io"
ATTR = re.compile(r'(?:href|src)="([^"]+)"')
SKIP = ("mailto:", "tel:", "data:", "javascript:")
BLOCKED = {401, 403, 405, 429}


def check_external(url: str) -> str:
    """Пусто — ссылка жива, иначе причина."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; security-wiki-link-check)",
        "Accept": "text/html,*/*;q=0.8",
    })
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                res.read(2048)
                return ""
        except urllib.error.HTTPError as e:
            if e.code in BLOCKED:
                return f"blocked {e.code}"
            return f"HTTP {e.code}"
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 2:
                return f"нет соединения: {getattr(e, 'reason', e)}"
            time.sleep(2)
    return "неизвестная ошибка"


def main() -> None:
    pages = sorted(DOCS.glob("*.html"))
    internal, anchors, external = [], [], set()
    for page in pages:
        for raw in ATTR.findall(page.read_text(encoding="utf-8")):
            if raw.startswith(SKIP) or raw.startswith("//"):
                continue
            if raw.startswith("http"):
                if OWN not in raw:
                    external.add(raw)
                continue
            if raw.startswith("#"):
                target, frag = page, raw[1:]
            else:
                path, _, frag = raw.partition("#")
                path = path.split("?")[0]
                target = (page.parent / path).resolve()
                if not target.exists():
                    internal.append(f"{page.name}: {raw}")
                    continue
            if frag and target.suffix == ".html":
                if f'id="{frag}"' not in target.read_text(encoding="utf-8"):
                    anchors.append(f"{page.name}: {raw}")

    blocked = []
    for url in sorted(external):
        reason = check_external(url)
        if reason.startswith("blocked"):
            blocked.append(f"{url} — {reason}")
        elif reason:
            internal.append(f"внешняя {url} — {reason}")

    print(f"страниц: {len(pages)}; внешних ссылок: {len(external)}; "
          f"битых: {len(internal) + len(anchors)}; заблокированных: {len(blocked)}")
    for item in internal + anchors + blocked:
        print("  -", item)
    if internal or anchors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
