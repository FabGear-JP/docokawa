# FabGear STEP Tools

製造業設計者向けのSTEPファイルツール集

## ツール一覧

### 1. ドコカワ（STEP差分比較）

設変前後で「どこ変わったの？」を自動検出。

- 部品単位の差分検出（追加・削除・変更）
- 3Dビューで形状比較
- PDF仕様書との寸法照合
- CSV/Excel出力

**ダウンロード**: [GitHub Releases](https://github.com/FabGear-JP/docokawa/releases/latest)

### 2. 部品リスト抽出（BOM Extractor）- MVP版

STEPファイルから部品表を自動生成。

- 部品名・サイズ・体積を自動抽出
- 標準部品（ネジ・ベアリング等）の型番認識
- 多言語対応（日本語・中国語）
- Webデモあり（インストール不要）

**Webデモ**: [Streamlit Cloud](https://docokawa-3tamcfxd9wsaq3bvxfxauw.streamlit.app/)

**ローカル実行**:
```bash
cd bom_extractor
pip install -r requirements.txt
python bom_extractor.py your_assembly.step
```

⚠️ **注意**: MVP版のため数量は参考値です。発注用途には使えません。

---

## 共通仕様

| 項目 | 内容 |
|:-----|:-----|
| 価格 | 無料 |
| プラットフォーム | Windows 10/11 |
| ネットワーク | オフライン動作（データは外部送信されません） |

機密CADデータも安心して使えます。

---

## 開発者

- GitHub: [FabGear-JP](https://github.com/FabGear-JP)
- Qiita: [FabGear_JP](https://qiita.com/FabGear_JP)
- Zenn: [fabgear_jp](https://zenn.dev/fabgear_jp)

---

# English

## FabGear STEP Tools

A collection of STEP file utilities for mechanical designers.

### 1. Dokocawa (STEP Diff Checker)

Compare two STEP files and detect what changed between design revisions.

- Part-level diff (added, removed, modified)
- 3D viewer comparison
- PDF spec sheet cross-reference
- CSV/Excel export

**Download**: [GitHub Releases](https://github.com/FabGear-JP/docokawa/releases/latest)

### 2. BOM Extractor (MVP)

Auto-generate a parts list from STEP files.

- Extract part names, sizes, volumes
- Recognize standard parts (screws, bearings)
- Multi-language support (Japanese, Chinese)
- Web demo available

**Web Demo**: [Streamlit Cloud](https://docokawa-3tamcfxd9wsaq3bvxfxauw.streamlit.app/)

⚠️ **Note**: MVP version — quantities are approximate. Not for ordering.
