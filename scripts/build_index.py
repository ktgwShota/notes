#!/usr/bin/env python3
"""記事ディレクトリを走査して、トップページの記事一覧を再生成する。

各記事の <head> から以下を読み取る:
  <title>            記事タイトル（末尾の " — notes" は除去）
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


def collect_articles() -> list[dict[str, object]]:
    articles = []
    for path in sorted(ROOT.glob("*/index.html")):
        slug = path.parent.name
        if slug in EXCLUDED_DIRS or slug.startswith("."):
            continue

        source = path.read_text(encoding="utf-8")
        title = extract_title(source)
        date = extract_meta(source, "date")

        missing = [k for k, v in (("title", title), ("date", date)) if not v]
        if missing:
            raise SystemExit(f"エラー: {slug}/index.html に {', '.join(missing)} がありません")

        tags = [t.strip() for t in extract_meta(source, "tags").split(",") if t.strip()]
        articles.append(
            {
                "slug": slug,
                "title": title,
                "date": date,
                "summary": extract_meta(source, "description"),
                "tags": tags,
            }
        )

    # 新しい記事を先頭に。同日の場合は slug で安定させる
    return sorted(articles, key=lambda a: (a["date"], a["slug"]), reverse=True)


def render(articles: list[dict[str, object]]) -> str:
    if not articles:
        return '      <li><span class="summary">記事はまだありません。</span></li>'

    blocks = []
    for article in articles:
        lines = [
            "      <li>",
            f'        <a href="{article["slug"]}/">',
            f'          <span class="title">{html.escape(str(article["title"]))}</span>',
            f'          <span class="date">{html.escape(str(article["date"]))}</span>',
        ]
        if article["summary"]:
            lines.append(
                f'          <span class="summary">{html.escape(str(article["summary"]))}</span>'
            )
        if article["tags"]:
            pills = "".join(
                f'<span class="tag-pill">{html.escape(t)}</span>'
                for t in article["tags"]  # type: ignore[union-attr]
            )
            lines.append(f'          <span class="tags">{pills}</span>')
        lines += ["        </a>", "      </li>"]
        blocks.append("\n".join(lines))

    return "\n".join(blocks)


def main() -> int:
    source = INDEX.read_text(encoding="utf-8")
    if START not in source or END not in source:
        raise SystemExit(f"エラー: index.html に {START} / {END} が見つかりません")

    articles = collect_articles()
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        f"{START}\n{render(articles)}\n{' ' * 6}{END}",
        source,
        flags=re.DOTALL,
    )

    if updated == source:
        print(f"変更なし（記事 {len(articles)} 件）")
        return 0

    INDEX.write_text(updated, encoding="utf-8")
    print(f"記事一覧を更新しました（{len(articles)} 件）")
    for article in articles:
        print(f"  {article['date']}  {article['slug']}  {article['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
