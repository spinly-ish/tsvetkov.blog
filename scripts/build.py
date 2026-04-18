#!/usr/bin/env python3
"""Static site generator for tsvetkov.blog.

Reads /data/posts.json and regenerates blocks delimited by BUILD-marker
comments in existing HTML files, plus sitemap.xml and RSS feeds.

Usage:
    python3 scripts/build.py

Idempotent: running twice produces the same output.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "posts.json"

RU_MONTHS = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}


def parse_date(iso: str) -> datetime:
    return datetime.strptime(iso, "%Y-%m-%d")


def fmt_date(iso: str, lang: str) -> str:
    d = parse_date(iso)
    if lang == "ru":
        return f"{d.day} {RU_MONTHS[d.month]} {d.year}"
    return d.strftime("%B ") + f"{d.day}, {d.year}"


def read_time_text(minutes: int, lang: str, site: dict) -> str:
    return site[lang]["read_time_template"].format(n=minutes)


def replace_between(text: str, marker: str, content: str) -> str:
    """Replace content between <!-- BUILD:MARKER_START --> and _END markers."""
    start = f"<!-- BUILD:{marker}_START -->"
    end = f"<!-- BUILD:{marker}_END -->"
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{content}\n    {end}"
    new_text, n = pat.subn(replacement, text)
    if n == 0:
        raise ValueError(f"Marker {marker} not found in target")
    return new_text


def esc(s: str) -> str:
    """Escape for HTML attribute values that use double quotes."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def indent_block(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in text.splitlines())


# ---------- Rendering ----------

def render_post_meta(post: dict, lang: str, site: dict) -> str:
    base = site["base_url"]
    slug = post["slug"]
    loc = post[lang]
    path = f"/posts/{slug}.html" if lang == "en" else f"/ru/posts/{slug}.html"
    canonical = f"{base}{path}"
    en_url = f"{base}/posts/{slug}.html"
    ru_url = f"{base}/ru/posts/{slug}.html"
    img_url = f"{base}{post['image']}"
    title_page = f"{loc['title']} — {site['author']}"

    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": loc["title"],
        "description": loc["description"],
        "image": img_url,
        "datePublished": post["date"],
        "author": {"@type": "Person", "name": site["author"]},
        "publisher": {"@type": "Person", "name": site["author"]},
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
    }
    jsonld_str = indent_block(json.dumps(jsonld, ensure_ascii=False, indent=4), 4)

    lines = [
        f'    <meta name="description" content="{esc(loc["description"])}">',
        f'    <title>{esc(title_page)}</title>',
        "",
        "    <!-- Canonical URL -->",
        f'    <link rel="canonical" href="{canonical}">',
        "",
        "    <!-- Open Graph -->",
        '    <meta property="og:type" content="article">',
        f'    <meta property="og:url" content="{canonical}">',
        f'    <meta property="og:title" content="{esc(loc["title"])}">',
        f'    <meta property="og:description" content="{esc(loc["description"])}">',
        f'    <meta property="og:image" content="{img_url}">',
        f'    <meta property="og:site_name" content="{esc(site["author"])}">',
        f'    <meta property="article:published_time" content="{post["date"]}">',
        f'    <meta property="article:author" content="{esc(site["author"])}">',
        "",
        "    <!-- Twitter Card -->",
        '    <meta name="twitter:card" content="summary_large_image">',
        f'    <meta name="twitter:title" content="{esc(loc["title"])}">',
        f'    <meta name="twitter:description" content="{esc(loc["description"])}">',
        f'    <meta name="twitter:image" content="{img_url}">',
        "",
        "    <!-- JSON-LD Structured Data -->",
        '    <script type="application/ld+json">',
        jsonld_str,
        "    </script>",
        "",
        "    <!-- hreflang -->",
        f'    <link rel="alternate" hreflang="en" href="{en_url}">',
        f'    <link rel="alternate" hreflang="ru" href="{ru_url}">',
        f'    <link rel="alternate" hreflang="x-default" href="{en_url}">',
    ]
    return "\n".join(lines)


