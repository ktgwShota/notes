# notes

調べたことをまとめて置いておく場所。GitHub Pages で公開しているので、URL を送れば誰でも読めます。

**https://ktgwshota.github.io/notes/**

## 記事の追加手順

1. ルートにディレクトリを 1 つ作り、その中に `index.html` を置く（例: `bfcache/index.html`）
2. `<link rel="stylesheet" href="../assets/style.css">` を読み込む
3. ルートの `index.html` の一覧に 1 件追加する
4. main に push すると数十秒〜2 分で反映される

## 構成

```
.
├── index.html          記事一覧
├── assets/style.css    全記事で共有するスタイル
└── <slug>/index.html   記事本体
```

スタイルは `assets/style.css` に集約しています。色はすべて CSS 変数で定義し、ライト／ダーク両方のテーマに対応済みです。記事側で色を直接書かず、変数を使ってください。

## 使えるコンポーネント

| クラス | 用途 |
| --- | --- |
| `.masthead` / `.eyebrow` / `.lede` | 記事ヘッダー |
| `.premise` | 前提・注記のボックス |
| `.matrix` / `.row` / `.verdict` | 比較マトリクス（横スクロール対応） |
| `.chip.is-block` / `.is-cond` / `.is-ok` | 判定チップ（赤／黄／緑） |
| `.card-list` | 並列項目のカード一覧 |
| `.steps` | 番号付きの手順リスト |
| `.entries` | トップページの記事一覧 |

## ローカル確認

```
python3 -m http.server 8000
```

http://localhost:8000 を開きます。
