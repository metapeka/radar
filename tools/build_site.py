#!/usr/bin/env python3
"""Собирает статическую вики из site/content/*.md в docs/ (GitHub Pages)."""
import datetime
import hashlib
import html
import json
import re
import subprocess
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = ROOT / "docs"

NAV = [
    ("Начало", [("index", "Обзор"), ("services", "Каталог сервисов"), ("about", "О проекте"),
                ("threat-model", "Модель угроз"),
                ("methodology", "Методика"), ("sources", "Здоровье источников"),
                ("charts", "Данные"), ("digest", "Сводка"), ("updates", "Обновления")]),
    ("Мессенджеры", [("comparison", "Сравнение"), ("whatsapp", "WhatsApp"), ("telegram", "Telegram"),
                     ("signal", "Signal"), ("max", "MAX"), ("max-research", "MAX: разбор")]),
    ("Платформы", [("macos", "macOS"), ("windows", "Windows"), ("linux", "Linux"),
                   ("ios", "iOS"), ("android", "Android")]),
    ("Семья", [("fam-phone", "Телефон за 15 минут"), ("fam-detect", "Какой у меня телефон"),
               ("push", "Пуши и обман"), ("fam-parent", "Чек-лист для родителя")]),
    ("Практика", [("network", "Сеть и периметр"), ("monitoring", "Мониторинг"),
                  ("passwords", "Менеджеры паролей"), ("breaches", "Проверка утечек"),
                  ("mail", "Почта"),
                  ("browsers", "Браузеры"), ("routers", "Роутер"),
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
    body = re.sub(r"<th(?=[\s>])(?![^>]*\bscope=)", '<th scope="col"', body)
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


def load_verified() -> dict:
    """Даты проверки страниц: site/data/verified.json, ключ — slug."""
    src = SITE / "data" / "verified.json"
    if not src.exists():
        print("проверено: нет site/data/verified.json — бейджи пропущены")
        return {}
    pages = json.loads(src.read_text())["pages"]
    for slug, iso in pages.items():
        try:
            datetime.date.fromisoformat(iso)
        except ValueError:
            raise SystemExit(f"{src}: {slug}: нужна дата ГГГГ-ММ-ДД, получено {iso!r}")
    return pages


def verified_badge(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return (f'<p class="verified"><time datetime="{iso}">проверено '
            f'{d.day:02d}.{d.month:02d}.{d.year}</time></p>')


def report_verified(verified: dict) -> None:
    today = datetime.date.today()
    missing = [slug for slug, _, _ in FLAT if slug not in verified and slug not in GENERATED]
    extra = sorted(set(verified) - set(slug for slug, _, _ in FLAT))
    stale = sorted(s for s, iso in verified.items()
                   if (today - datetime.date.fromisoformat(iso)).days > 90)
    print(f"проверено: {len(verified)} из {len(FLAT) - len(GENERATED)} страниц")
    if missing:
        print("  без даты:", ", ".join(missing))
    if extra:
        print("  лишние ключи (нет такой страницы):", ", ".join(extra))
    if stale:
        print("  старше 90 дней:", ", ".join(stale))


SOURCES = ROOT / "provenance" / "sources.json"
SERVICES = SITE / "data" / "services.json"
GENERATED = {"sources", "services"}
KINDS = {"messenger": "мессенджер", "platform": "платформа",
         "password-manager": "менеджер паролей", "mail": "почта",
         "browser": "браузер", "router": "роутер"}


def fmt_date(iso: str) -> str:
    return datetime.date.fromisoformat(iso[:10]).strftime("%d.%m.%Y")


def sources_page():
    """«Здоровье источников» собирается из манифеста, а не из Markdown."""
    data = json.loads(SOURCES.read_text())
    today = datetime.date.today()
    rows, broken, stale = [], [], []
    ok7 = 0
    for s in data["sources"]:
        snaps = s.get("snapshots") or []
        last = snaps[-1] if snaps else None
        ok = next((x for x in reversed(snaps) if x.get("status") == 200), None)
        age = (today - datetime.date.fromisoformat(ok["retrieved"][:10])).days if ok else None
        if age is not None and age <= 7:
            ok7 += 1
        if age is None or age > 90:
            stale.append(s["title"])
        if not last or last.get("status") != 200:
            broken.append(s["title"])
        if not last:
            status = "нет снапшота"
        elif last.get("status") == 200:
            status = "200 — ок"
        else:
            status = f'ошибка {last.get("status")}'
        rows.append(
            f'<tr><td><a href="{html.escape(s["url"], quote=True)}">{html.escape(s["title"])}</a>'
            f'<br>{html.escape(s.get("publisher") or "")}</td>'
            f'<td>{fmt_date(s["published"]) if s.get("published") else "—"}</td>'
            f'<td>{fmt_date(ok["retrieved"]) if ok else "—"}</td>'
            f'<td>{html.escape(status)}</td></tr>')

    total = len(data["sources"])
    attention = []
    if broken:
        attention.append("<li>Последняя попытка не удалась: " + ", ".join(
            html.escape(b) for b in broken) + ".</li>")
    if stale:
        attention.append("<li>Без успешной проверки дольше 90 дней: " + ", ".join(
            html.escape(s) for s in stale) + ".</li>")
    attention_html = ("<ul>" + "".join(attention) + "</ul>" if attention
                      else "<p>Сейчас всё в порядке: все источники отвечают, проверки свежие.</p>")

    body = f"""<blockquote>
<p>Какие источники живы, когда их проверяли и что сломалось. Страница собирается из манифеста при каждой сборке.</p>
</blockquote>

<div class="callout note">
<p>Даты и статусы берутся из <code>provenance/sources.json</code>. Успешная проверка — последний снапшот с кодом 200. Полные снапшоты и хеши лежат в приватном хранилище; здесь только метаданные.</p>
</div>

<h2 id="сводка">Сводка</h2>
<p>Источников в манифесте: <b>{total}</b>. Успешная проверка за последние 7 дней: <b>{ok7} из {total}</b>. Манифест обновлён {fmt_date(data["updated"])}.</p>

<h2 id="источники">Источники</h2>
<table>
<thead><tr><th>Источник</th><th>Опубликован</th><th>Проверен</th><th>Статус</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>

<h2 id="что-требует-внимания">Что требует внимания</h2>
{attention_html}

<h2 id="как-это-устроено">Как это устроено</h2>
<p>Правила фиксации — в <a href="https://github.com/metapeka/whatsapp-security-research/blob/master/provenance/README.md">provenance/README.md</a>, манифест — в <a href="https://github.com/metapeka/whatsapp-security-research/blob/master/provenance/sources.json">sources.json</a>. Хеш фиксирует, что именно мы видели; он не доказывает авторство источника.</p>
"""
    desc = "Статус источников: когда проверены, что отвечает, что сломалось."
    return "Здоровье источников", desc, transform(body)


SITE_URL = "https://metapeka.github.io/whatsapp-security-research/"


def _md_table(md: str, heading: str = ""):
    """Строки первой таблицы (без шапки и разделителя)."""
    if heading:
        md = md.split(heading, 1)[1]
    block, started = [], False
    for line in md.splitlines():
        if line.strip().startswith("|"):
            block.append(line)
            started = True
        elif started:
            break
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in block]
    return rows[2:]


def _iso_date(cell: str):
    try:
        return datetime.datetime.strptime(cell, "%d.%m.%Y").date().isoformat()
    except ValueError:
        return None


def _first_page(cell: str, default: str) -> str:
    m = re.search(r"\]\(([^)]+)\)", cell)
    return m.group(1) if m and m.group(1).endswith(".html") else default


def _entry(kind: str, iso: str, title: str, link: str, summary: str) -> dict:
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
    return {"id": f"tag:metapeka.github.io,{iso}:{kind}/{digest}", "title": title,
            "updated": iso, "link": link, "summary": summary}


def atom(title: str, subtitle: str, name: str, entries: list) -> str:
    entries.sort(key=lambda e: e["updated"], reverse=True)
    updated = entries[0]["updated"] if entries else datetime.date.today().isoformat()
    items = "".join(
        f'<entry><id>{html.escape(e["id"])}</id>'
        f'<title>{html.escape(e["title"])}</title>'
        f'<updated>{e["updated"]}T00:00:00Z</updated>'
        f'<link href="{html.escape(e["link"], quote=True)}"/>'
        f'<summary type="text">{html.escape(e["summary"])}</summary></entry>'
        for e in entries[:50])
    return ('<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">'
            f'<id>{SITE_URL}{name}</id>'
            f'<title>{html.escape(title)}</title>'
            f'<subtitle>{html.escape(subtitle)}</subtitle>'
            f'<updated>{updated}T00:00:00Z</updated>'
            f'<link rel="self" href="{SITE_URL}{name}"/>'
            f'<link href="{SITE_URL}"/>'
            '<author><name>Личная безопасность и мессенджеры</name></author>'
            f'{items}</feed>\n')


def render_feeds() -> None:
    entries = []
    for date, what, pages in _md_table((SITE / "content" / "updates.md").read_text()):
        iso = _iso_date(date)
        if iso:
            entries.append(_entry("updates", iso, plain(what),
                                  SITE_URL + _first_page(pages, "updates.html"), plain(pages)))
    (OUT / "feed-updates.xml").write_text(
        atom("Обновления сайта", "Что и когда менялось в вики", "feed-updates.xml", entries),
        encoding="utf-8")

    entries = []
    for row in _md_table((SITE / "content" / "digest.md").read_text(), "## Главное за неделю"):
        if len(row) < 4:
            continue
        date, what, who, action = row[:4]
        iso = _iso_date(date)
        if iso:
            entries.append(_entry("digest", iso, plain(what), SITE_URL + "digest.html",
                                  f"{plain(who)}: {plain(action)}"))
    (OUT / "feed-digest.xml").write_text(
        atom("Сводка за неделю", "Что изменилось в безопасности мессенджеров и устройств",
             "feed-digest.xml", entries),
        encoding="utf-8")


def load_services() -> dict:
    data = json.loads(SERVICES.read_text())
    services = {}
    for s in data["services"]:
        slug = s.get("slug", "")
        if not slug or slug in services:
            raise SystemExit(f"{SERVICES}: пустой или повторный slug: {slug!r}")
        try:
            datetime.date.fromisoformat(s["verified"])
        except (KeyError, ValueError):
            raise SystemExit(f"{SERVICES}: {slug}: нужна дата verified в формате ГГГГ-ММ-ДД")
        if not s.get("items") or not s.get("platforms"):
            raise SystemExit(f"{SERVICES}: {slug}: нужны непустые items и platforms")
        if s.get("heading_level", 3) not in {3, 4}:
            raise SystemExit(f"{SERVICES}: {slug}: heading_level должен быть 3 или 4")
        for it in s["items"]:
            if it.get("priority") not in {"P0", "P1", "P2"}:
                raise SystemExit(f"{SERVICES}: {slug}: неверный priority {it.get('priority')!r}")
            if not str(it.get("group", "")).startswith(it["priority"]):
                raise SystemExit(f"{SERVICES}: {slug}: group не начинается с {it['priority']}")
            if not it.get("text"):
                raise SystemExit(f"{SERVICES}: {slug}: пустой text")
        services[slug] = s
    return services


def checklist_md(service: dict) -> str:
    level = service.get("heading_level", 3)
    out, group = [], None
    for item in service["items"]:
        if item["group"] != group:
            group = item["group"]
            anchor = f" {{#{service['slug']}-{item['priority'].lower()}}}" if level > 3 else ""
            out.append(f"\n{'#' * level} {group}{anchor}\n")
        out.append(f"- [ ] {item['text']}")
    return "\n".join(out) + "\n"


def expand_services(md: str, services: dict) -> str:
    def repl(m):
        slug = m.group(1)
        if slug not in services:
            raise SystemExit(f"<!--services:{slug}-->: нет записи в services.json")
        return checklist_md(services[slug])
    return re.sub(r"\[Чек-лист на сайте\]\([^)]+\)\s*<!--services:([a-z0-9-]+)-->", repl, md)


def report_services(services: dict) -> None:
    print(f"сервисы: {len(services)}, пунктов: {sum(len(s['items']) for s in services.values())}")
    texts = [p.read_text() for p in (SITE / "content").glob("*.md")]
    for slug in services:
        if not any(f"<!--services:{slug}-->" in t for t in texts):
            print(f"  нет плейсхолдера на страницах: {slug}")


def services_page(services: dict):
    rows = []
    for s in services.values():
        counts = [sum(1 for i in s["items"] if i["priority"] == p) for p in ("P0", "P1", "P2")]
        rows.append(
            f'<tr><td><a href="{html.escape(s["page"], quote=True)}">{html.escape(s["name"])}</a>'
            f'<br>{html.escape(KINDS.get(s["kind"], s["kind"]))}</td>'
            f'<td>{html.escape(", ".join(s["platforms"]))}</td>'
            f'<td>{" / ".join(str(n) for n in counts)}</td>'
            f'<td>{fmt_date(s["verified"])}</td></tr>')

    body = f"""<blockquote>
<p>Сервисы вики и их чек-листы: платформы, число пунктов, дата проверки.</p>
</blockquote>

<div class="callout note">
<p>Таблица и блоки чек-листов собираются из <code>site/data/services.json</code> при сборке. Вручную их не правят: правится JSON, страница пересобирается.</p>
</div>

<h2 id="сервисы">Сервисы</h2>
<table>
<thead><tr><th>Сервис</th><th>Платформы</th><th>Пункты P0 / P1 / P2</th><th>Проверено</th></tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>

<h2 id="как-добавить-сервис">Как добавить сервис</h2>
<p>Добавьте запись в <a href="https://github.com/metapeka/whatsapp-security-research/tree/master/site/data">services.json</a>: slug, название, тип, страница, платформы, дата проверки и пункты с приоритетом. В тексте страницы поставьте строку <code>[Чек-лист на сайте](URL) &lt;!--services:slug--&gt;</code> — сборка подставит блок чек-листа. Проверка сборки падает, если у пункта нет приоритета или группы.</p>
"""
    return "Каталог сервисов", "Сервисы вики: платформы, чек-листы и дата проверки.", transform(body)


def validate_profiles() -> None:
    allowed = {"elevated", "targeted"}
    bad = []
    for f in sorted((SITE / "content").glob("*.md")):
        for i, line in enumerate(f.read_text().splitlines(), 1):
            m = re.match(r":::\s*\{\.profile([^}]*)\}", line)
            if not m:
                continue
            classes = [c.lstrip(".") for c in m.group(1).split()]
            if len(classes) != 1 or set(classes) - allowed:
                bad.append(f"{f.name}:{i}: {line.strip()}")
    if bad:
        print("профили: проверьте разметку:")
        for b in bad:
            print("  -", b)
    else:
        print("профили: разметка корректна")


def main() -> None:
    validate_profiles()
    verified = load_verified()
    report_verified(verified)
    services = load_services()
    report_services(services)
    ver = time.strftime("%y%m%d%H%M")
    template = (SITE / "template.html").read_text().replace("<!--VER-->", ver)
    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    for name in sorted(p.name for p in (SITE / "assets").glob("*.css")):
        (OUT / "assets" / name).write_text((SITE / "assets" / name).read_text())
    (OUT / "assets" / "app.js").write_text((SITE / "assets" / "app.js").read_text())

    render_charts()

    index = []
    for idx, (slug, label, group) in enumerate(FLAT):
        if slug == "sources":
            title, desc, body_html = sources_page()
            body_md = ""
        elif slug == "services":
            title, desc, body_html = services_page(services)
            body_md = ""
        else:
            src = SITE / "content" / f"{slug}.md"
            if not src.exists():
                raise SystemExit(f"нет файла: {src}")
            md = expand_services(src.read_text(), services)
            md = (md.replace("<!--stat:services-->", str(len(services)))
                    .replace("<!--stat:items-->", str(sum(len(x["items"]) for x in services.values())))
                    .replace("<!--stat:pages-->", str(len(verified))))
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
                .replace("<!--VERIFIED-->", verified_badge(verified[slug]) if slug in verified else "")
                .replace("<!--CONTENT-->", body_html)
                .replace("<!--TOC-->", build_toc(body_html))
                .replace("<!--PAGER-->", build_pager(idx)))
        (OUT / f"{slug}.html").write_text(page, encoding="utf-8")

        heads = [strip_tags(t) for _, _, t in
                 re.findall(r'<h([23]) id="([^"]+)"[^>]*>(.*?)</h\1>', body_html, flags=re.S)]
        index.append({"u": f"{slug}.html", "t": title, "g": group,
                      "h": heads,
                      "x": (plain(body_md) if body_md else strip_tags(body_html))[:2000]})

    render_feeds()

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
        .replace("<!--VERIFIED-->", "")
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
