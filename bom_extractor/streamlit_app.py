"""
BOM自動抽出ツール - Streamlitデモアプリ（簡易版）

STEPファイルをアップロードして、部品リストを確認できるWebアプリ
※ 簡易版のため、テキスト解析による部品名抽出のみ対応
"""
import re
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(
    page_title="部品リスト抽出ツール",
    page_icon="📋",
    layout="wide"
)

# タイトル
st.title("📋 部品リスト抽出ツール")
st.markdown("STEPファイルから部品名を自動抽出します")

# ⚠️ 簡易版の案内
st.markdown("""
<div style='background-color: #fff3e0; padding: 12px; border-radius: 8px; border-left: 4px solid #ff9800; margin: 16px 0;'>
    <span style='color: #e65100; font-weight: bold;'>ℹ️ これはWeb簡易版です</span><br>
    <span style='color: #666; font-size: 0.9em;'>
        部品名の抽出のみ対応。寸法・体積の計算が必要な場合は
        <a href='https://github.com/FabGear-JP/docokawa/tree/main/bom_extractor'>ローカル版</a>
        をご利用ください。
    </span>
</div>
""", unsafe_allow_html=True)

# ⚠️ 数量精度の警告
st.markdown("""
<div style='background-color: #ffebee; padding: 12px; border-radius: 8px; border-left: 4px solid #f44336; margin: 16px 0;'>
    <span style='color: #c62828; font-weight: bold;'>⚠️ 数量は参考値です。発注には使えません。</span><br>
    <span style='color: #666; font-size: 0.9em;'>同名部品をカウントして数量を推定しています。正確な数量が必要な場合はローカル版をお使いください。</span>
</div>
""", unsafe_allow_html=True)


def extract_parts_from_step_text(step_content: str) -> list[dict]:
    """
    STEPファイルのテキストから部品名を抽出（簡易版）

    PRODUCT エントリから部品名を取得
    形式: PRODUCT('部品名', '説明', '', ...)
    """
    parts = []

    # PRODUCT エントリを検索
    # 例: #123 = PRODUCT('Part_001', 'Description', '', (#456));
    product_pattern = r"PRODUCT\s*\(\s*'([^']*)'(?:\s*,\s*'([^']*)')?"

    matches = re.findall(product_pattern, step_content, re.IGNORECASE)

    for match in matches:
        part_name = match[0].strip() if match[0] else "Unknown"
        description = match[1].strip() if len(match) > 1 and match[1] else ""

        # 空の名前やシステム名をスキップ
        if not part_name or part_name.upper() in ['', 'NONE', 'UNKNOWN']:
            continue

        parts.append({
            "part_name": part_name,
            "description": description
        })

    return parts


def count_parts(parts: list[dict]) -> list[dict]:
    """同名部品をカウントして数量を推定"""
    from collections import Counter

    name_counts = Counter(p["part_name"] for p in parts)

    # 重複を除去して数量を追加
    seen = set()
    result = []
    for p in parts:
        name = p["part_name"]
        if name not in seen:
            seen.add(name)
            result.append({
                "part_name": name,
                "description": p.get("description", ""),
                "quantity": name_counts[name]
            })

    return result


# サイドバー: 説明
with st.sidebar:
    st.header("使い方")
    st.markdown("""
    1. STEPファイル（.step/.stp）をアップロード
    2. 自動的に部品名を抽出
    3. 部品リストを確認
    """)

    st.header("簡易版の制限")
    st.warning("""
    **Web簡易版では以下の機能は使えません**

    - ❌ 寸法（幅×奥行×高さ）
    - ❌ 体積計算
    - ❌ 面数・エッジ数

    上記が必要な場合は[ローカル版](https://github.com/FabGear-JP/docokawa/tree/main/bom_extractor)をお使いください。
    """)

    st.header("ローカル版の導入")
    st.code("""
pip install cadquery pandas
python bom_extractor.py your.step
    """, language="bash")


# ファイルアップロード
uploaded_file = st.file_uploader(
    "STEPファイルを選択してください",
    type=["step", "stp"],
    help="アセンブリのSTEPファイルをドラッグ&ドロップしてください"
)

