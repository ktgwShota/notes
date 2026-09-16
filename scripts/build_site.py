#!/usr/bin/env python3
"""公開用のサイトを _site/ に組み立てる。

リポジトリ上はページを pages/ にまとめておき、公開時はルート直下へ展開する。
    リポジトリ        公開後
    pages/<id>/  →   /<id>/
    assets/      →   /assets/
    templates/index.html + 各ページのメタ情報  →  /index.html

各ページの <head> から以下を読み取って一覧を組み立てる:
  <title>                    ページタイトル（末尾の " — notes" は除去）
  <meta name="description">  一覧に出す要約
  <meta name="date">         公開日（YYYY-MM-DD）
  <meta name="tags">         カンマ区切りのタグ（任意）
"""

from __future__ import annotations

import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "pages"
ASSETS_DIR = ROOT / "assets"
TEMPLATE = ROOT / "templates" / "index.html"
OUT_DIR = ROOT / "_site"
START = "<!-- ENTRIES:START -->"
END = "<!-- ENTRIES:END -->"
TITLE_SUFFIX = " — notes"
INDENT = " " * 6


def extract_meta(source: str, name: str) -> str:
    """<meta name="..." content="..."> を属性の順序に依らず取り出す。"""
    for tag in re.findall(r"<meta\b[^>]*>", source, re.IGNORECASE):
        if not re.search(rf'name=["\']{name}["\']', tag, re.IGNORECASE):
            continue
        content = re.search(r'content=["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if content:
            return content.group(1).strip()
    return ""


def extract_title(source: str) -> str:
    match = re.search(r"<title>(.*?)</title>", source, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = html.unescape(match.group(1)).strip()
    return title[: -len(TITLE_SUFFIX)] if title.endswith(TITLE_SUFFIX) else title


def collect_pages() -> list[dict[str, object]]:
    pages = []
    for path in sorted(PAGES_DIR.glob("*/index.html")):
        page_id = path.parent.name
        source = path.read_text(encoding="utf-8")
        title = extract_title(source)
        date = extract_meta(source, "date")

        missing = [k for k, v in (("title", title), ("date", date)) if not v]
        if missing:
            raise SystemExit(f"エラー: pages/{page_id}/index.html に {', '.join(missing)} がありません")

        tags = [t.strip() for t in extract_meta(source, "tags").split(",") if t.strip()]
        pages.append(
            {
                "id": page_id,
                "title": title,
                "date": date,
                "summary": extract_meta(source, "description"),
                "tags": tags,
            }
        )

    # 新しいページを先頭に。同日の場合は ID で安定させる
    return sorted(pages, key=lambda p: (p["date"], p["id"]), reverse=True)


def render_entries(pages: list[dict[str, object]]) -> str:
    if not pages:
        return ""

    blocks = []
    for page in pages:
        tags: list[str] = page["tags"]  # type: ignore[assignment]
        # 絞り込みは JS が data 属性だけを見る（タイトル・要約・タグを対象にする）
        haystack = " ".join([str(page["title"]), str(page["summary"]), *tags]).lower()

        lines = [
            f'{INDENT}<li class="entry" data-search="{html.escape(haystack)}"'
            f' data-tags="{html.escape(" ".join(tags))}">',
            f'{INDENT}  <a class="entry-link" href="{page["id"]}/">',
            f'{INDENT}    <span class="title">{html.escape(str(page["title"]))}</span>',
        ]
        if page["summary"]:
            lines.append(
                f'{INDENT}    <span class="summary">{html.escape(str(page["summary"]))}</span>'
            )
        lines += [
            f"{INDENT}  </a>",
            f'{INDENT}  <div class="entry-side">',
            f'{INDENT}    <span class="date">{html.escape(str(page["date"]))}</span>',
            f'{INDENT}    <button type="button" class="copy">リンクをコピー</button>',
            f"{INDENT}  </div>",
        ]
        if tags:
            pills = "".join(
                f'<button type="button" class="tag-pill" data-tag="{html.escape(t)}"'
                f' aria-pressed="false">{html.escape(t)}</button>'
                for t in tags
            )
            lines.append(f'{INDENT}  <div class="entry-tags">{pills}</div>')
        lines.append(f"{INDENT}</li>")
        blocks.append("\n".join(lines))

    return "\n".join(blocks)


def build_index(pages: list[dict[str, object]]) -> str:
    source = TEMPLATE.read_text(encoding="utf-8")
    if START not in source or END not in source:
        raise SystemExit(f"エラー: {TEMPLATE} に {START} / {END} が見つかりません")

    return re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        f"{START}\n{render_entries(pages)}\n{INDENT}{END}",
        source,
        flags=re.DOTALL,
    )


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()

    pages = collect_pages()

    # ページはルート直下へ展開する（URL に pages/ を含めない）
    for page in pages:
        shutil.copytree(PAGES_DIR / str(page["id"]), OUT_DIR / str(page["id"]))

    if ASSETS_DIR.exists():
        shutil.copytree(ASSETS_DIR, OUT_DIR / "assets")

    (OUT_DIR / "index.html").write_text(build_index(pages), encoding="utf-8")

    print(f"_site/ を組み立てました（ページ {len(pages)} 件）")
    for page in pages:
        print(f"  {page['date']}  /{page['id']}/  {page['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