def render_index_meta(site: dict, lang: str) -> str:
    base = site["base_url"]
    loc = site[lang]
    canonical = f"{base}/" if lang == "en" else f"{base}/ru/"

    jsonld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": site["author"],
        "description": loc["og_description"],
        "url": base if lang == "en" else f"{base}/ru",
        "author": {
            "@type": "Person",
            "name": site["author"],
            "jobTitle": site["job_title"],
        },
    }
    jsonld_str = indent_block(json.dumps(jsonld, ensure_ascii=False, indent=4), 4)

    lines = [
        f'    <meta name="description" content="{esc(loc["description"])}">',
        f'    <title>{esc(loc["title"])}</title>',
        "",
        "    <!-- Canonical URL -->",
        f'    <link rel="canonical" href="{canonical}">',
        "",
        "    <!-- Open Graph -->",
        '    <meta property="og:type" content="website">',
        f'    <meta property="og:url" content="{canonical}">',
        f'    <meta property="og:title" content="{esc(loc["title"])}">',
        f'    <meta property="og:description" content="{esc(loc["og_description"])}">',
        f'    <meta property="og:site_name" content="{esc(site["author"])}">',
        "",
        "    <!-- Twitter Card -->",
        '    <meta name="twitter:card" content="summary">',
        f'    <meta name="twitter:title" content="{esc(loc["title"])}">',
        f'    <meta name="twitter:description" content="{esc(loc["og_description"])}">',
        "",
        "    <!-- JSON-LD Structured Data -->",
        '    <script type="application/ld+json">',
        jsonld_str,
        "    </script>",
        "",
        "    <!-- hreflang -->",
        f'    <link rel="alternate" hreflang="en" href="{base}/">',
        f'    <link rel="alternate" hreflang="ru" href="{base}/ru/">',
        f'    <link rel="alternate" hreflang="x-default" href="{base}/">',
    ]
    return "\n".join(lines)


def render_post_card(post: dict, lang: str, site: dict) -> str:
    loc = post[lang]
    url = f"/posts/{post['slug']}.html" if lang == "en" else f"/ru/posts/{post['slug']}.html"
    date_txt = fmt_date(post["date"], lang)
    rt = read_time_text(post["read_time_min"], lang, site)
    return (
        '            <article class="blog-post">\n'
        '                <div class="post-meta">\n'
        f'                    <time datetime="{post["date"]}">{date_txt}</time>\n'
        f'                    <span class="read-time">{rt}</span>\n'
        '                </div>\n'
        '                <div class="blog-post-inner">\n'
        '                    <div class="blog-post-thumbnail">\n'
        f'                        <a href="{url}">\n'
        f'                            <img loading="lazy" decoding="async" src="{post["image"]}" alt="{esc(loc["image_alt_card"])}">\n'
        '                        </a>\n'
        '                    </div>\n'
        '                    <div class="blog-post-content">\n'
        '                        <h3>\n'
        f'                            <a href="{url}">{esc(loc["title"])}</a>\n'
        '                        </h3>\n'
        '                        <p>\n'
        f'                            {esc(loc["excerpt"])}\n'
        '                        </p>\n'
        '                    </div>\n'
        '                </div>\n'
        '            </article>'
    )


def render_posts_list(posts: list, lang: str, site: dict) -> str:
    return "\n\n".join(render_post_card(p, lang, site) for p in posts)


# ---------- File writers ----------

def build_post_file(path: Path, post: dict, lang: str, site: dict):
    txt = path.read_text(encoding="utf-8")
    meta = render_post_meta(post, lang, site)
    new = replace_between(txt, "META", meta)
    if new != txt:
        path.write_text(new, encoding="utf-8")


