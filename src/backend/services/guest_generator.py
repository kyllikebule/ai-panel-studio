"""嘉宾生成服务：调用 LLM 生成差异化嘉宾列表。"""
import json
import logging

from src.backend.core.deepseek import deepseek_chat
from src.logic.prompt_lib import GuestDef, GUEST_SPEAK_CONTENT

logger = logging.getLogger(__name__)


class GuestGenerationError(Exception):
    """嘉宾生成失败时抛出，含原因描述。"""
    pass


async def generate_guests(topic: str, count: int) -> list[GuestDef]:
    """调用 LLM 生成 count 位差异化嘉宾，返回标准化 GuestDef 列表。

    Args:
        topic: 讨论主题
        count: 需要生成的嘉宾数量（2-6）

    Returns:
        标准化嘉宾定义列表

    Raises:
        GuestGenerationError: LLM 调用失败
    """
    prompt = (
        f"讨论主题：{topic}\n"
        f"请生成 {count} 位立场差异化的 AI 专家嘉宾，每位嘉宾需有不同的persona和发言风格。\n"
        f"仅返回 JSON 数组，格式："
        '[{"name":"姓名","persona":"人设描述（至少10字符）","speak_style":"发言风格","system_prompt":"系统prompt"}]'
        f"\n要求：各位嘉宾的 persona 必须互不相同，代表不同立场和视角。"
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        result = await deepseek_chat(
            messages=messages,
            model="deepseek-chat",
            temperature=0.8,
            max_tokens=2048,
        )
    except Exception as e:
        logger.error("嘉宾生成失败: %s", e)
        raise GuestGenerationError(f"嘉宾生成失败: {e}") from e

    raw_content = result["choices"][0]["message"]["content"]
    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1])

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise GuestGenerationError(f"LLM 返回非 JSON: {raw_content[:200]}") from e

    if not isinstance(data, list):
        raise GuestGenerationError(f"期望 JSON 数组，实际: {type(data)}")

    guests = []
    for item in data[:count]:
        guests.append(GuestDef(
            name=str(item.get("name", "")).strip(),
            persona=str(item.get("persona", "")).strip(),
            system_prompt=str(item.get("system_prompt", "")).strip(),
            speak_style=str(item.get("speak_style", "")).strip(),
        ))

    if len(guests) != count:
        raise GuestGenerationError(f"期望 {count} 位嘉宾，实际生成 {len(guests)} 位")

    return guests


def validate_guest_diversity(guests: list[GuestDef]) -> bool:
    """校验嘉宾立场差异化：persona 字段两两编辑距离 ≥ 10 字符。

    Args:
        guests: 嘉宾列表

    Returns:
        True 表示所有嘉宾两两 persona 有足够差异
    """
    if len(guests) <= 1:
        return True

    for i in range(len(guests)):
        for j in range(i + 1, len(guests)):
            if _edit_distance(guests[i].persona, guests[j].persona) < 10:
                return False

    return True


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein 编辑距离。"""
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(
                curr[-1] + 1,
                prev[j] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            ))
        prev = curr

    return prev[-1]
