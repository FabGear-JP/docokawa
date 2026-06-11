---
title: "「何が変わったか」をテーブルで見せる — 修正STEPの確認を数値で判定する"
emoji: "📊"
type: "tech"
topics: ["機械設計", "Python", "STEP", "CadQuery", "設計効率化"]
published: true
---

前に[『STEPファイルの差分比較、毎回目視でやってませんか』](https://zenn.dev/fabgear_jp/articles/step-diff-comparison)という記事を書いた。目視での確認が大変だという話だった。

今回は、その「どこが・どれだけ変わったか」を部品単位で数値化するところの実装の話。判定ロジック、精度、限界をまとめた。

---

## 困り事のおさらい

設計変更したSTEPが戻ってくる。「修正しました」とだけ書いてある。どこを修正したのか全然わからない。

複数の部品を目視でCADを開いて比較すると30分かかることがある。その間に変更漏れを見落とすこともある。

製作品20品、購入品20品、ボルト類100品が1ユニット。これを複数集めた製品だと、比較対象が数百部品になる。もう目視では無理。

正直、前の記事では「比較ができる」という部分に焦点を当てたんだけど、実装してみて気づいたのは「数値で判定する」という部分がけっこう厄介だということ。

---

## どうやって「変わったか」を数値で判定するのか

STEPファイルを読み込んで、部品ごとに特性を比べる。バウンディングボックス（部品を囲む直方体のサイズ）・体積・面数で見ると「変わった」かどうかがわかる。

ただし、ここからが複雑。この3つを全部見たら、どれが重要か。どのくらい変わったら「修正」として拾い上げるのか。

正直、最初は「3つのうち1つでも変わってたら修正」でいいと思ってた。でも実装してみたら、そうじゃなかった。

たとえば穴を1つ追加した部品がある。バウンディングボックスは変わらない（穴は内側だから外形は同じ）。でも体積は減る。面数は増える。

こういう時に「3つのうち1つ変わってたら修正」ルールだと正確に拾える。ただ、誤検知も増える。

### 体積変化を重視する理由

結局のところ、「部品の実体が変わったか」が一番重要。穴を追加して体積が減ったなら、それは加工仕様が変わってるということ。

バウンディングボックスは見た目の外形。面数は複雑さ。これらも参考にはなるけど、製造の実務では「体積がいくら減ったか」の方が直結する。

だから体積変化率を軸にしてる。ざっくり、体積が5%以上変わったら要確認って感じ。これ以下だと、誤検知が多くて実務的でない。

## 実装してわかったこと

```python
import cadquery as cq
import pandas as pd

def get_part_properties(step_file):
    """STEPファイルから部品のプロパティを取得"""
    doc = cq.importers.importStep(step_file)
    parts = {}
    
    for label in doc.getObjects():
        if "Body" in label.Name or "Solid" in label.Name:
            shape = label.Shape
            bbox = shape.BoundingBox()
            volume = shape.Volume()
            face_count = len(shape.Faces())
            
            parts[label.Label] = {
                "bbox_x": bbox.xlen,
                "bbox_y": bbox.ylen,
                "bbox_z": bbox.zlen,
                "volume": volume,
                "faces": face_count
            }
    
    return parts

def compare_parts(before_file, after_file):
    """修正前後の部品を比較"""
    before = get_part_properties(before_file)
    after = get_part_properties(after_file)
    
    results = []
    
    for part_name in before.keys():
        if part_name not in after:
            results.append({
                "part": part_name,
                "status": "削除",
                "volume_change_pct": -100.0
            })
            continue
        
        b = before[part_name]
        a = after[part_name]
        
        # 体積変化率を計算
        if b["volume"] > 0:
            volume_change = abs(a["volume"] - b["volume"]) / b["volume"] * 100
        else:
            volume_change = 0
        
        # 体積が5%以上変わったら「修正」と判定
        if volume_change >= 5.0:
            results.append({
                "part": part_name,
                "status": "修正",
                "volume_change_pct": volume_change
            })
        else:
            results.append({
                "part": part_name,
                "status": "変更なし",
                "volume_change_pct": volume_change
            })
    
    for part_name in after.keys():
        if part_name not in before:
            results.append({
                "part": part_name,
                "status": "追加",
                "volume_change_pct": None
            })
    
    return pd.DataFrame(results)

# 使用例
df = compare_parts("修正前.step", "修正後.step")
df_modified = df[df["status"] != "変更なし"]
print(df_modified[["part", "status", "volume_change_pct"]])
```

最初は修正前後のバウンディングボックス・体積・面数を全部見てて、「1つでも変わってたら修正」という判定をしてた。

実装してみたら、これだと誤検知が多くて。CADが出力したメタデータの微細な違いで「変わった」って判定されちゃう。

結局、体積変化率を軸にして、5%以上変わったものだけ「修正」としてる。この基準だと、実務的な変更（穴追加、リブ削除、素材厚さ変更等）をちゃんと拾える。

---

## 実務で使ってみて

テーブルで修正部品が一覧で出てくると、レビューの説明が楽になる。200部品のアセンブリで、修正フラグが立った部品だけを確認する。全部見て回るより段違いに早い。

修正確認に30分かかってた時間が、5分で終わることもある。変更漏れを見落とすリスクも下がる。目視で200部品見てると、途中で意識がぼやけるけど、テーブルなら漏れようがない。

ただし、自動検出した結果には必ず3Dビューアで目視確認が必要。体積変化率の5%という基準は万能じゃないから。

CADが吐き出したメタデータ・単位の違い・ツールごとのSTEP出力の違いで、実は変わってないのに「変わった」って判定されることもある。

---

## 限界

STEPファイル自体に問題がある場合、このやり方も限界。

ツールAで出力したSTEPと、ツールBで出力したSTEPでは、部品名の埋め込み方が全然違う。階層が深い場合も解析が複雑になる。あと、単位の違い。mmで吐き出されたのか、インチで吐き出されたのか。体積の絶対値が変わるから、比較ロジックが狂う。

この辺りは、実装時に「あ、これ対応が必要だな」と気づく類のやつ。前もって全部予測するのは難しい。

---

## 結論

「修正しました、ご確認ください」とだけ書いてあるメール。何が変わったのか分からない。だから目視で全部見ないといけなかった。

でも部品数が100を超えると、もう無理。

体積変化率で絞り込めば、確認対象を数分の1に減らせる。30分かかってた確認が、5分で終わることもある。テーブルに出た部品だけ確認する使い方。

ただし「自動検出は補助。最終判断は目視」というスタンス。完璧な自動化を目指さない方が実務的だと思う。

もし「修正内容がどこにあるのか」を瞬時に把握したい設計者なら、試してみるといいかもしれません。[ドコカワのWeb版](https://fabgear-jp.github.io/docokawa/?utm_source=zenn7)で試せます。

---

## 参考

- **CadQuery**: STEP/IGES読み込み、形状解析
- **pandas**: テーブル操作・フィルタリング
- **ドコカワ**: 本記事で紹介したSTEP差分検出の実装例
