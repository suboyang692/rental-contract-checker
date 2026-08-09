"""D4 验证：用大模型抽取两份陷阱合同的关键条款"""
import json

from app.pdf_parser import extract_text
from app.llm_extract import extract_clauses

for name in ["test2.pdf", "test3.pdf"]:
    print("=" * 60)
    print(name)
    text = extract_text(f"samples/{name}")
    print("  正在调用大模型抽取条款（约 10~20 秒）…")
    result = extract_clauses(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()