---
title: "PDF仕様書から寸法・公差・部品表を正規表現で抽出してみた"
emoji: "📄"
type: "tech"
topics: ["Python", "PDF", "正規表現", "機械設計", "pdfplumber"]
published: true
---

50ページの仕様書を手で写すのが面倒だった。入力ミスがあると、そのまま客先に送って迷惑をかけることになる。部品表も寸法も書いてあるのに、スプレッドシートにひたすら手入力していた。製作品20品・購入品20品・ボルト類100品が1ユニット。これが複数集まった製品だと、見落としと入力ミスが増える。

Pythonで PDF仕様書からテキストを抽出して、寸法・公差・BOMを正規表現でパターンマッチする仕組みを作ってみました。STEP差分比較ツール「ドコカワ」の内部で使っている補助機能です。完全自動ではないけど、ネイティブPDFなら8割くらいは自動で取れるので、残り2割は手で直す前提で使っています。

---

## ネイティブPDFだけを対象に

入ってくるPDFは大きく2種類ある。CADから直接出力されたもの（ネイティブPDF）と、紙の仕様書をスキャンしたもの（スキャンPDF）。

今のところ、**ネイティブPDFだけを対象** にしている。スキャンPDFをOCRで処理すると、品質判定・前処理・ノイズフィルタリングとやることが爆発的に増えるので、ネイティブPDFが送られてくる限りは優先度を上げなかった。

