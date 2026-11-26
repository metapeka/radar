#!/usr/bin/env python3
"""Проверяет темы: цвет литералом в style.css, неизвестная переменная, неполная тема.

Ошибка останавливает проверку. Запускать после правки CSS, до сборки.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "site" / "assets"
THEME_FILE = re.compile(r"^tokens-(\d\d)\.css$")

REQUIRED = [
    "bg", "bg-soft", "bg-code", "fg", "muted", "line",
    "accent", "accent-soft", "accent-ink", "ring",
    "ink", "ink-fg", "ink-muted", "bar-accent",
    "ok", "ok-soft", "warn", "warn-soft", "myth", "myth-soft",
    "p0-bg", "p0-fg", "p0-line", "p1-bg", "p1-fg", "p1-line",
    "p2-bg", "p2-fg", "p2-line",
    "veil", "on-ink-7", "on-ink-18", "on-ink-22",
    "shadow", "radius", "radius-sm", "radius-xs", "radius-badge", "track", "mark-shape",
    "font-body", "font-mono", "font-label", "font-display",
    "size-base", "lh", "measure", "h1", "h2", "h3", "lead",
    "micro", "small", "body-sm",
    "gap", "pad", "col-nav", "col-toc", "bar-h",
    "nav-bg", "nav-border", "nav-active-bg", "nav-active-fg",
    "h2-rule", "h2-num", "topbar-bg", "topbar-fg", "topbar-rule",
]

# Значения, которые в style.css допустимы литералом: ноль и прозрачность.
ALLOWED = re.compile(r"^(0|none|transparent|auto|inherit)$|^\d+(\.\d+)?(px|em|rem|%)?$|^0 0 /$")

declared = lambda text: set(re.findall(r"(--[\w-]+)\s*:", text))


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def main() -> None:
    errors, notes = [], []

    themes = sorted(p for p in ASSETS.glob("tokens-*.css") if THEME_FILE.match(p.name))
    if not themes:
        sys.exit("нет файлов тем в site/assets/")

    base = strip_comments((ASSETS / "tokens-01.css").read_text()) if (ASSETS / "tokens-01.css").exists() else ""
    base_names = declared(base)
    if not base_names:
        errors.append("tokens-01.css: не объявлено ни одной переменной")

    missing_base = [n for n in REQUIRED if "--" + n not in base_names]
    if missing_base:
        errors.append("tokens-01.css: нет обязательных переменных: " + ", ".join(missing_base))

    for path in themes:
        css = strip_comments(path.read_text())
        names = declared(css)
        used = set(re.findall(r"var\((--[\w-]+)", css))
        required = set(n if n.startswith("--") else "--" + n for n in REQUIRED)
        absent = sorted(required - names)
        if absent:
            errors.append(f"{path.name}: не заданы {len(absent)} обязательных переменных: "
                          + ", ".join(absent[:8]) + ("…" if len(absent) > 8 else ""))
        outside = sorted(used - names - base_names)
        if outside:
            errors.append(f"{path.name}: ссылки на переменные, которых нет ни в теме, ни в 01: "
                          + ", ".join(outside))

    style_path = ASSETS / "style.css"
    style = strip_comments(style_path.read_text())
    if re.search(r"^\s*--[\w-]+\s*:", style, re.M):
        errors.append("style.css: объявление переменных не на месте — значения живут в темах")

    leftover = [c for c in re.findall(r"#[0-9a-fA-F]{3,8}\b", style) if c.lower() != "#000"]
    if leftover:
        errors.append("style.css: цвет литералом: " + ", ".join(sorted(set(leftover))))

    if re.search(r"rgba?\(", style):
        errors.append("style.css: цвет в rgba() — вынесите в переменную темы")

    unknown = sorted(set(re.findall(r"var\((--[\w-]+)", style)) - base_names)
    if unknown:
        errors.append("style.css: переменные без значения в tokens-01.css: " + ", ".join(unknown))

    # тема без пары в переключателе
    app = (ASSETS / "app.js").read_text()
    wired = set(re.findall(r"id:\s*'(\d\d)'", app))
    files = {THEME_FILE.match(p.name).group(1) for p in themes}
    if wired != files:
        errors.append("app.js: THEMES не совпадает с файлами тем. "
                      f"В js: {sorted(wired)}; на диске: {sorted(files)}")

    notes.append(f"тем: {len(themes)} ({', '.join(p.stem.split('-')[1] for p in themes)})")
    notes.append(f"обязательных переменных: {len(REQUIRED)}")
    for n in notes:
        print(n)
    if errors:
        print("\nошибки:")
        for e in errors:
            print("  -", e)
        raise SystemExit(1)
    print("темы: проверка пройдена")


if __name__ == "__main__":
    main()
