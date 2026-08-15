"""D5 验证：完整流程 PDF → 规则 + LLM → Markdown 报告（需要 API Key + 网络）"""
import glob
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # 兼容 Windows GBK 控制台（✓/✅ 打印会触发 UnicodeEncodeError）


from app.llm_extract import extract_clauses
from app.pdf_parser import extract_text
from app.report import generate_report
from app.rules import check_rules

os.makedirs("reports", exist_ok=True)

for name in sorted(glob.glob("samples/*.pdf")):
    print("=" * 60)
    print(name)
    text = extract_text(f"samples/{name}")
    findings = check_rules(text)
    print(f"  规则命中 {len(findings)} 处，正在调用 LLM 抽取…（约 10~20 秒）")
    extracted = extract_clauses(text)
    report = generate_report(findings, extracted)
    out_path = f"reports/{name.replace('.pdf', '')}_报告.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(report)
    print(f"  ✅ 报告已保存: {out_path}")
    print()