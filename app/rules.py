"""规则引擎（D3+ 迭代版）：用关键词 + 正则锁死高频陷阱条款"""

import re

# ---------- 规则定义（数据驱动：以后加规则 = 加一条字典） ----------

RISK_RULES = [
    {
        "id": "R01",
        "name": "押金退还条款模糊",
        "severity": "高",
        "suggestion": "押金退还条件应明确写死（如：结清费用且房屋无损坏后全额无息退还）；「由甲方决定」「不予退还」「没收押金」属于自由裁量，退租时极易被克扣。",
        "patterns": [
            r"押金.{0,30}(由甲方决定|由出租方决定|甲方酌情|视甲方|甲方说了算)",
            r"没收.{0,15}(全部)?押金",
            r"押金.{0,10}(不予退还|不予返还|不退还|概不退还)",
        ],
    },
    {
        "id": "R02",
        "name": "违约金比例过高",
        "severity": "动态",
        "suggestion": "《民法典》第585条允许违约金过高时请求法院调低，司法实践一般以实际损失的30%为参考线；建议违约金不超过月租金的30%。",
        "patterns": [
            r"月租金的?\s*(\d{1,3})\s*[%％]",
            r"(?:剩余|全部)?租金的?\s*(\d{1,3})\s*[%％]",
            r"违约金.{0,30}([一二两三四五六七八九十]{1,2})个月(租金|房租)",
        ],
    },
    {
        "id": "R03",
        "name": "转租惩罚过重",
        "severity": "中",
        "suggestion": "《民法典》第716条：承租人经出租人同意可以转租。限制转租本身合法，但「无条件收回+没收押金+全额赔偿+连带责任」等惩罚明显过重。",
        "patterns": [
            r"(?:转租|转借).{0,80}(没收.{0,10}押金|全额赔偿|无条件|全部.{0,8}连带责任)",
            r"(?:转租|转借).{0,20}(无权拒绝|自由裁量|甲方决定)",
        ],
    },
    {
        "id": "R04",
        "name": "维修责任转嫁乙方",
        "severity": "高",
        "suggestion": "《民法典》第712条：出租人应履行维修义务，仅承租人过错造成的损坏才由承租人担责。自然损耗/老化费用全由乙方承担属于责任转嫁，显失公平。",
        "patterns": [
            r"(?:维修|更换|修缮)(?:责任|费用)?.{0,30}均由(乙方|承租方).{0,10}(承担|自理|负责|支付)",
            r"(全部|所有|一切).{0,25}(损坏|故障|老化|损耗).{0,45}(维修|修缮|更换).{0,20}由?(乙方|承租方).{0,10}(承担|自理|负责|支付)",
            r"(自然|正常|老化)损耗.{0,30}(乙方|承租方).{0,10}(承担|自理|负责)",
        ],
    },
    {
        "id": "R05",
        "name": "提前退租惩罚过重",
        "severity": "高",
        "suggestion": "提前退租违约金应合理（常见为1-2个月租金）；「剩余租金50%+押金不退」双重惩罚明显过高，可请求法院调低。",
        "patterns": [
            r"(乙方|承租方)(?:(?!甲方).){0,15}?(擅自)?(提前退租|提前解约|单方解除合同|单方终止合同|无故搬离).{0,60}?(50%|不予退还|不退还|没收|全部租金)",
        ],
    },
    {
        "id": "R06",
        "name": "租金单方调整",
        "severity": "高",
        "suggestion": "《民法典》第543条：合同变更需双方协商一致。单方调整租金且提前通知即生效，剥夺承租方定价话语权；乙方不同意还构成违约，属于双重陷阱。",
        "patterns": [
            r"(甲方|出租方)(?:(?!乙方|不得|禁止|无权|不可|不允许).){0,50}(?:单方|单方面).{0,15}(?:调整|提高|上调).{0,15}租金",
            r"(甲方|出租方)(?:(?!乙方|不得|禁止|无权|不可|不允许).){0,50}(?:单方|单方面).{0,10}租金(?:调整|上涨|上调)",
        ],
    },
]


def _penalty_severity(m: re.Match) -> str | None:
    """R02 动态风险等级：>=50% 高，30%~50% 中，<=30% 不算风险"""
    try:
        pct = int(m.group(1))
    except (ValueError, IndexError):
        return "中"  # 汉字数字形式（如"两个月租金"）给中等风险
    if pct >= 50:
        return "高"
    if pct > 30:
        return "中"
    return None


def check_rules(text: str) -> list[dict]:
    """跑全部规则，返回风险发现列表：去重、按原文位置排序"""
    findings = []
    seen_text = set()   # 同规则 + 完全相同的命中原文，只报一次
    for rule in RISK_RULES:
        spans = []      # 同规则内已报过的区间，重叠的跳过（防止同一条款被多个句式重复报）
        for pattern in rule["patterns"]:
            for m in re.finditer(pattern, text):
                if any(m.start() < e and m.end() > s for s, e in spans):
                    continue
                matched = m.group(0)
                key = (rule["id"], matched)
                if key in seen_text:
                    continue
                seen_text.add(key)
                spans.append((m.start(), m.end()))
                severity = rule["severity"]
                if severity == "动态":
                    severity = _penalty_severity(m)
                    if severity is None:
                        continue
                findings.append(
                    {
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "severity": severity,
                        "pos": m.start(),
                        "matched": matched,
                        "snippet": text[max(0, m.start() - 20) : m.end() + 20],
                        "suggestion": rule["suggestion"],
                    }
                )
    findings.sort(key=lambda f: (f["pos"], f["rule_id"]))
    return findings