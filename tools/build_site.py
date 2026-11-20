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

NAV = [
    ("Начало", [("index", "Обзор"), ("threat-model", "Модель угроз"),
                ("methodology", "Методика"), ("charts", "Данные")]),
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

CALL_NOTES = {"note": "Контекст", "warning": "Важно", "ok": "Проверено", "myth": "Миф"}


def pandoc(md: str) -> str:
    res = subprocess.run(
        ["pandoc", "--from", "markdown+task_lists+pipe_tables+smart+autolink_bare_uris+fenced_divs",
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
    s = re.sub(r"^\s*:::\s*\{[^}]*\}\s*$", " ", s, flags=re.M)
    s = re.sub(r"[#>*_|]", " ", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return re.sub(r"\s+", " ", s).strip()


def transform(body: str) -> str:
    """Бейджи приоритетов, scope у th, подписи таблиц и заголовки callout."""
    body = re.sub(r"<td>\s*(?:<strong>)?P([012])(?:</strong>)?\s*</td>",
                  lambda m: f'<td><span class="badge p{m.group(1)}">P{m.group(1)}</span></td>', body)
    body = re.sub(r"<th(?![^>]*\bscope=)", '<th scope="col"', body)
    for cls, label in CALL_NOTES.items():
        body = body.replace(f'<div class="callout {cls}">',
                            f'<div class="callout {cls}"><span class="callout-title">{label}</span>')

    parts = re.split(r"(<h[23][^>]*>.*?</h[23]>)", body, flags=re.S)
    out, cur = [], "Таблица"
    for part in parts:
        if re.match(r"<h[23]", part):
            cur = strip_tags(part) or cur
        part = part.replace(
            "<table>",
            f'<table tabindex="0" aria-label="{html.escape(cur, quote=True)}">',
        )
        out.append(part)
    return "".join(out)


def build_nav(active: str) -> str:
    out = []
    for group, pages in NAV:
        links = []
        for slug, label in pages:
            cls = ' class="active"' if slug == active else ""
            aria = ' aria-current="page"' if slug == active else ""
            links.append(f'<a href="{slug}.html"{cls}{aria}>{html.escape(label)}</a>')
        out.append('<div class="nav-group">'
                   f'<div class="nav-title">{html.escape(group)}</div>'
                   + "".join(links) + "</div>")
    return "\n".join(out)


def build_toc(body: str) -> str:
    heads = re.findall(r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>', body, flags=re.S)
    if not heads:
        return '<div class="toc-empty">—</div>'
    return "\n".join(f'<a class="d{lvl}" href="#{hid}">{strip_tags(text)}</a>'
                     for lvl, hid, text in heads)


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


def build_crumbs(group: str, title: str) -> str:
    return ('<a href="index.html">Главная</a><span class="sep">/</span>'
            f'<span>{html.escape(group)}</span><span class="sep">/</span>'
            f'<span class="here">{html.escape(title)}</span>')


# ---------- графики ----------

C = {
    "bg": "#ffffff", "fg": "#16181d", "muted": "#5b6270",
    "line": "#e3e6ec", "accent": "#245fda", "soft": "#eaf0fe",
    "ok_bg": "#d9f0e3", "ok_fg": "#0f5c3c",
    "no_bg": "#fbe3e3", "no_fg": "#9b1c1c",
    "na_bg": "#f4efd6", "na_fg": "#7a5f00",
}


def _txt(x, y, s, size=12, fill=None, anchor="middle", weight="400"):
    fill = fill or C["fg"]
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" font-family="-apple-system,Segoe UI,Roboto,Arial,sans-serif">{html.escape(s)}</text>')


def svg_cve(data: dict) -> str:
    rows = {r["year"]: max(len(r["ids"]), r["count"]) for r in data["cve_by_year"]}
    missing = {m["year"] for m in data.get("cve_missing_years", [])}
    years = list(range(2019, 2027))
    w, h, ml, mr, mt, mb = 780, 320, 48, 20, 28, 52
    plot_h = h - mt - mb
    maxv = 3
    bw = 52
    gap = (w - ml - mr - bw * len(years)) / (len(years) - 1)
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
         f'<rect width="{w}" height="{h}" fill="{C["bg"]}"/>']
    for i in range(maxv + 1):
        y = mt + plot_h - plot_h * i / maxv
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{w - mr}" y2="{y:.1f}" stroke="{C["line"]}" stroke-width="1"/>')
        s.append(_txt(ml - 10, y + 4, str(i), 11, C["muted"], "end"))
    for i, year in enumerate(years):
        x = ml + i * (bw + gap)
        cx = x + bw / 2
        s.append(_txt(cx, h - 22, str(year), 12, C["muted"]))
        if year in missing:
            s.append(f'<rect x="{x}" y="{mt + plot_h - 2}" width="{bw}" height="2" fill="{C["line"]}"/>')
            s.append(_txt(cx, mt + plot_h - 12, "н/д", 11, C["muted"]))
            continue
        v = rows.get(year, 0)
        bh = plot_h * v / maxv
        y = mt + plot_h - bh
        s.append(f'<rect x="{x}" y="{y:.1f}" width="{bw}" height="{bh:.1f}" rx="4" fill="{C["accent"]}" opacity="0.9"/>')
        s.append(_txt(cx, y - 7, str(v), 13, C["fg"], weight="700"))
    s.append(f'<line x1="{ml}" y1="{mt + plot_h}" x2="{w - mr}" y2="{mt + plot_h}" stroke="{C["muted"]}" stroke-width="1"/>')
    s.append("</svg>")
    return "".join(s)


def svg_ios(data: dict) -> str:
    rows = data["ios_matrix"]
    w, h = 780, 60 + len(rows) * 42 + 46
    label_w, cell_w = 300, 150
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
         f'<rect width="{w}" height="{h}" fill="{C["bg"]}"/>']
    heads = ["Функция", "16.7.x", "18.7.x", "26.x"]
    for i, t in enumerate(heads):
        x = label_w * 0 if i == 0 else label_w + (i - 1) * cell_w
        s.append(_txt(x + 10, 30, t, 12, C["muted"], "start", "700"))
    keys = {"yes": ("Да", C["ok_bg"], C["ok_fg"]),
            "no": ("Нет", C["no_bg"], C["no_fg"]),
            "not_guaranteed": ("Н/д", C["na_bg"], C["na_fg"])}
    for r, row in enumerate(rows):
        y = 46 + r * 42
        if r % 2 == 0:
            s.append(f'<rect x="0" y="{y}" width="{w}" height="42" fill="#fafafb"/>')
        s.append(_txt(10, y + 26, row["feature"], 12.5, C["fg"], "start"))
        for j, key in enumerate(("v16", "v18", "v26")):
            label, bg, fg = keys.get(row.get(key, "not_guaranteed"), keys["not_guaranteed"])
            x = label_w + j * cell_w
            s.append(f'<rect x="{x + 6}" y="{y + 9}" width="{cell_w - 12}" height="24" rx="12" fill="{bg}"/>')
            s.append(_txt(x + cell_w / 2, y + 26, label, 12, fg, "middle", "600"))
    s.append(_txt(10, h - 14, "Источник: таблица на странице iOS. Н/д — данных в таблице нет.", 11, C["muted"], "start"))
    s.append("</svg>")
    return "".join(s)


def render_charts() -> None:
    src = SITE / "data" / "charts.json"
    if not src.exists():
        print("графики: нет site/data/charts.json — пропуск")
        return
    data = json.loads(src.read_text())
    out = OUT / "assets" / "charts"
    out.mkdir(parents=True, exist_ok=True)
    if data.get("cve_by_year"):
        (out / "cve.svg").write_text(svg_cve(data), encoding="utf-8")
    if data.get("ios_matrix"):
        (out / "ios.svg").write_text(svg_ios(data), encoding="utf-8")
    print("графики:", ", ".join(p.name for p in sorted(out.glob("*.svg"))))


def main() -> None:
    template = (SITE / "template.html").read_text()
    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    for name in ("style.css", "app.js"):
        (OUT / "assets" / name).write_text((SITE / "assets" / name).read_text())

    render_charts()

    index = []
    for idx, (slug, label, group) in enumerate(FLAT):
        src = SITE / "content" / f"{slug}.md"
        if not src.exists():
            raise SystemExit(f"нет файла: {src}")
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

        body_html = transform(pandoc(body_md))
        page = (template
                .replace("<!--TITLE-->", html.escape(title))
                .replace("<!--DESC-->", html.escape(desc, quote=True))
                .replace("<!--NAV-->", build_nav(slug))
                .replace("<!--CRUMBS-->", "" if slug == "index" else build_crumbs(group, title))
                .replace("<!--PAGETITLE-->", html.escape(title))
                .replace("<!--CONTENT-->", body_html)
                .replace("<!--TOC-->", build_toc(body_html))
                .replace("<!--PAGER-->", build_pager(idx)))
        (OUT / f"{slug}.html").write_text(page, encoding="utf-8")

        heads = [strip_tags(t) for _, _, t in
                 re.findall(r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>', body_html, flags=re.S)]
        index.append({"u": f"{slug}.html", "t": title, "g": group,
                      "h": heads, "x": plain(body_md)[:2000]})

    (OUT / "assets" / "search-index.js").write_text(
        "window.SEARCH_INDEX = " + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")

    (OUT / "404.html").write_text(
        template
        .replace("<!--TITLE-->", "Страница не найдена")
        .replace("<!--DESC-->", "Страница не найдена.")
        .replace("<!--NAV-->", build_nav(""))
        .replace("<!--CRUMBS-->", '<a href="index.html">Главная</a><span class="sep">/</span><span class="here">404</span>')
        .replace("<!--PAGETITLE-->", "Страница не найдена")
        .replace("<!--CONTENT-->",
                 '<p>Возможно, раздел переехал. Начните с <a href="index.html">обзора</a> '
                 'или воспользуйтесь поиском (клавиша <kbd>/</kbd>).</p>')
        .replace("<!--TOC-->", "")
        .replace("<!--PAGER-->", '<a href="index.html"><span class="dir">Назад</span>К обзору</a>'),
        encoding="utf-8")

    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"собрано страниц: {len(FLAT)} → {OUT}")


if __name__ == "__main__":
    main()
