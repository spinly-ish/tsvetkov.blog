#!/usr/bin/env python3
"""One-shot: add BUILD:BODY_START / BUILD:BODY_END markers around existing
post bodies in posts/<slug>.html and ru/posts/<slug>.html.

Запускается ОДИН раз после миграции контента в Directus, перед первым
`build.py --source=directus`. Идемпотентный — повторный прогон ничего не делает.

Использование:
    python3 scripts/add_body_markers.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Захватываем содержимое <article class="post-content"> ... </article>
# с переносами строк по краям. Группа 1 — начальный тег, 2 — внутренности, 3 — закрывающий тег.
PATTERN = re.compile(
    r'(<article\s+class="post-content">)(.*?)(</article>)',
    re.DOTALL,
)

START_MARKER = "<!-- BUILD:BODY_START -->"
END_MARKER = "<!-- BUILD:BODY_END -->"


def process(path: Path, dry_run: bool) -> str:
    """Возвращает один из: 'added', 'skip-existing', 'no-article', 'error'."""
    txt = path.read_text(encoding="utf-8")

    if START_MARKER in txt and END_MARKER in txt:
        return "skip-existing"

    m = PATTERN.search(txt)
    if not m:
        return "no-article"

    open_tag, body, close_tag = m.groups()
    inner = body.strip("\n")
    new_block = (
        f"{open_tag}\n"
        f"            {START_MARKER}\n"
        f"{inner}\n"
        f"            {END_MARKER}\n"
        f"        {close_tag}"
    )
    new_txt = txt[: m.start()] + new_block + txt[m.end():]

    if not dry_run:
        path.write_text(new_txt, encoding="utf-8")
    return "added"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="Не писать, только показать.")
    args = parser.parse_args()

    targets: list[Path] = []
    targets += sorted((ROOT / "posts").glob("*.html"))
    targets += sorted((ROOT / "ru" / "posts").glob("*.html"))

    counts: dict[str, int] = {"added": 0, "skip-existing": 0, "no-article": 0}
    for path in targets:
        result = process(path, args.dry_run)
        counts[result] = counts.get(result, 0) + 1
        rel = path.relative_to(ROOT)
        print(f"  {result:15s} {rel}")

    print()
    print(f"Files: added={counts.get('added', 0)} skip-existing={counts.get('skip-existing', 0)} no-article={counts.get('no-article', 0)}")
    if args.dry_run:
        print("(dry-run, ничего не записано)")


if __name__ == "__main__":
    main()
