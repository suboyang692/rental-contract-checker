"""分析历史（SQLite 存储）：每次分析结果落库，可回溯"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

# 数据库放在项目根目录 data/ 下（已加入 .gitignore）
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "history.db"


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT,
            finding_count INTEGER,
            high_count INTEGER,
            medium_count INTEGER,
            findings TEXT,
            extracted TEXT,
            report TEXT,
            created_at TEXT
        )
        """
    )
    return conn


def save_analysis(file_name: str, findings: list[dict], extracted: dict | None, report: str) -> int:
    """保存一次分析记录，返回记录 id"""
    high = sum(1 for f in findings if f["severity"] == "高")
    medium = sum(1 for f in findings if f["severity"] == "中")
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO analyses
           (file_name, finding_count, high_count, medium_count, findings, extracted, report, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            file_name,
            len(findings),
            high,
            medium,
            json.dumps(findings, ensure_ascii=False),
            json.dumps(extracted, ensure_ascii=False) if extracted else None,
            report,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return aid


def list_history(limit: int = 20) -> list[dict]:
    """最近 N 条记录（不含大字段，列表用）"""
    conn = _connect()
    rows = conn.execute(
        """SELECT id, file_name, finding_count, high_count, medium_count, created_at
           FROM analyses ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_analysis(aid: int) -> dict | None:
    """按 id 取完整记录（findings/extracted 反序列化）"""
    conn = _connect()
    row = conn.execute("SELECT * FROM analyses WHERE id = ?", (aid,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["findings"] = json.loads(d["findings"])
    d["extracted"] = json.loads(d["extracted"]) if d["extracted"] else None
    return d