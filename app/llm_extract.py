"""LLM 调用封装（D4 版：JSON mode 结构化抽取合同关键条款）"""

import json

from openai import OpenAI

from . import config


def get_client() -> OpenAI:
    return OpenAI(
        api_key=config.DASHSCOPE_API_KEY,
        base_url=config.LLM_BASE_URL,
        timeout=30.0,  # 30 秒超时，防止 API 卡住时接口长时间挂起（超时走降级逻辑）
    )


def quick_test() -> str:
    """验证 API key 是否可用"""
    client = get_client()
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[{"role": "user", "content": "用一句话介绍你自己"}],
    )
    return resp.choices[0].message.content


EXTRACT_SYSTEM_PROMPT = """你是合同审查助手，请从房屋租赁合同中抽取结构化信息。
只输出 JSON，不要输出任何其他内容。JSON 结构如下：
{
  "rent_amount": "每月租金金额，没有则填 null",
  "deposit_amount": "押金金额，没有则填 null",
  "lease_term": "租期，如一年/两年，没有则填 null",
  "payment_method": "支付方式，如押一付三，没有则填 null",
  "penalty_clause": "违约金条款的原文摘要，没有则填 null",
  "repair_responsibility": "维修责任归属的原文摘要，没有则填 null",
  "sublease_clause": "转租条款的原文摘要，没有则填 null",
  "early_termination": "提前退租条款的原文摘要，没有则填 null",
  "risk_summary": "用一句话总结本合同对承租方最大的风险"
}
摘要要保留原文关键表述，不要自行发挥。"""


def _parse_json(content: str) -> dict:
    """容错解析：去掉可能出现的 ```json 代码块包裹"""
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


def extract_clauses(text: str) -> dict:
    """抽取合同关键条款，返回 dict；抽取失败抛异常"""
    if not text.strip():
        raise ValueError("合同文本为空")
    client = get_client()
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
            # 合同全文最多截前 8000 字，控制 token 成本
            {"role": "user", "content": f"合同全文：\n{text[:8000]}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return _parse_json(resp.choices[0].message.content)