"""D4 验证：用大模型抽取样本合同的陷阱条款（需要 API Key + 网络）"""
import glob
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # 兼容 Windows GBK 控制台（✓/✅ 打印会触发 UnicodeEncodeError）


from app.pdf_parser import extract_text
from app.llm_extract import extract_clauses

for name in sorted(glob.glob("samples/*.pdf")):
    print("=" * 60)
    print(name)
    text = extract_text(f"samples/{name}")
    print("  正在调用大模型抽取条款（约 10~20 秒）…")
    result = extract_clauses(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()