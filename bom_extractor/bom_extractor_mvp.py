"""
BOM自動抽出MVP - STEPファイルからアセンブリ構造・部品名・数量を抽出

CadQueryベースの実装版
既存のstep_parser.pyの機能を活用してBOMを生成する

制約:
- CadQueryは階層構造を保持しないため、フラットな部品リストを取得
- 部品名の重複カウントで数量を算出
- PRODUCT名をSTEPファイルから正規表現で抽出

将来の改善:
- pythonocc-core直接使用でXCAF階層構造対応
- 親子関係の保持
"""
import sys
import csv
import io

# Windowsコンソールでの文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from collections import Counter
from typing import List, Dict

# 既存のstep_parser.pyをインポート
sys.path.insert(0, str(Path(__file__).parent.parent / "projects" / "spec-checker" / "src"))

try:
    from step_parser import parse_assembly, extract_product_names
    HAS_STEP_PARSER = True
except ImportError:
    HAS_STEP_PARSER = False
    print("Error: step_parser.py not found")
    print("Expected location: projects/spec-checker/src/step_parser.py")
    sys.exit(1)


def extract_bom_from_step(step_file: Path) -> Dict[str, any]:
    """
    STEPファイルからBOMを抽出する

    Args:
        step_file: STEPファイルのパス

    Returns:
        dict: 抽出結果（成功フラグ、BOMリスト、エラーメッセージ）
    """
    if not step_file.exists():
        return {
            "success": False,
            "error": f"File not found: {step_file}",
            "bom": [],
            "total_parts": 0,
            "unique_parts": 0
        }

    # 既存のparse_assembly()を使用
    result = parse_assembly(step_file)

    if not result.success:
        return {
            "success": False,
            "error": result.error_message,
            "bom": [],
            "total_parts": 0,
            "unique_parts": 0
        }

    # 部品名から数量を集計
    part_names = [part.name for part in result.parts]
    part_counter = Counter(part_names)

    # BOMリストを作成
    bom_list = []
    seen_parts = set()

    for i, part in enumerate(result.parts):
        if part.name not in seen_parts:
            # 同名部品の最初の出現のみBOMに追加
            bom_list.append({
                "part_name": part.name,
                "quantity": part_counter[part.name],
                "width": part.width,
                "depth": part.depth,
                "height": part.height,
                "volume": part.volume,
                "num_faces": part.num_faces,
                "num_edges": part.num_edges,
                "index": part.index
            })
            seen_parts.add(part.name)

    # 名前順にソート
    bom_list.sort(key=lambda x: x["part_name"])

    return {
        "success": True,
        "error": None,
        "bom": bom_list,
        "total_parts": result.num_parts,
        "unique_parts": len(bom_list),
        "assembly_info": {
            "width": result.total_width,
            "depth": result.total_depth,
            "height": result.total_height,
            "volume": result.total_volume
        }
    }


def print_bom(result: Dict[str, any], show_details: bool = False):
    """BOMをコンソールに出力"""
    if not result["success"]:
        print(f"ERROR: {result['error']}")
        return

    print("\n" + "="*80)
    print("BOM (Bill of Materials)")
    print("="*80)

    # アセンブリ情報
    asm = result["assembly_info"]
    print(f"\n【Assembly Information】")
    print(f"  Total parts:  {result['total_parts']}")
    print(f"  Unique parts: {result['unique_parts']}")
    print(f"  Overall size: {asm['width']:.1f} x {asm['depth']:.1f} x {asm['height']:.1f} mm")
    if asm['volume']:
        print(f"  Total volume: {asm['volume']:.1f} mm^3")

    # BOMテーブル
    print(f"\n【Parts List】")
    if show_details:
        print(f"{'No.':<5} {'Part Name':<35} {'Qty':<6} {'Dimensions (W x D x H)':<30} {'Volume':<12}")
        print("-"*80)
        for i, item in enumerate(result["bom"], 1):
            dims = f"{item['width']:.1f} x {item['depth']:.1f} x {item['height']:.1f}"
            vol = f"{item['volume']:.1f}" if item['volume'] > 0 else "-"
            print(f"{i:<5} {item['part_name']:<35} {item['quantity']:<6} {dims:<30} {vol:<12}")
    else:
        print(f"{'No.':<5} {'Part Name':<50} {'Quantity':<10}")
        print("-"*80)
        for i, item in enumerate(result["bom"], 1):
            print(f"{i:<5} {item['part_name']:<50} {item['quantity']:<10}")

    print("="*80 + "\n")


def export_csv(result: Dict[str, any], output_path: Path):
    """BOMをCSVに出力"""
    if not result["success"]:
        print(f"Cannot export CSV: {result['error']}")
        return

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        # ヘッダー
        writer.writerow([
            "No.",
            "Part Name",
            "Quantity",
            "Width (mm)",
            "Depth (mm)",
            "Height (mm)",
            "Volume (mm^3)",
            "Faces",
            "Edges"
        ])

        # BOMデータ
        for i, item in enumerate(result["bom"], 1):
            writer.writerow([
                i,
                item["part_name"],
                item["quantity"],
                f"{item['width']:.2f}",
                f"{item['depth']:.2f}",
                f"{item['height']:.2f}",
                f"{item['volume']:.2f}",
                item["num_faces"],
                item["num_edges"]
            ])

    print(f"BOM exported to: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python bom_extractor_mvp.py <step_file> [options]")
        print("\nOptions:")
        print("  --csv <output.csv>  Export BOM to CSV file")
        print("  --details           Show detailed dimensions in console output")
        print("\nExamples:")
        print("  python bom_extractor_mvp.py assembly.step")
        print("  python bom_extractor_mvp.py assembly.step --details")
        print("  python bom_extractor_mvp.py assembly.step --csv bom.csv")
        sys.exit(1)

    step_file = Path(sys.argv[1])

    # オプション解析
    csv_output = None
    show_details = "--details" in sys.argv

    if "--csv" in sys.argv:
        csv_idx = sys.argv.index("--csv")
        if csv_idx + 1 < len(sys.argv):
            csv_output = Path(sys.argv[csv_idx + 1])

    print(f"Reading STEP file: {step_file}")

    # BOM抽出
    result = extract_bom_from_step(step_file)

    # コンソール出力
    print_bom(result, show_details=show_details)

    # CSV出力
    if csv_output and result["success"]:
        export_csv(result, csv_output)

    # 終了コード
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