def build_index_file(path: Path, site: dict, posts: list, lang: str):
    txt = path.read_text(encoding="utf-8")
    meta = render_index_meta(site, lang)
    txt = replace_between(txt, "META", meta)
    list_html = render_posts_list(posts, lang, site)
    txt = replace_between(txt, "POSTS", list_html)
    path.write_text(txt, encoding="utf-8")


def build_sitemap(site: dict, posts: list):
    base = site["base_url"]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "  <url>",
        f"    <loc>{base}/</loc>",
        f"    <lastmod>{today}</lastmod>",
        "    <changefreq>weekly</changefreq>",
        "    <priority>1.0</priority>",
        "  </url>",
        "  <url>",
        f"    <loc>{base}/ru/</loc>",
        f"    <lastmod>{today}</lastmod>",
        "    <changefreq>weekly</changefreq>",
        "    <priority>1.0</priority>",
        "  </url>",
    ]
    for p in posts:
        for lang, prefix in (("en", ""), ("ru", "/ru")):
            lines += [
                "  <url>",
                f"    <loc>{base}{prefix}/posts/{p['slug']}.html</loc>",
                f"    <lastmod>{p['date']}</lastmod>",
                "    <changefreq>monthly</changefreq>",
                "    <priority>0.8</priority>",
                "  </url>",
            ]
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def rfc822(date_iso: str) -> str:
    d = parse_date(date_iso)
    return d.strftime("%a, %d %b %Y 00:00:00 +0000")


def build_feed(site: dict, posts: list, lang: str):
    base = site["base_url"]
    loc = site[lang]
    feed_path = ROOT / ("feed.xml" if lang == "en" else "ru/feed.xml")
    home = f"{base}/" if lang == "en" else f"{base}/ru/"
    feed_url = f"{base}/feed.xml" if lang == "en" else f"{base}/ru/feed.xml"
    last_build = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = []
    for p in posts:
        post_loc = p[lang]
        url = f"{base}/posts/{p['slug']}.html" if lang == "en" else f"{base}/ru/posts/{p['slug']}.html"
        items.append(
            "    <item>\n"
            f"      <title>{esc(post_loc['title'])}</title>\n"
            f"      <link>{url}</link>\n"
            f"      <guid isPermaLink=\"true\">{url}</guid>\n"
            f"      <pubDate>{rfc822(p['date'])}</pubDate>\n"
            f"      <description>{esc(post_loc['description'])}</description>\n"
            "    </item>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        f"    <title>{esc(loc['feed_title'])}</title>\n"
        f"    <link>{home}</link>\n"
        f"    <description>{esc(loc['feed_description'])}</description>\n"
        f"    <language>{lang}</language>\n"
        f"    <lastBuildDate>{last_build}</lastBuildDate>\n"
        f'    <atom:link href="{feed_url}" rel="self" type="application/rss+xml" />\n'
        + "\n".join(items) + "\n"
        "  </channel>\n"
        "</rss>\n"
    )
    feed_path.parent.mkdir(parents=True, exist_ok=True)
    feed_path.write_text(xml, encoding="utf-8")


# ---------- Main ----------

def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    site = data["site"]
    posts = sorted(data["posts"], key=lambda p: p["date"], reverse=True)

    build_index_file(ROOT / "index.html", site, posts, "en")
    build_index_file(ROOT / "ru" / "index.html", site, posts, "ru")

    for p in posts:
        build_post_file(ROOT / "posts" / f"{p['slug']}.html", p, "en", site)
        build_post_file(ROOT / "ru" / "posts" / f"{p['slug']}.html", p, "ru", site)

    build_sitemap(site, posts)
    build_feed(site, posts, "en")
    build_feed(site, posts, "ru")

    print(f"Built: {len(posts)} posts × 2 langs, 2 indexes, sitemap, 2 feeds")


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(f"Build error: {e}", file=sys.stderr)
        sys.exit(1)
