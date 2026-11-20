#!/usr/bin/env python3
"""Собирает статическую вики из site/content/*.md в docs/ (GitHub Pages)."""
import html
import json
import re
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "docs"
DATE = "21.11.2026"

NAV = [
    ("Начало", [("index", "Обзор"), ("threat-model", "Модель угроз"), ("methodology", "Методика")]),
    ("Мессенджеры", [("whatsapp", "WhatsApp"), ("telegram", "Telegram"), ("signal", "Signal"),
                     ("max", "MAX")]),
    ("Платформы", [("macos", "macOS"), ("windows", "Windows"), ("linux", "Linux"),
                   ("ios", "iOS"), ("android", "Android")]),
    ("Практика", [("network", "Сеть и периметр"), ("monitoring", "Мониторинг"),
                  ("app-analysis", "Анализ приложений"), ("lab-bench", "Стенд для анализа"),
                  ("incident-response", "Реагирование"), ("diagnostics-ai", "Диагностика с AI"),
                  ("iphone-lab", "iPhone как стенд")]),
]

FLAT = [(slug, label, group) for group, pages in NAV for slug, label in pages]


def pandoc(md: str) -> str:
    res = subprocess.run(
        ["pandoc", "--from", "markdown+task_lists+pipe_tables+smart+autolink_bare_uris",
         "--to", "html", "--wrap=none"],
        input=md, capture_output=True, text=True, check=True,
    )
    return res.stdout


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def plain(md: str) -> str:
    s = re.sub(r"```.*?```", " ", md, flags=re.S)
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"^\s*[-*+]\s+\[.\]\s*", "", s, flags=re.M)
    s = re.sub(r"[#>*_|]", " ", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def build_nav(active: str) -> str:
    out = []
    for group, pages in NAV:
        links = []
        for slug, label in pages:
            cls = ' class="active"' if slug == active else ""
            aria = ' aria-current="page"' if slug == active else ""
            links.append(f'<a href="{slug}.html"{cls}{aria}>{html.escape(label)}</a>')
        out.append(
            '<div class="nav-group">'
            f'<div class="nav-title">{html.escape(group)}</div>'
            + "".join(links) + "</div>"
        )
    return "\n".join(out)


def build_toc(html_body: str) -> str:
    heads = re.findall(r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>', html_body, flags=re.S)
    if not heads:
        return '<div class="toc-empty">—</div>'
    return "\n".join(
        f'<a class="d{lvl}" href="#{hid}">{strip_tags(text)}</a>'
        for lvl, hid, text in heads
    )


def build_pager(idx: int) -> str:
    parts = []
    if idx > 0:
        slug, label, _ = FLAT[idx - 1]
        parts.append(f'<a class="prev" href="{slug}.html"><span class="dir">Назад</span>{html.escape(label)}</a>')
    else:
        parts.append("<span></span>")
    if idx < len(FLAT) - 1:
        slug, label, _ = FLAT[idx + 1]
        parts.append(f'<a class="next" href="{slug}.html"><span class="dir">Дальше</span>{html.escape(label)}</a>')
    return "".join(parts)


def main() -> None:
    template = (SITE / "template.html").read_text()
    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    for name in ("style.css", "app.js"):
        (OUT / "assets" / name).write_text((SITE / "assets" / name).read_text())

    index = []
    for idx, (slug, label, group) in enumerate(FLAT):
        src = SITE / "content" / f"{slug}.md"
        md = src.read_text()
        m = re.match(r"#\s+(.+?)\s*\n", md)
        if not m:
            raise SystemExit(f"{src}: нужен заголовок '# ...' первой строкой")
        title = strip_tags(m.group(1))
        body_md = md[m.end():]

        desc = "Защита личных данных и мессенджеров: практические чек-листы."
        sm = re.search(r"^>\s*(.+)$", body_md, flags=re.M)
        if sm:
            desc = plain(sm.group(1))[:180]

        html_body = pandoc(body_md)
        page = (
            template
            .replace("<!--TITLE-->", html.escape(title))
            .replace("<!--DESC-->", html.escape(desc, quote=True))
            .replace("<!--NAV-->", build_nav(slug))
            .replace("<!--PAGETITLE-->", html.escape(title))
            .replace("<!--CONTENT-->", html_body)
            .replace("<!--TOC-->", build_toc(html_body))
            .replace("<!--PAGER-->", build_pager(idx))
        )
        (OUT / f"{slug}.html").write_text(page, encoding="utf-8")

        heads = [strip_tags(t) for _, _, t in re.findall(r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>', html_body, flags=re.S)]
        index.append({"u": f"{slug}.html", "t": title, "g": group, "h": heads, "x": plain(body_md)[:2000]})

    (OUT / "assets" / "search-index.js").write_text(
        "window.SEARCH_INDEX = " + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    (OUT / "404.html").write_text(
        template
        .replace("<!--TITLE-->", "Страница не найдена")
        .replace("<!--DESC-->", "Страница не найдена.")
        .replace("<!--NAV-->", build_nav(""))
        .replace("<!--PAGETITLE-->", "Страница не найдена")
        .replace("<!--CONTENT-->",
                 "<p>Возможно, раздел переехал. Начните с <a href=\"index.html\">обзора</a> "
                 "или воспользуйтесь поиском (клавиша <kbd>/</kbd>).</p>")
        .replace("<!--TOC-->", "")
        .replace("<!--PAGER-->", '<a href="index.html"><span class="dir">Назад</span>К обзору</a>'),
        encoding="utf-8",
    )

    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"собрано страниц: {len(FLAT)} → {OUT}")


if __name__ == "__main__":
    main()
