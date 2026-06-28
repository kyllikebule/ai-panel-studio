"""嘉宾生成 —— 调用 LLM 生成立场差异化的嘉宾列表。"""
from .prompt_lib import GuestDef


class GuestGenerationError(Exception):
    """嘉宾生成失败时抛出。"""
    pass


async def generate_guests(topic: str, count: int, llm_client) -> list[GuestDef]:
    """生成 count 位立场差异化的嘉宾。

    Args:
        topic: 讨论主题
        count: 嘉宾人数 (2-6)
        llm_client: 注入的 LLM 客户端（测试时 mock），需要有 chat_json 方法

    Returns:
        标准化 GuestDef 列表

    Raises:
        ValueError: count 不在 2-6 范围内
    """
    if count < 2:
        raise ValueError("至少需要 2 位嘉宾参与讨论")
    if count > 6:
        raise ValueError("最多生成 6 位嘉宾")

    try:
        result = await llm_client.chat_json(
            f"""你是一位专业讨论策划。请为以下讨论主题生成 {count} 位立场差异化的嘉宾。

讨论主题：{topic}

要求：
1. 每位嘉宾立场必须不同（至少 2 种不同立场），涵盖支持、反对、中间等多种视角
2. 返回 JSON 格式: {{"guests": [{{"name": "姓名", "persona": "人设描述+立场", "speak_style": "发言风格", "system_prompt": "完整角色提示"}}]}}
3. name 必须各不相同
4. persona 需体现对该话题的具体立场，至少 10 字
5. speak_style 从以下选一：学术严谨、理性分析、法律实务、政策导向、实战经验、犀利追问
"""
        )
        raw_guests = result.get("guests", [])
    except Exception:
        return _fallback_guests(count)

    if len(raw_guests) < count:
        raw_guests = raw_guests[:count]

    guests = []
    for g in raw_guests[:count]:
        guests.append(GuestDef(
            name=g.get("name", "").strip(),
            persona=g.get("persona", "").strip(),
            speak_style=g.get("speak_style", "").strip(),
            system_prompt=g.get("system_prompt", "").strip(),
        ))

    if not validate_guest_diversity(guests):
        return _fallback_guests(count)

    return guests


def validate_guest_diversity(guests: list[GuestDef]) -> bool:
    """校验嘉宾立场差异化：至少 2 位嘉宾 persona 有明显不同。

    使用简单规则：收集所有 persona 字符集，检查是否有至少 2 个明显不同的 persona。
    """
    if len(guests) < 2:
        return False

    personas = [g.persona for g in guests]

    def _simple_similarity(a: str, b: str) -> float:
        """简单字符级别相似度。"""
        set_a, set_b = set(a), set(b)
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    unique_count = 1
    for i in range(1, len(personas)):
        is_unique = True
        for j in range(i):
            if _simple_similarity(personas[i], personas[j]) > 0.7:
                is_unique = False
                break
        if is_unique:
            unique_count += 1

    return unique_count >= 2


def _fallback_guests(count: int) -> list[GuestDef]:
    """LLM 失败或立场不足时的预设嘉宾回退。"""
    pool = [
        GuestDef(name="李教授", persona="AI伦理学专家，主张对高风险AI严格监管",
                 system_prompt="你是李教授，AI伦理学专家。发言时引用学术研究，语气平和但有分量。",
                 speak_style="学术严谨"),
        GuestDef(name="王博士", persona="计算机科学家，技术乐观派，认为创新不应被过度束缚",
                 system_prompt="你是王博士，计算机科学家。发言时注重逻辑和数据，强调技术发展的重要性。",
                 speak_style="理性分析"),
        GuestDef(name="张律师", persona="科技法律顾问，关注监管与创新的平衡",
                 system_prompt="你是张律师，科技法律顾问。发言时从法律实务角度出发，强调可操作性。",
                 speak_style="法律实务"),
        GuestDef(name="赵研究员", persona="产业政策研究员，宏观视角看产业影响",
                 system_prompt="你是赵研究员，产业政策专家。发言时从宏观经济和产业链角度分析问题。",
                 speak_style="政策导向"),
        GuestDef(name="陈总", persona="AI企业创始CEO，行业深耕实践者",
                 system_prompt="你是陈总，AI企业CEO。发言时结合创业实战经验，关注落地可行性。",
                 speak_style="实战经验"),
        GuestDef(name="孙记者", persona="科技媒体人，代表公众视角追问",
                 system_prompt="你是孙记者，科技媒体人。发言时代表公众追问，直击要害。",
                 speak_style="犀利追问"),
    ]
    return pool[:count]
