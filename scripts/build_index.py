#!/usr/bin/env python3
"""ページのディレクトリを走査して、トップページの一覧を再生成する。

各ページの <head> から以下を読み取る:
  <title>            ページタイトル（末尾の " — notes" は除去）
  <meta name="description">  一覧に出す要約
  <meta name="date">         公開日（YYYY-MM-DD）
  <meta name="tags">         カンマ区切りのタグ（任意）

index.html の ENTRIES:START / ENTRIES:END マーカーの間を書き換える。
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
START = "<!-- ENTRIES:START -->"
END = "<!-- ENTRIES:END -->"
TITLE_SUFFIX = " — notes"
EXCLUDED_DIRS = {"assets", "scripts", ".git", ".github"}


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
    for path in sorted(ROOT.glob("*/index.html")):
        page_id = path.parent.name
        if page_id in EXCLUDED_DIRS or page_id.startswith("."):
            continue

        source = path.read_text(encoding="utf-8")
        title = extract_title(source)
        date = extract_meta(source, "date")

        missing = [k for k, v in (("title", title), ("date", date)) if not v]
        if missing:
            raise SystemExit(f"エラー: {page_id}/index.html に {', '.join(missing)} がありません")

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
    return sorted(pages, key=lambda a: (a["date"], a["id"]), reverse=True)


def render(pages: list[dict[str, object]]) -> str:
    if not pages:
        return '      <li><span class="summary">ページはまだありません。</span></li>'

    blocks = []
    for page in pages:
        lines = [
            "      <li>",
            f'        <a href="{page["id"]}/">',
            f'          <span class="title">{html.escape(str(page["title"]))}</span>',
            f'          <span class="date">{html.escape(str(page["date"]))}</span>',
        ]
        if page["summary"]:
            lines.append(
                f'          <span class="summary">{html.escape(str(page["summary"]))}</span>'
            )
        if page["tags"]:
            pills = "".join(
                f'<span class="tag-pill">{html.escape(t)}</span>'
                for t in page["tags"]  # type: ignore[union-attr]
            )
            lines.append(f'          <span class="tags">{pills}</span>')
        lines += ["        </a>", "      </li>"]
        blocks.append("\n".join(lines))

    return "\n".join(blocks)


def main() -> int:
    source = INDEX.read_text(encoding="utf-8")
    if START not in source or END not in source:
        raise SystemExit(f"エラー: index.html に {START} / {END} が見つかりません")

    pages = collect_pages()
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        f"{START}\n{render(pages)}\n{' ' * 6}{END}",
        source,
        flags=re.DOTALL,
    )

    if updated == source:
        print(f"変更なし（ページ {len(pages)} 件）")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    print(f"一覧を更新しました（{len(pages)} 件）")
    for page in pages:
        print(f"  {page['date']}  {page['id']}  {page['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
