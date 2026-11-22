#!/usr/bin/env python3
"""Собирает черновик недельной сводки: CISA KEV и новые CVE по мессенджерам."""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("Europe/Moscow")
except Exception:
    LOCAL_TZ = timezone.utc

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEYWORDS = ["WhatsApp", "Telegram", "Signal"]
PATTERNS = {
    "WhatsApp": re.compile(r"\bWhatsApp\b", re.I),
    "Telegram": re.compile(r"\bTelegram\b", re.I),
    "Signal": re.compile(r"\bSignal\b"),
}
EXCLUDE = re.compile(r"\b(Linux kernel|WordPress|Oracle Java|Magento|Drupal|Joomla|plugin|driver)\b", re.I)
UA = "MultiTool-security-wiki/1.0 (+https://github.com/metapeka/whatsapp-security-research)"


def fetch_json(url: str, timeout: int, retries: int = 2):
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json",
    })
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 503) and attempt < retries:
                time.sleep(8)
                continue
            raise
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(3)
                continue
            raise
    raise last


def cell(value, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = text.replace("|", "\\|")
    return text[:limit] + ("…" if len(text) > limit else "")


def kev_section(days: int, timeout: int) -> tuple[list[str], int, str | None]:
    cutoff = (datetime.now(LOCAL_TZ) - timedelta(days=days)).date().isoformat()
    try:
        data = fetch_json(KEV_URL, timeout)
    except Exception as exc:
        return [], 0, f"CISA KEV недоступен: {type(exc).__name__}: {exc}"

    rows = []
    for item in data.get("vulnerabilities", []):
        if item.get("dateAdded", "") < cutoff:
            continue
        name = cell(item.get("vulnerabilityName"))
        if item.get("knownRansomwareCampaignUse") == "Known":
            name += " (ransomware)"
        rows.append((
            item.get("dateAdded", ""),
            f"| {cell(item.get('cveID'))} | {name} | {cell(item.get('dateAdded'))} | {cell(item.get('dueDate'))} |",
        ))
    rows.sort(reverse=True)
    return [row for _, row in rows], len(rows), None


def nvd_section(days: int, timeout: int) -> tuple[list[str], int, list[str]]:
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    end = now.strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    found = {}
    errors = []

    for keyword in KEYWORDS:
        params = {
            "pubStartDate": start,
            "pubEndDate": end,
            "keywordSearch": keyword,
            "resultsPerPage": 30,
        }
        url = NVD_URL + "?" + urllib.parse.urlencode(params)
        try:
            data = fetch_json(url, timeout)
        except Exception as exc:
            errors.append(f"NVD/{keyword}: {type(exc).__name__}: {exc}")
            time.sleep(7)
            continue

        for item in data.get("vulnerabilities", []):
            cve = item.get("cve", {})
            cve_id = cve.get("id")
            if not cve_id or cve.get("vulnStatus") == "Rejected":
                continue
            descriptions = cve.get("descriptions", [])
            description = next((d.get("value", "") for d in descriptions if d.get("lang") == "en"), "")
            if not PATTERNS[keyword].search(description[:200]) or EXCLUDE.search(description):
                continue
            score = ""
            for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                metrics = cve.get("metrics", {}).get(key) or []
                if metrics:
                    cvss = metrics[0].get("cvssData", {})
                    score = str(cvss.get("baseScore") or "")
                    break
            entry = found.setdefault(cve_id, {
                "who": set(),
                "published": (cve.get("published") or "")[:10],
                "score": score,
                "description": description,
            })
            entry["who"].add(keyword)
            if score and not entry["score"]:
                entry["score"] = score

        time.sleep(7)

    rows = []
    for cve_id, entry in found.items():
        who = ", ".join(sorted(entry["who"]))
        rows.append(
            f"| {cell(cve_id)} | {cell(who)} | {cell(entry['published'])} | "
            f"{cell(entry['score'] or '—')} | {cell(entry['description'])} |"
        )
    rows.sort(key=lambda row: row.split("|")[3].strip(), reverse=True)
    return rows, len(rows), errors


def build(days: int, timeout: int, skip_kev: bool, skip_nvd: bool) -> str:
    now = datetime.now(LOCAL_TZ)
    start = (now - timedelta(days=days)).date().isoformat()
    lines = [
        f"# Сводка: {now.date().isoformat()} — черновик",
        "",
        "> Черновик для проверки. Не публиковать без редакции: статусы, версии и выводы не проставлены.",
        "",
        f"Окно: {start} — {now.date().isoformat()} (Europe/Moscow). Источники: CISA KEV, NVD.",
        "",
    ]

    errors = []
    if not skip_kev:
        rows, count, error = kev_section(days, timeout)
        lines += ["## CISA KEV: новые за неделю", ""]
        if error:
            lines += [f"Источник недоступен: {error}", ""]
            errors.append(error)
        elif not rows:
            lines += ["За окно новых записей нет.", ""]
        else:
            lines += ["| CVE | Что | Добавлено | Дедлайн |", "|---|---|---|---|"] + rows + [""]

    if not skip_nvd:
        rows, count, nvd_errors = nvd_section(timeout=timeout, days=days)
        lines += ["## Новые CVE по мессенджерам (NVD)", ""]
        if nvd_errors:
            lines += [f"Ошибки: {'; '.join(nvd_errors)}", ""]
            errors += nvd_errors
        if not rows:
            lines += ["За окно ничего не найдено. Это тоже результат — проверьте вручную по ссылкам ниже.", ""]
        else:
            lines += [
                "| CVE | Кто | Опубликовано | CVSS | Что |",
                "|---|---|---|---|---|",
            ] + rows + [""]

    lines += [
        "## Проверить вручную",
        "",
        "- [ ] WhatsApp Security Advisories — https://www.whatsapp.com/security/advisories/",
        "- [ ] Signal Security — https://signal.org/security",
        "- [ ] Telegram — https://telegram.org/blog",
        "- [ ] Apple Security Releases — https://support.apple.com/en-us/100100",
        "- [ ] MAX — публичных CVE нет; проверить bug bounty и новости",
        "",
        "## Как оформить",
        "",
        "1. Убрать нерелевантное и то, что не меняет рекомендацию.",
        "2. Проверить статус, версии и эксплуатацию по первоисточнику.",
        "3. Перенести 3–6 строк в `site/content/digest.md`.",
        "4. Записать изменение в `site/content/updates.md`.",
        "5. Снять снапшот источника по `provenance/README.md`.",
        "",
    ]

    return "\n".join(lines)[:60000]


def main() -> int:
    parser = argparse.ArgumentParser(description="Черновик недельной сводки")
    parser.add_argument("--days", type=int, default=7, help="окно в днях")
    parser.add_argument("--out", default="digest-draft.md", help="файл результата")
    parser.add_argument("--timeout", type=int, default=40, help="таймаут запроса, секунды")
    parser.add_argument("--skip-kev", action="store_true")
    parser.add_argument("--skip-nvd", action="store_true")
    args = parser.parse_args()

    text = build(args.days, args.timeout, args.skip_kev, args.skip_nvd)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(text)
    print(f"черновик: {args.out} ({len(text)} символов)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
