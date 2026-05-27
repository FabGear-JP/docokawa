"""
BOM自動抽出ツール - Streamlitデモアプリ

STEPファイルをアップロードして、ブラウザ上でBOMを確認できるWebアプリ
"""
import sys
import io
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

# Windowsコンソールでの文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# bom_extractor_mvpをインポート
sys.path.insert(0, str(Path(__file__).parent))
from bom_extractor_mvp import extract_bom_from_step

# ページ設定
st.set_page_config(
    page_title="BOM自動抽出ツール",
    page_icon="📋",
    layout="wide"
)

# タイトル
st.title("📋 BOM自動抽出ツール（MVP版）")
st.markdown("STEPファイルから部品表（BOM）を自動生成します")

# ⚠️ 数量精度の警告（メイン画面に赤字で表示）
st.markdown("""
<div style='background-color: #ffebee; padding: 12px; border-radius: 8px; border-left: 4px solid #f44336; margin: 16px 0;'>
    <span style='color: #c62828; font-weight: bold;'>⚠️ 数量は参考値です。発注には使えません。</span><br>
    <span style='color: #666; font-size: 0.9em;'>MVP版のため、すべての部品が「1個」として表示されます。部品リストの確認用途にご利用ください。</span>
</div>
""", unsafe_allow_html=True)

# サイドバー: 説明
with st.sidebar:
    st.header("使い方")
    st.markdown("""
    1. STEPファイル（.step/.stp）をアップロード
    2. 自動的にBOMを抽出
    3. 部品リストを確認
    4. CSV出力も可能
    """)

    st.header("⚠️ 制約事項")
    st.warning("""
    **数量が正確ではありません**

    現在のMVP版は階層構造を保持できないため、すべての部品が「1個」として表示されます。

    - ✅ 部品リスト確認
    - ✅ 設計レビュー
    - ❌ 発注用BOM（数量不正確）
    """)

# ファイルアップロード
uploaded_file = st.file_uploader(
    "STEPファイルを選択してください",
    type=["step", "stp"],
    help="アセンブリのSTEPファイルをドラッグ&ドロップしてください"
)

if uploaded_file is not None:
    # 一時ファイルとして保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".step") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = Path(tmp_file.name)

    # ファイル情報
    st.info(f"📂 ファイル名: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

    # BOM抽出
    with st.spinner("BOMを抽出中..."):
        result = extract_bom_from_step(tmp_path)

    # 一時ファイル削除
    tmp_path.unlink()

    if result["success"]:
        # 成功時の表示
        st.success("✅ BOM抽出完了")

        # アセンブリ情報
        st.subheader("📦 アセンブリ情報")
        asm = result["assembly_info"]
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("総部品数", result["total_parts"])
        with col2:
            st.metric("ユニーク部品", result["unique_parts"])
        with col3:
            st.metric("サイズ (mm)", f"{asm['width']:.1f} × {asm['depth']:.1f} × {asm['height']:.1f}")
        with col4:
            if asm['volume'] > 0:
                st.metric("総体積 (mm³)", f"{asm['volume']:.1f}")
            else:
                st.metric("総体積", "N/A")

        # 部品リスト
        st.subheader("📋 部品リスト（BOM）")

        # DataFrameに変換
        bom_data = []
        for i, item in enumerate(result["bom"], 1):
            bom_data.append({
                "No.": i,
                "部品名": item["part_name"],
                "数量": item["quantity"],
                "幅 (mm)": f"{item['width']:.2f}",
                "奥行 (mm)": f"{item['depth']:.2f}",
                "高さ (mm)": f"{item['height']:.2f}",
                "体積 (mm³)": f"{item['volume']:.2f}" if item['volume'] > 0 else "-",
                "面数": item["num_faces"],
                "エッジ数": item["num_edges"]
            })

        df = pd.DataFrame(bom_data)

        # テーブル表示
        st.dataframe(df, use_container_width=True, height=400)

        # CSV出力
        st.subheader("💾 CSV出力")
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"{uploaded_file.name.replace('.step', '').replace('.stp', '')}_BOM.csv",
            mime="text/csv"
        )

        # 詳細統計
        with st.expander("📊 詳細統計"):
            st.markdown("### 部品名の内訳")

            # 部品名の長さ分布
            name_lengths = [len(item["part_name"]) for item in result["bom"]]
            st.markdown(f"- 最短部品名: {min(name_lengths)}文字")
            st.markdown(f"- 最長部品名: {max(name_lengths)}文字")
            st.markdown(f"- 平均文字数: {sum(name_lengths) / len(name_lengths):.1f}文字")

            # 標準部品の検出
            standard_parts = [item for item in result["bom"] if any(
                keyword in item["part_name"].upper()
                for keyword in ["M3", "M2", "DIN", "ISO", "BEARING", "SCREW", "NUT", "BOLT"]
            )]
            if standard_parts:
                st.markdown(f"- 標準部品（推定）: {len(standard_parts)}個")

            # 無名部品の検出
            unnamed_parts = [item for item in result["bom"] if "Part_" in item["part_name"]]
            if unnamed_parts:
                st.warning(f"⚠️ 無名部品（Part_XXX）: {len(unnamed_parts)}個")

    else:
        # エラー時の表示
        st.error(f"❌ BOM抽出に失敗しました: {result['error']}")
        st.info("""
        **トラブルシューティング**:
        - STEPファイルが破損していないか確認してください
        - アセンブリ（組立品）のファイルかどうか確認してください
        - ファイルサイズが大きすぎる場合は処理に時間がかかる可能性があります
        """)

else:
    # ファイル未アップロード時の説明
    st.info("👆 STEPファイルをアップロードしてください")

    st.markdown("""
    ### このツールでできること

    - ✅ STEPファイルから部品名を自動抽出
    - ✅ 部品ごとのサイズ（W×D×H）・体積を計算
    - ✅ アセンブリ全体の寸法・体積を算出
    - ✅ 標準部品（ネジ・ベアリング等）の型番を認識
    - ✅ 多言語対応（日本語・中国語等）
    - ✅ CSV出力で表計算ソフトに取り込み可能

    ### テスト済みのファイル

    以下のようなオープンソースCADデータで検証済みです:
    - Voron Stealthburner（3Dプリンタヘッド、198部品）
    - Dobot ロボットアーム（212部品、中国語対応）
    """)

    # サンプル画像があれば表示（オプション）
    # st.image("sample_bom.png", caption="BOM抽出例")

# フッター
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>開発: <a href='https://github.com/FabGear-JP'>FabGear</a> |
    関連ツール: <a href='https://github.com/FabGear-JP/docokawa'>ドコカワ（STEP差分比較）</a></p>
</div>
""", unsafe_allow_html=True)