if uploaded_file is not None:
    # ファイル情報
    file_size_kb = uploaded_file.size / 1024
    st.info(f"📂 ファイル名: {uploaded_file.name} ({file_size_kb:.1f} KB)")

    # ファイル内容を読み込み
    try:
        content = uploaded_file.read().decode('utf-8', errors='replace')
    except Exception as e:
        st.error(f"ファイルの読み込みに失敗しました: {e}")
        st.stop()

    # 部品抽出
    with st.spinner("部品リストを抽出中..."):
        raw_parts = extract_parts_from_step_text(content)
        parts = count_parts(raw_parts)

    if parts:
        st.success(f"✅ {len(parts)}種類の部品を検出しました（総数: {len(raw_parts)}個）")

        # 部品リスト
        st.subheader("📋 部品リスト")

        # DataFrameに変換
        df = pd.DataFrame([
            {
                "No.": i + 1,
                "部品名": p["part_name"],
                "数量": p["quantity"],
                "説明": p.get("description", "-")
            }
            for i, p in enumerate(parts)
        ])

        # テーブル表示
        st.dataframe(df, use_container_width=True, height=400)

        # 統計
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("ユニーク部品数", len(parts))
        with col2:
            st.metric("総部品数", len(raw_parts))
        with col3:
            multi_parts = len([p for p in parts if p["quantity"] > 1])
            st.metric("複数使用部品", multi_parts)

        # CSV出力
        st.subheader("💾 CSV出力")
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"{uploaded_file.name.replace('.step', '').replace('.stp', '')}_parts.csv",
            mime="text/csv"
        )

        # 標準部品の検出
        with st.expander("📊 詳細分析"):
            # 標準部品
            standard_keywords = ["M2", "M3", "M4", "M5", "M6", "M8", "M10",
                               "DIN", "ISO", "JIS", "BEARING", "SCREW", "NUT", "BOLT",
                               "ベアリング", "ネジ", "ボルト", "ナット", "ワッシャ"]
            standard_parts = [p for p in parts if any(
                kw.upper() in p["part_name"].upper() for kw in standard_keywords
            )]
            if standard_parts:
                st.markdown(f"**標準部品（推定）**: {len(standard_parts)}種類")
                for p in standard_parts[:10]:
                    st.markdown(f"- {p['part_name']} ×{p['quantity']}")
                if len(standard_parts) > 10:
                    st.markdown(f"...他 {len(standard_parts) - 10}種類")

            # 無名部品
            unnamed = [p for p in parts if "Part_" in p["part_name"] or p["part_name"].startswith("unnamed")]
            if unnamed:
                st.warning(f"⚠️ 無名部品（Part_XXX等）: {len(unnamed)}種類")

    else:
        st.warning("⚠️ 部品が検出できませんでした")
        st.info("""
        **考えられる原因**:
        - 単一部品のSTEPファイル（アセンブリではない）
        - 非標準のSTEP形式
        - ファイルの破損

        ローカル版なら解析できる可能性があります。
        """)

else:
    # ファイル未アップロード時
    st.info("👆 STEPファイルをアップロードしてください")

    st.markdown("""
    ### このツールでできること

    - ✅ STEPファイルから部品名を自動抽出
    - ✅ 同名部品のカウント（数量推定）
    - ✅ 標準部品（ネジ・ベアリング等）の検出
    - ✅ CSV出力

    ### ローカル版ならさらに

    - ✅ 部品ごとの寸法（幅×奥行×高さ）
    - ✅ 体積計算
    - ✅ より正確な解析

    👉 [ローカル版のダウンロード](https://github.com/FabGear-JP/docokawa/tree/main/bom_extractor)
    """)


# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p><a href='https://fabgear-jp.github.io/docokawa/'>ドコカワ LP</a> |
    <a href='https://fabgear-jp.github.io/'>FabGear</a> |
    <a href='https://github.com/FabGear-JP/docokawa'>GitHub</a></p>
</div>
""", unsafe_allow_html=True)
