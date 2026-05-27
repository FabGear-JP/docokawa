---
title: "STEPから部品リストを自動で抜くスクリプトを書いてみた"
emoji: "📋"
type: "tech"
topics: ["機械設計", "Python", "STEP", "BOM", "Excel"]
published: true
---

設計変更のたびに部品リストを手入力していないですか。

CADを開いて、アセンブリの部品一覧をスクショして、Excelに手入力する。
100部品を超えたらコピペでも振り分けに時間がかかる。
同じ部品名でも何度も入力し直すし、誰かが修正したら、それをまた反映させるのに時間がかかる。

その間に転記ミスも出る。
検図すると、「部品数が合わない」って事もちらほら。

「何かこれを自動化できないか」と思って、PythonでSTEPファイルから部品情報を抽出して、そのままExcelに落とすスクリプトを書いてみました。

## 前の記事で説明したこと

STEPファイルをPythonで読み込む基本的な方法は、[前の記事](https://zenn.dev/fabgear_jp/articles/step-diff-comparison)で説明しています。

この記事では、BOM生成に特有の処理 — 部品情報の抽出とExcel出力 — に絞ります。

## アセンブリから部品情報を抽出する

アセンブリのSTEPを読むと、複数のソリッド（部品）が入ってます。

```python
import cadquery as cq
import re

def load_part_names(step_path):
    """STEPファイルのテキストから部品名を抽出"""
    with open(step_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    products = re.findall(r"PRODUCT\s*\(\s*'([^']+)'", text)
    # ルートアセンブリ（UUID形式）は除外
    names = [p for p in products if not (len(p) == 36 and p.count("-") == 4)]
    return names

def extract_bom(step_path):
    """STEPからBOM（部品リスト）を抽出"""
    result = cq.importers.importStep(step_path)
    shape = result.val()  # Compoundを取得
    solids = shape.Solids()  # OCCのShapeリスト
    names = load_part_names(step_path)

    # 部品名が足りない場合は自動採番
    while len(names) < len(solids):
        names.append(f"Part_{len(names)+1:03d}")

    bom = []
    for i, solid in enumerate(solids):
        bb = solid.BoundingBox()
        volume = solid.Volume()
        bom.append({
            "Part Name": names[i] if i < len(names) else f"Part_{i+1:03d}",
            "Width (mm)": round(bb.xlen, 2),
            "Depth (mm)": round(bb.ylen, 2),
            "Height (mm)": round(bb.zlen, 2),
            "Volume (mm³)": round(volume, 1),
        })

    return bom
```

STEPのテキストには `PRODUCT('部品名')` という形式で部品情報が埋まってる。正規表現で抜いて、UUIDっぽいもの（ルートアセンブリの名前）は除外。

## Excelに出力する

pandasでDataFrameにして、そのまま.xlsxに落とす。

```python
import pandas as pd

def export_to_excel(bom, output_path):
    """BOMをExcelに出力"""
    df = pd.DataFrame(bom)
    df.to_excel(output_path, index=False, sheet_name="BOM")
    print(f"BOMを出力しました: {output_path}")
```

出力結果はこんな感じ。

| Part Name | Width (mm) | Depth (mm) | Height (mm) | Volume (mm³) |
|:----------|:-----------|:-----------|:------------|:-------------|
| Base_Plate | 200.0 | 150.0 | 10.0 | 300000.0 |
| Bracket_01 | 50.0 | 30.0 | 20.0 | 30000.0 |
| Shaft | 10.0 | 10.0 | 100.0 | 7853.8 |

これで部品名と寸法が自動で埋まる。手入力の転記ミスがなくなった。

## 数量の集計

部品が重複してたら数量をカウントする。

```python
from collections import Counter

def count_parts(bom):
    """部品名ごとに数量を集計"""
    names = [item["Part Name"] for item in bom]
    counts = Counter(names)

    # 重複を削除して数量を追加
    unique_bom = []
    seen = set()
    for item in bom:
        name = item["Part Name"]
        if name not in seen:
            item["Quantity"] = counts[name]
            unique_bom.append(item)
            seen.add(name)

    return unique_bom
```

同じ部品が複数あれば「Quantity: 4」みたいに集計される。

## 自分の運用で使ってみて

設変のたびにExcelを手で更新してたのが、スクリプト1発で終わる。
部品数100超えても数秒。転記ミスもない。

正直、もう手入力には戻れない。

## 公開してます

もともと自分用に作ったけど、同じ悩みの人は絶対多い。

Windows用のexe、無料。インストーラー版（推奨）とZIP版（インストール不要）の2種類あり。

**ダウンロード**: [ドコカワ v1.0（Windows用・無料）](https://fabgear-jp.github.io/docokawa/?utm_source=zenn)

ダメ出し・改善要望は歓迎。
X：[@FabGear_jp](https://x.com/FabGear_jp)
メール：fabgear.jp@gmail.com
