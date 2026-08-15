"""D3 验证脚本：跑全部样本合同，看规则命中情况"""
import glob
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # 兼容 Windows GBK 控制台（✓/✅ 打印会触发 UnicodeEncodeError）


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