```python
import pdfplumber

with pdfplumber.open('specification.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

`pdfplumber` を使うと、ネイティブPDFのテキストはほぼ正確に抽出できる。行の順序が保たれるし、テーブル構造も比較的強い。PyPDF2より後発でテキスト抽出に最適化されているのが理由だと思う。

スキャンPDFが必要になったときは、そのとき考える。

---

## 寸法値を正規表現で抽出する

PDFから取ったテキストには、「幅 100mm」「高さ：50」「W100×D50」とか、いろいろなフォーマットで寸法が混在している。

単純なテキスト検索では漏れが出るので、正規表現のパターンマッチで拾う。実装した関数がこれ。

```python
def extract_dimensions(text: str) -> list[dict]:
    """テキストから寸法値を抽出"""
    results = []
    seen = set()

    # ラベル付きパターン（日本語・英語）
    label_patterns = [
        (r"幅\s*[：:]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "幅"),
        (r"奥行\s*[：:]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "奥行"),
        (r"高さ\s*[：:]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "高さ"),
        (r"Width\s*[：:]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "幅"),
        (r"Depth\s*[：:]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "奥行"),
        (r"Height\s*[：:]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "高さ"),
        (r"\bW\s*[：:]?\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "幅"),
        (r"\bD\s*[：:]?\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "奥行"),
        (r"\bH\s*[：:]?\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?", "高さ"),
    ]

    for pattern, label in label_patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            value = float(m.group(1))
            unit = (m.group(2) or "mm").lower()
            key = (label, round(value, 6))
            if key not in seen:
                seen.add(key)
                results.append({"label": label, "value": value, "unit": unit})

    # × 区切り寸法: 100×50×30mm 形式
    if not results:
        cross_pattern = (
            r"([0-9]+\.?[0-9]*)\s*[×x]\s*"
            r"([0-9]+\.?[0-9]*)\s*[×x]\s*"
            r"([0-9]+\.?[0-9]*)\s*(mm|cm|m)?"
        )
        m = re.search(cross_pattern, text, re.IGNORECASE)
        if m:
            unit = (m.group(4) or "mm").lower()
            for idx, label in enumerate(["幅", "奥行", "高さ"]):
                results.append({"label": label, "value": float(m.group(idx + 1)), "unit": unit})

    return results
```

パターンの優先順位で誤マッチが減るのかなとは思っている。ラベル付き（「幅：100」）から探して、見つからなければ × 区切り、それでも見つからなければ数値だけを拾う。この順序で探している。

---

## 公差情報も正規表現で

「±0.1mm」「公差: ±0.05」「100±0.05」とか、公差もいろいろな書き方がある。

```python
def extract_tolerances(text: str) -> dict:
    """テキストから公差情報を抽出"""
    result = {"global": None, "per_label": {}}

    # ラベルの正規化マップ
    LABEL_MAP = {
        "幅": "幅", "Width": "幅", "W": "幅",
        "奥行": "奥行", "Depth": "奥行", "D": "奥行",
        "高さ": "高さ", "Height": "高さ", "H": "高さ",
    }

    # ラベル付き公差: 「幅 ±0.1mm」「Width: ±0.05」
    label_tol_pattern = (
        r"(幅|奥行|高さ|Width|Depth|Height|W|D|H)"
        r"\s*[：:（(]?\s*"
        r"[±＋-]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?"
    )
    for m in re.finditer(label_tol_pattern, text, re.IGNORECASE):
        label_key = m.group(1)
        label = LABEL_MAP.get(label_key, label_key)
        value = float(m.group(2))
        if label not in result["per_label"]:
            result["per_label"][label] = value

    # インライン公差: 「100±0.05mm」
    inline_pattern = r"[0-9]+\.?[0-9]*\s*[±＋]\s*([0-9]+\.?[0-9]*)\s*(mm|cm|m)?"
    for m in re.finditer(inline_pattern, text, re.IGNORECASE):
        value = float(m.group(1))
        if result["global"] is None:
            result["global"] = value

    return result
```

ラベル別に公差を分けている。「幅は±0.1、高さは±0.05」みたいに異なる場合があるので、1つのグローバル公差だけでは不足する。

---

## 部品表（BOM）を行ごとにパターンマッチ

部品表の各行には、「数量」「品名」「寸法」の情報が混在している。行ごとに処理して、それぞれのパターンを探す。

```python
def extract_bom(text: str) -> list[dict]:
    """テキストからBOM情報を抽出"""
    results = []
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 数量パターン: 「×2」「2個」「qty: 2」など
        qty_patterns = [
            r"数量[：:\s]*([0-9]+)",
            r"[Qq](?:ty|uantity)[：:\s.]*([0-9]+)",
            r"[×xX]([0-9]+)(?:\s|$)",
            r"([0-9]+)\s*(?:個|本|枚|点|pcs?)",
        ]
        quantity = None
        for pat in qty_patterns:
            m = re.search(pat, line, re.IGNORECASE)
            if m:
                try:
                    quantity = int(m.group(1))
                    break
                except (ValueError, IndexError):
                    pass

        if quantity is None:
            continue  # 数量が読み取れない行はスキップ

        # 寸法パターン: 「100×50×30mm」
        dim_pattern = (
            r"([0-9]+\.?[0-9]*)\s*[×xX]\s*"
            r"([0-9]+\.?[0-9]*)\s*[×xX]\s*"
            r"([0-9]+\.?[0-9]*)(?:\s*(mm|cm|m))?"
        )
        width = depth = height = None
        unit = "mm"
        dm = re.search(dim_pattern, line, re.IGNORECASE)
        if dm:
            width = float(dm.group(1))
            depth = float(dm.group(2))
            height = float(dm.group(3))
            unit = (dm.group(4) or "mm").lower()

        # 品名: 数字・記号を除いたテキスト
        name_text = re.sub(r"[0-9×xX.±＋\-\s:：（()）,，]", " ", line)
        name_text = re.sub(r"(mm|cm|個|本|枚|点|qty|quantity)", " ", name_text, flags=re.IGNORECASE)
        name = " ".join(name_text.split())[:40]

        item = {"name": name, "quantity": quantity, "unit": unit}
        if width is not None:
            item["width"] = width
            item["depth"] = depth
            item["height"] = height

        results.append(item)

    return results
```

数量パターンで行をふるい分けるのが効果的だった。

---

## CSVで検証可能な形に

抽出した情報をCSVに落とすのは簡単。重要なのは、出力の検証ステップ。

```python
extracted_bom = extract_bom(pdf_text)

# ドコカワの場合、CSVに落とさずに内部的にDataFrameで処理
# ただ、検証しやすいように出力可能な形にしている
for item in extracted_bom:
    print(f"{item['name']}: {item['quantity']}個 {item.get('width', '-')}×{item.get('depth', '-')}×{item.get('height', '-')}{item['unit']}")
```

全部が正確に抽出できるわけではない。フォーマットがバラバラな仕様書だと、パターンマッチの精度は下がる。想定しているフローはこんな感じ:

1. PDFを投げる
2. スクリプトが自動抽出（5〜30秒）
3. 抽出結果を表示
4. 元のPDFと見比べて、漏れや誤りがないか確認
5. 必要に応じて手で追加・修正

「最後は必ず目で確認する」が前提。

---

## まだ対応していないこと

- **スキャンPDF** — OCRが必要になるので、別の話。ネイティブPDFが十分にあるうちは優先度を上げていない
- **テーブルからの抽出** — pdfplumberのテーブル機能を使えば可能だけど、今のところ行単位のテキスト処理で足りている
- **単位の統一** — mmとinchが混在する場合の自動変換。実運用で必要になったらやる

---

## パターンマッチだからできること、できないこと

パターンマッチの強さは「フォーマットが決まっている情報」の抽出。寸法値・公差・数量は、ほぼ数字と記号で表現されるので、正規表現で高精度に拾える。

弱いのは「品名」みたいなフリーテキスト。数字・記号を除いても、ノイズが混ざることがある。品名は最後に目で確認するしかない。
