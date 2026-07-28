# FabGear STEP Tools

製造業設計者向けのSTEPファイルツール集

**メインサイト**: [ドコカワ LP](https://fabgear-jp.github.io/docokawa/) | [FabGear ポートフォリオ](https://fabgear-jp.github.io/)

---

## ドコカワ（STEP差分比較）

「修正しました、ご確認ください」とだけ書いてあるメールが来る。どこが変わったのかは書いていない。だからCADを開いて、修正前のデータと見比べる。

製作品20品、購入品20品、ボルト類100品が1ユニット。これが複数集まった製品になると、目視で全部確認するのに30分かかることがある。それでも変更漏れを見落とす。

このツールはその確認を数値でやるためのもの。

![STEPファイルを2つ読み込むと差分テーブルと3D比較が並んで表示されるデモ](docs/docokawa_demo.gif)

**ダウンロード**: [GitHub Releases](https://github.com/FabGear-JP/docokawa/releases/latest)（Windows exe・インストール不要）

### できること

STEPファイルを2つ読み込むと、部品ごとに「追加 / 削除 / 変更 / 変更なし」を判定してテーブルで出す。修正フラグが立った部品だけ3Dビューで確認して、結果はCSVで書き出せる。

気になったことがあれば [こちらのフォームから教えてもらえると助かります](https://fabgear-jp.github.io/docokawa/)。

---

## 部品リスト抽出（BOM Extractor）— MVP版

STEPファイルから部品表を自動生成する。

- 部品名・サイズ・体積を自動抽出
- 標準部品（ネジ・ベアリング等）の型番認識
- 多言語対応（日本語・中国語）

⚠️ MVP版のため数量は参考値です。発注用途には使えません。

**Webデモ（インストール不要）**: [Streamlit Cloud](https://docokawa-3tamcfxd9wsaq3bvxfxauw.streamlit.app/)

ローカルで動かすには `cd bom_extractor` → `pip install -r requirements.txt` → `streamlit run streamlit_app.py` の順で。

---

## 共通仕様

無料 / Windows 10・11 / オフライン動作（機密CADでも安心）

---

## 開発者

機械設計者が作った、設計者向けのツール。

- GitHub: [FabGear-JP](https://github.com/FabGear-JP)
- Qiita: [記事一覧](https://qiita.com/FabGear_JP)
- Zenn: [記事一覧](https://zenn.dev/fabgear_jp)

---

# English

## FabGear STEP Tools

A collection of STEP file tools for mechanical designers.

**Main site**: [Docokawa LP](https://fabgear-jp.github.io/docokawa/) | [FabGear Portfolio](https://fabgear-jp.github.io/)

---

## Docokawa (STEP diff viewer)

When a revised STEP file arrives, the message is usually just "please review." No list of what changed. So you open the CAD, load the old file next to the new one, and compare manually.

One unit can have 20 machined parts, 20 purchased parts, and 100 fasteners. A full visual check can take 30 minutes — and still miss something.

This tool does the comparison numerically.

**Download**: [GitHub Releases](https://github.com/FabGear-JP/docokawa/releases/latest) (Windows exe, no install needed)

### What it does

Load two STEP files and it outputs a table: added / removed / modified / unchanged per part. Flagged parts can be checked in a 3D view. Results export to CSV.

If something is not working the way you expect, the [feedback form here](https://fabgear-jp.github.io/docokawa/) goes directly to the developer.

---

## BOM Extractor — MVP

Generates a parts list from a STEP file.

- Extracts part names, sizes, and volumes automatically
- Recognizes standard parts (screws, bearings, etc.)
- Japanese and Chinese part name support

⚠️ MVP: quantities are approximate. Not for production BOM use.

**Web demo (no install)**: [Streamlit Cloud](https://docokawa-3tamcfxd9wsaq3bvxfxauw.streamlit.app/)

To run locally: `cd bom_extractor` → `pip install -r requirements.txt` → `streamlit run streamlit_app.py`

---

## Common specs

Free / Windows 10 and 11 / Runs offline (safe for confidential CAD files)

---

## Developer

A mechanical designer building tools for mechanical designers.

- GitHub: [FabGear-JP](https://github.com/FabGear-JP)
- Qiita: [Articles](https://qiita.com/FabGear_JP)
- Zenn: [Articles](https://zenn.dev/fabgear_jp)
