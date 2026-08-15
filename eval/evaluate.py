"""评测脚本：标注集（条款级） vs 规则命中 → 精确率 / 召回率（纯规则，不调 LLM）

用法：python eval/evaluate.py
说明：标注集 = 3+ 份样本合同人工整理的"预期命中条款"，用于回归验证规则引擎。
匹配方式：同规则 id 且标注关键词出现在命中原文里（关键词是条款定位锚点）。
"""
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # 兼容 Windows GBK 控制台（⚠️ 打印会触发 UnicodeEncodeError）

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # 让 app 包可导入

from app.pdf_parser import extract_text
from app.rules import check_rules

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"
ANNOTATIONS_FILE = Path(__file__).resolve().parent / "annotations.json"


def load_annotations() -> dict[str, list[dict]]:
    return json.loads(ANNOTATIONS_FILE.read_text(encoding="utf-8"))


def evaluate_file(file_name: str, annotations: list[dict]) -> dict:
    """跑规则，与标注集对比，算 TP/FP/FN 和精确率/召回率"""
    text = extract_text(SAMPLES_DIR / file_name)
    findings = check_rules(text)

    # 每个发现最多匹配一个标注（同规则 id 且关键词出现在命中原文里）
    matched_ids = set()
    matched_anns = set()
    tp = 0
    for ann_idx, ann in enumerate(annotations):
        for f_idx, f in enumerate(findings):
            if f_idx in matched_ids:
                continue
            if f["rule_id"] == ann["rule_id"] and ann["keyword"] in f["matched"]:
                matched_ids.add(f_idx)
                matched_anns.add(ann_idx)
                tp += 1
                break

    fp = len(findings) - tp
    fn = len(annotations) - tp
    precision = tp / len(findings) if findings else None
    recall = tp / len(annotations) if annotations else (1.0 if not findings else 0.0)

    return {
        "file_name": file_name,
        "expected": len(annotations),
        "predicted": len(findings),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "unmatched_predictions": [f for i, f in enumerate(findings) if i not in matched_ids],
        "missed_annotations": [a for i, a in enumerate(annotations) if i not in matched_anns],
    }


def main() -> None:
    annotations = load_annotations()
    print(f"标注集: {ANNOTATIONS_FILE}")
    print(f"{'文件':<12}{'预期':>5}{'命中':>5}{'TP':>5}{'FP':>5}{'FN':>5}{'精确率':>8}{'召回率':>8}")
    total_tp = total_pred = total_exp = 0
    for file_name, anns in sorted(annotations.items()):
        if not (SAMPLES_DIR / file_name).exists():
            print(f"跳过（样本缺失）: {file_name}")
            continue
        r = evaluate_file(file_name, anns)
        total_tp += r["tp"]
        total_pred += r["predicted"]
        total_exp += r["expected"]
        p = f"{r['precision']:.2f}" if r["precision"] is not None else "  N/A"
        rec = f"{r['recall']:.2f}" if r["recall"] is not None else "  N/A"
        print(f"{r['file_name']:<12}{r['expected']:>5}{r['predicted']:>5}{r['tp']:>5}{r['fp']:>5}{r['fn']:>5}{p:>8}{rec:>8}")
        for f in r["unmatched_predictions"]:
            print(f"    ⚠️ 规则误报: [{f['rule_id']}] {f['matched'][:50]}")
        for a in r["missed_annotations"]:
            print(f"    ⚠️ 规则漏报: [{a['rule_id']}] {a['clause']}")
    print("-" * 62)
    print(f"{'合计':<12}{total_exp:>5}{total_pred:>5}{total_tp:>5}{total_pred-total_tp:>5}{total_exp-total_tp:>5}"
          f"{(total_tp/total_pred if total_pred else 0):>8.2f}{(total_tp/total_exp if total_exp else 0):>8.2f}")


if __name__ == "__main__":
    main()