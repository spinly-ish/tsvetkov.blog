# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Local Preview

```bash
python3 -m http.server 8000
```

No build step. No dependencies. No tests. Pure static files served as-is.

After adding a new post, always start the server so the user can preview before committing.

## Deployment

GitHub Pages, auto-deployed from `main`. The `docs/` folder is gitignored and never deployed.

## Bilingual Structure

The blog supports English (primary) and Russian:

```
tsvetkov.blog/           → EN homepage
tsvetkov.blog/ru/        → RU homepage
tsvetkov.blog/posts/     → EN posts
tsvetkov.blog/ru/posts/  → RU posts
```

Path conventions:
- `ru/index.html` uses `../styles.css` and `/pics/` (absolute) for images
- `ru/posts/*.html` uses `../../styles.css` and `/pics/` (absolute) for images
- All RU pages have `<html lang="ru">` and back-links to `/ru/`

Every page (EN and RU) includes hreflang alternate links in `<head>`:
```html
<link rel="alternate" hreflang="en" href="https://tsvetkov.blog/posts/slug.html">
<link rel="alternate" hreflang="ru" href="https://tsvetkov.blog/ru/posts/slug.html">
<link rel="alternate" hreflang="x-default" href="https://tsvetkov.blog/posts/slug.html">
```

Language switcher (`.lang-toggle` in `.search-container`) shows **EN** | RU on English pages and EN | **RU** on Russian pages.

## Adding a New Post

Four files must be updated for a full bilingual post:

1. **Create** `posts/<slug>.html` — copy any existing EN post as a template, add hreflang + lang-toggle
2. **Create** `ru/posts/<slug>.html` — RU stub with `[Перевод готовится]` placeholder, proper paths (`../../styles.css`), hreflang, back-link to `/ru/`
3. **Prepend** a new `<article class="blog-post">` block at the top of `index.html`
4. **Prepend** a matching `<article class="blog-post">` block at the top of `ru/index.html`

Also update `sitemap.xml` with both the EN and RU URLs.

Every post requires: `<meta name="description">`, Open Graph tags, Twitter Card tags, JSON-LD structured data, and `<link rel="canonical">`. All use absolute URLs (`https://tsvetkov.blog/...`).

## Post HTML Structure

- `<time datetime="YYYY-MM-DD">` in both the post header and the index article block
- `<img src="/pics/filename" ...>` — images live in `/pics/`
- `<span class="read-time">~ N min read</span>` in the index article block
- Post filename becomes the URL slug

## Theming

CSS variables defined in `styles.css` under `:root` (light) and `[data-theme="dark"]`. Theme is toggled via JS that sets `data-theme="dark"` on `<html>` and persists to `localStorage`. Every page includes the anti-flash inline script in `<head>` before any other content.

## Analytics

Amplitude with session replay is loaded on every page (both `index.html` and all post pages). The init key is `e20b6ff1be04dca612ab40af3c889626`. Do not remove or modify these scripts.

## Content Style

Russian is the primary language for new posts; English is secondary. Topics: product strategy, tech, behavior, simplicity vs complexity.

### Russian posts
Written by the author directly. Keep the original tone and text as-is.

### English posts
Mark Manson-inspired tone: direct, informal, punchy short paragraphs, conversational voice. Not a literal translation of the Russian — a rewrite that captures the same idea but sounds natural in English. Short sentences. A bit of attitude. No corporate speak.
