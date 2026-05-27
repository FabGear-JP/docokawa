---
title: "STEPから寸法まで自動で抜いてるPythonライブラリ5つ"
emoji: "🐍"
type: "tech"
topics: ["Python", "機械設計", "STEP", "CAD", "自動化"]
published: true
---

他社に依頼して設計してもらった時、stpデータでの納品もままあります。
修正が出るたびにSTEPファイルを開いて、何が変わったのか比較して図面を修正する作業が発生します。
もちろんBOMが変わることも。
部品が100個を超えると、それだけで想定外の作業が膨らんでいきます。
転記ミスも出ますし、前回の修正がどこだったかもわからなくなる始末です。

何とかこれを自動化できないかと思い、Pythonで設計に必要な情報を一気に抜くスクリプトを書き始めました。
そこでよく使っているライブラリが5つあります。
調べた限り、どれもよく使われているもののようです。

## 1. CadQuery — STEP読み込みと寸法・形状の抽出

STEPファイルを読み込んで、部品の寸法・形状情報を抽出するためのライブラリです。
これなしでは始まらない。

CadQueryを使うと、STEPの読み込みはもちろん、バウンディングボックスや面数、体積なんかも自動で取得できます。

```python
import cadquery as cq

# STEPを読み込む
result = cq.importers.importStep("assembly.step")
shape = result.val()  # Compoundを取得

# 部品（ソリッド）を抽出
solids = shape.Solids()

for solid in solids:
    bb = solid.BoundingBox()
    print(f"幅: {bb.xlen:.2f}mm, 奥行: {bb.ylen:.2f}mm, 高さ: {bb.zlen:.2f}mm")
    print(f"体積: {solid.Volume():.1f}mm³, 面数: {len(solid.Faces())}")
```

修正前後のSTEPを比較して「この部品の何が変わったのか」を自動判定するのに使っています。
バウンディングボックスの変化で形状変更を検出し、体積差で材料の変更も捕捉可能です。
精度は1mmオーダーあれば十分。

ただし、インストールが環境依存なので、ビルド済みバイナリを使うのが楽でした。

## 2. pdfplumber — 仕様書PDFから寸法・部品表を抽出

設計変更と一緒に上がってくるのが、修正内容を書いたPDF仕様書です。
そこに変更寸法と部品構成が書いてあります。

pdfplumberを使うと、PDFのテーブルやテキストを構造化して抽出できます。

```python
import pdfplumber

with pdfplumber.open("specification.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)

        # テーブルも抽出できる
        tables = page.extract_tables()
        for table in tables:
            print(table)
```

正規表現と組み合わせて、「幅：100mm」とか「±0.1」みたいな寸法・公差を抽出する。
部品表がテーブルで書かれてれば、そのまま抽出してDataFrameに突っ込める。

PyPDF2より後発で、テキスト抽出精度が高い印象です。

## 3. openpyxl — Excel BOM の読み書き

部品表の出力先はだいたいExcel。
openpyxlを使うと、.xlsxを直接読み書きできる。

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "BOM"

# ヘッダー
ws.append(["Part Name", "Quantity", "Width", "Depth", "Height"])

# 部品データを追記
for part in bom_list:
    ws.append([part["name"], part["qty"], part["w"], part["d"], part["h"]])

wb.save("bom_output.xlsx")
```

設変記録をそのままExcelに落とせるので、検図で使いやすい。

## 4. pandas — データの集計・変換

部品リストの重複削除、数量カウント、フィルタリングにはpandasが便利。

```python
import pandas as pd

# BOMをDataFrameに
df = pd.DataFrame(bom_list)

# 部品名でグルーピング、数量を集計
df_grouped = df.groupby("Part Name").agg({"Quantity": "sum"}).reset_index()

# Excel出力
df_grouped.to_excel("bom_summary.xlsx", index=False)
```

STEPから抽出した部品リストを、実務で使える形に変換するのに欠かせない。

## 5. pyvista — 3D可視化

部品の変更箇所を目で確認したい時に使う。

```python
import pyvista as pv

# STLやVTKを読み込んで可視化
mesh = pv.read("part.stl")
mesh.plot(color="lightblue")
```

CadQueryで取り出した形状をpyvistaに渡して、変更箇所を色分け表示する。
Streamlitと組み合わせると、Webブラウザで3Dビューアが動く。

レビューで「どこが変わったか」を見せるのに便利。

## 自分の運用で使ってみて

この5つを組み合わせて、STEPと仕様書PDFを投げるとBOMと寸法チェック結果が出てくるツールを作りました。

設変のたびに30分かけて手作業でやってたのが、数秒で終わる。
転記ミスもなくなった。

正直、もう手作業には戻れない。

## 公開してます

もともと自分用に作ったけど、同じ悩みの人は絶対多い。

Windows用のexe、無料。インストーラー版（推奨）とZIP版（インストール不要）の2種類あり。

**ダウンロード**: [ドコカワ v1.0（Windows用・無料）](https://fabgear-jp.github.io/docokawa/?utm_source=zenn)

ダメ出し・改善要望は歓迎。
X：[@FabGear_jp](https://x.com/FabGear_jp)
メール：fabgear.jp@gmail.com
