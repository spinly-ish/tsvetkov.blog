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

## Adding a New Post

Two files must be updated:

1. **Create** `posts/<slug>.html` — copy any existing post as a template
2. **Prepend** a new `<article class="blog-post">` block at the top of the blog list in `index.html`

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

English. Mark Manson-inspired: direct, informal, punchy short paragraphs, conversational tone. Topics: product strategy, tech, behavior, simplicity vs complexity.
