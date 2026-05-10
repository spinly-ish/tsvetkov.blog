#!/usr/bin/env python3
"""One-shot migration of data/posts.json + HTML bodies into Directus.

Запускается один раз после применения схемы (infra/directus/apply_schema.py).
Идемпотентный: повторный запуск обновит существующие записи (по slug),
не создавая дубликатов.

Использование:
    pip install markdownify  # одноразовая dev-зависимость, в CI не нужна

    DIRECTUS_URL=https://cms.tsvetkov.blog \
    DIRECTUS_TOKEN=<admin token> \
    python3 scripts/migrate_to_directus.py [--dry-run]

Что делает:
    1. Читает data/posts.json → апсертит site_config (singleton).
    2. Для каждого поста читает posts/<slug>.html и ru/posts/<slug>.html,
       выдёргивает <article class="post-content">, конвертирует в Markdown.
    3. Апсертит запись в коллекцию posts. status=published для всех.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "posts.json"
POSTS_DIR_EN = ROOT / "posts"
POSTS_DIR_RU = ROOT / "ru" / "posts"


def fail(msg: str) -> None:
    sys.exit(f"ERROR: {msg}")


try:
    from markdownify import markdownify as md
except ImportError:
    fail("markdownify not installed. Run: pip install markdownify")


URL = os.environ.get("DIRECTUS_URL", "").rstrip("/")
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")

if not URL or not TOKEN:
    fail("Set DIRECTUS_URL and DIRECTUS_TOKEN env vars")


# ---------- Directus REST helpers ----------

def api(method: str, path: str, body: Any = None) -> tuple[int, Any]:
    req = urllib.request.Request(
        f"{URL}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            return resp.status, json.loads(data) if data else None
    except urllib.error.HTTPError as e:
        text = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(text)
        except json.JSONDecodeError:
            return e.code, text


def upsert_singleton(collection: str, payload: dict) -> None:
    code, resp = api("PATCH", f"/items/{collection}", payload)
    if code >= 300:
        fail(f"upsert {collection} failed: {code} {resp}")


def find_post_by_slug(slug: str) -> dict | None:
    code, data = api("GET", f"/items/posts?filter[slug][_eq]={slug}&limit=1")
    if code != 200:
        fail(f"lookup posts/{slug} failed: {code} {data}")
    items = data.get("data") or []
    return items[0] if items else None


def upsert_post(payload: dict) -> None:
    existing = find_post_by_slug(payload["slug"])
    if existing:
        post_id = existing["id"]
        code, resp = api("PATCH", f"/items/posts/{post_id}", payload)
        if code >= 300:
            fail(f"update post {payload['slug']} failed: {code} {resp}")
        print(f"  post {payload['slug']}: updated")
    else:
        code, resp = api("POST", "/items/posts", payload)
        if code >= 300:
            fail(f"create post {payload['slug']} failed: {code} {resp}")
        print(f"  post {payload['slug']}: created")


# ---------- HTML body extraction ----------

ARTICLE_RE = re.compile(
    r'<article\s+class="post-content">(.*?)</article>',
    re.DOTALL,
)


def extract_body_html(path: Path) -> str:
    txt = path.read_text(encoding="utf-8")
    m = ARTICLE_RE.search(txt)
    if not m:
        fail(f"<article class=\"post-content\"> not found in {path}")
    return m.group(1).strip()


def html_to_md(html: str) -> str:
    """Конвертация в Markdown с настройками под наш стиль постов."""
    return md(
        html,
        heading_style="ATX",       # # вместо ===
        bullets="-",
        strip=["script", "style"],
        escape_asterisks=False,
        escape_underscores=False,
    ).strip()


# ---------- Main ----------

def build_site_config_payload(site: dict) -> dict:
    en = site["en"]
    ru = site["ru"]
    return {
        "base_url": site["base_url"],
        "author": site["author"],
        "job_title": site["job_title"],
        "title_en": en["title"],
        "title_ru": ru["title"],
        "description_en": en["description"],
        "description_ru": ru["description"],
        "og_description_en": en["og_description"],
        "og_description_ru": ru["og_description"],
        "hero_label_en": en["hero_label"],
        "hero_label_ru": ru["hero_label"],
        "about_title_en": en["about_title"],
        "about_title_ru": ru["about_title"],
        "about_text_en": en["about_text"],
        "about_text_ru": ru["about_text"],
        "back_link_en": en["back_link"],
        "back_link_ru": ru["back_link"],
        "read_time_template_en": en["read_time_template"],
        "read_time_template_ru": ru["read_time_template"],
        "feed_title_en": en["feed_title"],
        "feed_title_ru": ru["feed_title"],
        "feed_description_en": en["feed_description"],
        "feed_description_ru": ru["feed_description"],
    }


def build_post_payload(post: dict) -> dict:
    slug = post["slug"]
    en = post["en"]
    ru = post["ru"]

    en_html = extract_body_html(POSTS_DIR_EN / f"{slug}.html")
    ru_html = extract_body_html(POSTS_DIR_RU / f"{slug}.html")

    return {
        "slug": slug,
        "date": post["date"],
        "read_time_min": post["read_time_min"],
        "image": post["image"],
        "status": "published",
        "title_en": en["title"],
        "title_ru": ru["title"],
        "description_en": en["description"],
        "description_ru": ru["description"],
        "excerpt_en": en["excerpt"],
        "excerpt_ru": ru["excerpt"],
        "image_alt_card_en": en["image_alt_card"],
        "image_alt_card_ru": ru["image_alt_card"],
        "image_alt_post_en": en["image_alt_post"],
        "image_alt_post_ru": ru["image_alt_post"],
        "body_md_en": html_to_md(en_html),
        "body_md_ru": html_to_md(ru_html),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Печатать payloads, не отправлять")
    args = parser.parse_args()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    site = data["site"]
    posts = data["posts"]

    print(f"Source: {DATA_FILE} ({len(posts)} posts)")
    print(f"Target: {URL}")
    print()

    site_payload = build_site_config_payload(site)
    print("site_config")
    if args.dry_run:
        print(json.dumps(site_payload, ensure_ascii=False, indent=2))
    else:
        upsert_singleton("site_config", site_payload)
        print("  site_config: upserted")

    print()
    print("posts")
    for p in posts:
        payload = build_post_payload(p)
        if args.dry_run:
            preview = {**payload, "body_md_en": payload["body_md_en"][:80] + "...", "body_md_ru": payload["body_md_ru"][:80] + "..."}
            print(json.dumps(preview, ensure_ascii=False, indent=2))
        else:
            upsert_post(payload)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
