#!/usr/bin/env python3
"""Снимает приватные снапшоты источников и обновляет provenance/sources.json."""
import argparse
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "provenance" / "sources.json"
PRIVATE = ROOT / "provenance" / ".private"
UA = "MultiTool-security-wiki/1.0 (+https://github.com/metapeka/whatsapp-security-research)"

EXT = {
    "text/html": "html",
    "application/xhtml+xml": "html",
    "application/pdf": "pdf",
    "application/json": "json",
    "text/plain": "txt",
}


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.lower()).strip("-") or "source"


def fetch(url: str, timeout: int):
    request = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.8",
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.headers, response.read(), None
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read() or None, f"HTTP {exc.code}"
    except Exception as exc:
        return None, {}, None, f"{type(exc).__name__}: {exc}"


def unique_path(name: str, ext: str) -> pathlib.Path:
    path = PRIVATE / f"{name}.{ext}"
    counter = 2
    while path.exists():
        path = PRIVATE / f"{name}-{counter}.{ext}"
        counter += 1
    return path


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(data: dict) -> None:
    data["updated"] = datetime.now(timezone.utc).date().isoformat()
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(MANIFEST)


def has_snapshot(source: dict) -> bool:
    return any(item.get("sha256") for item in source.get("snapshots", []))


def snapshot(source: dict, timeout: int, dry_run: bool) -> bool:
    url = source["url"]
    status, headers, body, error = fetch(url, timeout)
    if dry_run:
        print(f"DRY  {source['id']:40} {url}")
        return True
    if body is None:
        record = {
            "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "status": status,
            "error": error,
        }
        source.setdefault("snapshots", []).append(record)
        print(f"FAIL {source['id']:40} {status or '-'} {error}")
        return False

    content_type = headers.get("Content-Type", "application/octet-stream")
    base = content_type.split(";")[0].strip().lower()
    ext = EXT.get(base, "bin")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = unique_path(f"{slug(source['id'])}-{stamp}", ext)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)

    digest = hashlib.sha256(body).hexdigest()
    relative = path.relative_to(ROOT).as_posix()
    record = {
        "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "content_type": content_type,
        "etag": headers.get("ETag"),
        "last_modified": headers.get("Last-Modified"),
        "bytes": len(body),
        "sha256": digest,
        "path": relative,
    }
    source.setdefault("snapshots", []).append(record)
    print(f"OK   {source['id']:40} {status} {len(body):>9} {digest[:12]} {relative}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Приватные снапшоты источников")
    parser.add_argument("--id", action="append", default=[], help="ID источника; можно несколько")
    parser.add_argument("--all", action="store_true", help="снять заново все источники, включая уже снятые")
    parser.add_argument("--dry-run", action="store_true", help="только показать, что будет снято")
    parser.add_argument("--timeout", type=int, default=30, help="таймаут запроса, секунды")
    args = parser.parse_args()

    data = load_manifest()
    sources = data.get("sources", [])
    by_id = {source["id"]: source for source in sources}
    unknown = [item for item in args.id if item not in by_id]
    if unknown:
        print("неизвестные ID:", ", ".join(unknown), file=sys.stderr)
        return 2

    if args.id:
        targets = [by_id[item] for item in args.id]
    elif args.all:
        targets = sources
    else:
        targets = [source for source in sources if not has_snapshot(source)]

    if not targets:
        print("все источники уже сняты; для новой версии используйте --all или --id")
        return 0

    results = [snapshot(source, args.timeout, args.dry_run) for source in targets]
    if not args.dry_run:
        save_manifest(data)
        print(f"\nснято {sum(results)} из {len(results)}; приватные файлы: {PRIVATE.relative_to(ROOT)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
