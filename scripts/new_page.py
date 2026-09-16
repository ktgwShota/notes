#!/usr/bin/env python3
"""ページを 1 枚作る。

URL は共有専用で回遊しないため、パーマリンクは意味を持たせずランダム ID にする。
命名を考える工程をなくすのが目的なので、ID はこのスクリプトが決める。

  python3 scripts/new_page.py "bfcache が効かない理由" \
      --description "一覧とリンクプレビューに出る要約" \
      --tags browser,performance
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "pages"
BASE_URL = "https://ktgwshota.github.io/notes/pages"
ID_BYTES = 4

TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — notes</title>
<meta name="description" content="{description}">
<meta name="date" content="{date}">
<meta name="tags" content="{tags}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🧊</text></svg>">
<link rel="stylesheet" href="../../assets/style.css">
</head>
<body>

<div class="wrap">

  <header class="masthead">
    <p class="eyebrow">{eyebrow}</p>
    <h1>{title}</h1>
    <p class="lede">{description}</p>
  </header>

  <section>
    <div class="sec-head">
      <h2>見出し</h2>
      <p>ここから書く。使えるコンポーネントは README を参照。</p>
    </div>
  </section>

  <footer>
    {date} 時点の内容です。
  </footer>

</div>

</body>
</html>
"""


def generate_id() -> str:
    """既存ページと衝突しない ID を返す。"""
    while True:
        page_id = secrets.token_hex(ID_BYTES)
        if not (PAGES_DIR / page_id).exists():
            return page_id


def main() -> int:
    parser = argparse.ArgumentParser(description="notes にページを 1 枚作る")
    parser.add_argument("title", help="ページタイトル")
    parser.add_argument("--description", default="", help="一覧とリンクプレビューに出る要約")
    parser.add_argument("--tags", default="", help="カンマ区切りのタグ")
    parser.add_argument("--eyebrow", default="notes", help="ヘッダー上部の小見出し")
    args = parser.parse_args()

    page_id = generate_id()
    directory = PAGES_DIR / page_id
    directory.mkdir(parents=True)

    (directory / "index.html").write_text(
        TEMPLATE.format(
            title=html.escape(args.title, quote=True),
            description=html.escape(args.description, quote=True),
            tags=html.escape(args.tags, quote=True),
            eyebrow=html.escape(args.eyebrow, quote=True),
            date=dt.date.today().isoformat(),
            url=f"{BASE_URL}/{page_id}/",
        ),
        encoding="utf-8",
    )

    print(f"作成しました: pages/{page_id}/index.html")
    print(f"公開 URL:     {BASE_URL}/{page_id}/")
    print("公開可否チェックを済ませてから push してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
