"""
BOM自動抽出ツール - スタンドアロン版

STEPファイルからアセンブリ構造・部品名・数量を抽出する。
step_parser.pyへの依存を解消した独立版。

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
import re
from pathlib import Path
from collections import Counter
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# Windowsコンソールでの文字化け対策
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import cadquery as cq
    HAS_CADQUERY = True
except ImportError:
    HAS_CADQUERY = False
    print("Error: cadquery not installed")
    print("Please install: pip install cadquery")
    sys.exit(1)


@dataclass
class PartInfo:
    """部品情報"""
    index: int
    name: str
    width: float
    depth: float
    height: float
    volume: float
    center: Tuple[float, float, float]
    num_faces: int = 0
    num_edges: int = 0


@dataclass
class AssemblyParserResult:
    """アセンブリ解析結果"""
    success: bool
    # 全体情報
    total_width: Optional[float] = None
    total_depth: Optional[float] = None
    total_height: Optional[float] = None
    total_volume: Optional[float] = None
    num_parts: int = 0
    # 形状情報（全体）
    total_faces: int = 0
    total_edges: int = 0
    total_vertices: int = 0
    # 部品一覧
    parts: List[PartInfo] = None
    # エラー情報
    error_message: Optional[str] = None

    def __post_init__(self):
        if self.parts is None:
            self.parts = []


def extract_product_names(step_path: Path) -> List[str]:
    """
    STEPファイルからPRODUCT名を抽出する。
    PRODUCT ( 'name', 'description', ... ) の最初の引数を取得。
    UUID形式のルートアセンブリ名は除外する。
    """
    if not step_path.exists():
        return []
    try:
        with open(step_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return []
    pattern = r"PRODUCT\s*\(\s*'([^']+)'"
    names = re.findall(pattern, content)
    # UUIDっぽい名前（ルートアセンブリ）は除外
    return [
        n for n in names
        if not (len(n) == 36 and n.count("-") == 4)
    ]


def parse_assembly(file_path: Path) -> AssemblyParserResult:
    """
    アセンブリSTEPファイルを解析

    アセンブリ内の全ソリッドを列挙し、各部品の寸法・体積・位置を取得する。
    単一部品のSTEPファイルでも使用可能（部品数=1として返す）。

    Args:
        file_path: STEPファイルのパス

    Returns:
        AssemblyParserResult: アセンブリ解析結果（全体情報 + 部品一覧）
    """
    if not HAS_CADQUERY:
        return AssemblyParserResult(
            success=False,
            error_message="cadquery がインストールされていません"
        )
    if not file_path.exists():
        return AssemblyParserResult(
            success=False,
            error_message=f"ファイルが見つかりません: {file_path}"
        )
    if file_path.suffix.lower() not in (".step", ".stp"):
        return AssemblyParserResult(
            success=False,
            error_message=f"STEPファイルではありません: {file_path.suffix}"
        )

    try:
        result = cq.importers.importStep(str(file_path))

        if hasattr(result, 'val'):
            shape = result.val()
        else:
            shape = result

        # 全体のバウンディングボックス
        bb = shape.BoundingBox()

        # 全体の形状情報
        total_faces = len(shape.Faces())
        total_edges = len(shape.Edges())
        total_vertices = len(shape.Vertices())
        total_volume = shape.Volume() if hasattr(shape, 'Volume') else None

        # 部品名を取得（PRODUCT行から）
        product_names = extract_product_names(file_path)

        # ソリッドを列挙
        parts = []
        if hasattr(shape, 'Solids'):
            solids = shape.Solids()
        else:
            solids = [shape]

        for i, solid in enumerate(solids):
            solid_bb = solid.BoundingBox()
            center = solid.Center()
            vol = solid.Volume() if hasattr(solid, 'Volume') else 0

            if i < len(product_names):
                name = product_names[i]
            else:
                name = f"Part_{i + 1:03d}"

            parts.append(PartInfo(
                index=i + 1,
                name=name,
                width=solid_bb.xlen,
                depth=solid_bb.ylen,
                height=solid_bb.zlen,
                volume=vol,
                center=(center.x, center.y, center.z),
                num_faces=len(solid.Faces()) if hasattr(solid, 'Faces') else 0,
                num_edges=len(solid.Edges()) if hasattr(solid, 'Edges') else 0,
            ))

        return AssemblyParserResult(
            success=True,
            total_width=bb.xlen,
            total_depth=bb.ylen,
            total_height=bb.zlen,
            total_volume=total_volume,
            num_parts=len(solids),
            total_faces=total_faces,
            total_edges=total_edges,
            total_vertices=total_vertices,
            parts=parts,
        )

    except Exception as e:
        return AssemblyParserResult(
            success=False,
            error_message=f"解析エラー: {str(e)}"
        )


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

    # parse_assembly()を使用
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
        print("Usage: python bom_extractor_standalone.py <step_file> [options]")
        print("\nOptions:")
        print("  --csv <output.csv>  Export BOM to CSV file")
        print("  --details           Show detailed dimensions in console output")
        print("\nExamples:")
        print("  python bom_extractor_standalone.py assembly.step")
        print("  python bom_extractor_standalone.py assembly.step --details")
        print("  python bom_extractor_standalone.py assembly.step --csv bom.csv")
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
