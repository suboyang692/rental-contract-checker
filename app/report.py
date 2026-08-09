"""报告生成（D5 版）：规则命中 + LLM 抽取 → Markdown 风险报告"""

from datetime import datetime

# LLM 抽取字段 → 中文标签（报告里展示用）
_FIELD_LABELS = {
    "rent_amount": "每月租金",
    "deposit_amount": "押金金额",
    "lease_term": "租期",
    "payment_method": "支付方式",
    "penalty_clause": "违约金条款",
    "repair_responsibility": "维修责任",
    "sublease_clause": "转租条款",
    "early_termination": "提前退租",
}


def _level_line(findings: list[dict]) -> str:
    """根据发现列表给出整体风险等级"""
    if any(f["severity"] == "高" for f in findings):
        return "高风险"
    if findings:
        return "中风险"
    return "低风险"


def _finding_section(title: str, emoji: str, items: list[dict]) -> list[str]:
    lines = [f"### {emoji} {title}", ""]
    if not items:
        lines += ["未发现该类风险。", ""]
        return lines
    for i, f in enumerate(items, 1):
        lines.append(f"{i}. **{f['rule_name']}**")
        lines.append("")
        lines.append(f"   - 命中原文：`{f['matched']}`")
        lines.append(f"   - 建议：{f['suggestion']}")
        lines.append("")
    return lines


def _info_table(extracted: dict | None) -> list[str]:
    lines = ["### 关键条款（LLM 抽取）", "", "| 字段 | 内容 |", "| --- | --- |"]
    if not extracted:
        lines.append("| LLM 抽取失败 | 仅展示规则结果 |")
        return lines
    for field, label in _FIELD_LABELS.items():
        value = extracted.get(field)
        if value:
            lines.append(f"| {label} | {value} |")
        else:
            lines.append(f"| {label} | 未填写/未提取到 |")
    lines.append("")
    return lines


def generate_report(findings: list[dict], extracted: dict | None) -> str:
    """把规则发现 + LLM 抽取合成一份 Markdown 报告"""
    high = [f for f in findings if f["severity"] == "高"]
    medium = [f for f in findings if f["severity"] == "中"]
    total = len(findings)
    level = _level_line(findings)

    lines = []
    lines.append("# 租房合同风险审查报告")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("## 一、总体结论")
    lines.append("")
    lines.append(f"- **整体风险等级：{level}**")
    lines.append(f"- 共发现 **{total} 处**风险（高风险 {len(high)} 处 / 中风险 {len(medium)} 处）")
    if extracted and extracted.get("risk_summary"):
        lines.append(f"- **LLM 总结**：{extracted['risk_summary']}")
    lines.append("")
    lines.append("## 二、风险发现明细")
    lines.append("")
    lines += _finding_section("高风险条款", "🔴", high)
    lines += _finding_section("中风险条款", "🟡", medium)
    lines += _info_table(extracted)
    lines.append("## 三、审查建议")
    lines.append("")
    lines.append("- 高风险条款建议在签约前与出租方协商修改；")
    lines.append("- 「由甲方决定」「不予退还」等自由裁量表述应改为明确标准；")
    lines.append("- 违约金、押金条款明显过高的，可依据《民法典》请求调低；")
    lines.append("- 拿不准的条款建议咨询专业法律人士后再签字。")
    lines.append("")
    return "\n".join(lines)