"""FastAPI 入口（D6+ 版：PDF 上传 + Web 界面 + 分析历史）"""

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import history
from .llm_extract import extract_clauses
from .pdf_parser import extract_text
from .report import generate_report
from .rules import check_rules

app = FastAPI(title="租房合同风险审查助手")

# 静态资源目录（index.html），不存在就自动创建
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def root():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "租房合同风险审查助手 API 已启动，请先复制 static/index.html"}


@app.get("/health")
def health():
    return {"status": "ok"}


class AnalyzeRequest(BaseModel):
    text: str  # 直接传合同文本（测试用）


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    findings = check_rules(req.text)
    try:
        extracted = extract_clauses(req.text)  # LLM 抽取，约 10~20 秒
    except Exception as exc:
        extracted = None
        print(f"[analyze] LLM 抽取失败: {exc}")
    report = generate_report(findings, extracted)
    try:
        history.save_analysis("文本直传", findings, extracted, report)
    except Exception as exc:
        print(f"[analyze] 历史记录保存失败: {exc}")
    return {
        "status": "ok",
        "finding_count": len(findings),
        "findings": findings,
        "extracted": extracted,
        "report": report,
    }


@app.post("/analyze_pdf")
def analyze_pdf(file: UploadFile = File(...)):
    """上传 PDF → 提取文本 → 规则 + LLM → 风险报告"""
    suffix = Path(file.filename or "contract.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        text = extract_text(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    if not text.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": "PDF 未能提取出文字（可能是扫描件，暂不支持 OCR）"},
        )
    findings = check_rules(text)
    try:
        extracted = extract_clauses(text)
    except Exception as exc:
        extracted = None
        print(f"[analyze_pdf] LLM 抽取失败: {exc}")
    report = generate_report(findings, extracted)
    try:
        history.save_analysis(file.filename or "未命名.pdf", findings, extracted, report)
    except Exception as exc:
        print(f"[analyze_pdf] 历史记录保存失败: {exc}")
    return {
        "status": "ok",
        "file_name": file.filename,
        "finding_count": len(findings),
        "findings": findings,
        "extracted": extracted,
        "report": report,
        "text_preview": text[:150],
    }


@app.get("/history")
def get_history():
    """最近分析记录列表"""
    return {"status": "ok", "items": history.list_history(20)}


@app.get("/history/{aid}")
def get_history_item(aid: int):
    """单条分析记录完整内容（可复用前端 render）"""
    item = history.get_analysis(aid)
    if not item:
        return JSONResponse(status_code=404, content={"status": "error", "detail": "记录不存在"})
    return {"status": "ok", **item}