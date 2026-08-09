"""D3 验证脚本：跑全部样本合同，看规则命中情况"""
import glob
import os

from app.pdf_parser import extract_text
from app.rules import check_rules

for path in sorted(glob.glob("samples/*.pdf")):
    print("=" * 60)
    print(os.path.basename(path))
    findings = check_rules(extract_text(path))
    if not findings:
        print("  未命中风险条款 ✓")
    for f in findings:
        print(f"  [{f['severity']}] {f['rule_name']}")
        print(f"    命中: {f['matched'][:70]}")
    print()