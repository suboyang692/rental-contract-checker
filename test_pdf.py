"""批量测试 samples 下的所有 PDF，确认都能提取出文本"""
import glob
import os

from app.pdf_parser import extract_summary

paths = sorted(glob.glob("samples/*.pdf"))
if not paths:
    print("samples 目录下没有 PDF，先放 3 份测试合同进来")
else:
    for path in paths:
        info = extract_summary(path)
        preview = info["preview"].replace("\n", " ")
        print(f"{os.path.basename(path)}: {info['pages']} 页, {info['chars']} 字")
        print(f"  预览: {preview[:80]}")
        print()