"""PDF 文本提取（D2 版：多页、空页过滤、页标记、文本归一化）"""

import logging
import re
import unicodedata

import pdfplumber

# 豆包等生成的 PDF 字体元数据不规范，pdfminer 会刷大量 FontBBox 警告，压掉
logging.getLogger("pdfminer").setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.ERROR)

# NFKC 管不了的部首补充区字符（U+2E80-U+2EFF 没有兼容分解），按样本手动补映射
_RADICAL_SUPPLEMENT_MAP = {
    "\u2EA0": "民",  # ⺠ CJK RADICAL CIVILIAN
    "\u2ED3": "长",  # ⻓ CJK RADICAL C-SIMPLIFIED LONG
    "\u2ED4": "门",  # ⻔ CJK RADICAL C-SIMPLIFIED GATE
    "\u6236": "户",  # ⼾ 经 NFKC 后会变成繁体「戶」，中文合同统一用简体
}


def normalize_text(text: str) -> str:
    """文本归一化：NFKC + 部首补充区手动映射，保证关键词匹配不漏字"""
    text = unicodedata.normalize("NFKC", text)
    for old, new in _RADICAL_SUPPLEMENT_MAP.items():
        text = text.replace(old, new)
    return text


def extract_text(pdf_path: str) -> str:
    """提取 PDF 全文：带页码标记 + 文本归一化 + 去空白（否则正则跨行匹配会失效）"""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"【第{page_idx + 1}页】\n{page_text.strip()}")
    full = normalize_text("\n\n".join(text_parts))
    return re.sub(r"\s+", "", full)


def extract_summary(pdf_path: str) -> dict:
    """批量测试用：返回页数、总字数、前 200 字预览"""
    full = extract_text(pdf_path)
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
    return {
        "pages": page_count,
        "chars": len(full),
        "preview": full[:200],
    }