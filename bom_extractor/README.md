# BOM Extractor（部品リスト抽出）- MVP版

STEPファイルから部品表（BOM）を自動生成するツール。

## ⚠️ 重要な制限

**数量は参考値です。発注には使えません。**

MVP版は階層構造を保持できないため、すべての部品が「1個」として表示されます。

- ✅ 部品リストの確認
- ✅ 設計レビュー
- ❌ 発注用BOM（数量不正確）

## 使い方

### コマンドライン

```bash
pip install -r requirements.txt
python bom_extractor.py your_assembly.step
```

### Streamlitアプリ（ローカル）

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Streamlit Cloud（Webデモ）

[https://fabgear-bom.streamlit.app/](https://fabgear-bom.streamlit.app/) ※準備中

## 出力例

```
部品名: M3x10_SHCS
数量: 1 (※参考値)
サイズ: 3.00 x 3.00 x 10.00 mm
体積: 70.69 mm³
```

## 依存パッケージ

- cadquery
- pandas
- streamlit（Webアプリ使用時）

## 関連ツール

- [ドコカワ](../) - STEP差分比較ツール
