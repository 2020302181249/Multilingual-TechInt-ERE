# -*- coding: utf-8 -*-
import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List


ENTITY_TYPES = "企业、机构、人员、国家、地点、技术、产品、政策、法规、时间"
RELATION_TYPES = "竞争、合作、从属、位于、拥有、出生地、研发、制定、采用、包含、党派、亲属、同事、雇佣、创办人、负责人、管理、职位、别名"

SYSTEM_PROMPT = (
    "请补全下面的 Python 函数主体，使其根据 text 先从 text 抽取实体及其类型，"
    "再在已抽取实体之间抽取关系，并将结果依次填入 result['entities'] 和 result['relations'] 中。"
    "只需给出函数体中相应的代码行（从 result['entities'].append 开始，到 return result 结束），不要额外解释。\n"
    "在实现函数体时，请先完成实体抽取部分（Step 1），再完成基于实体的关系抽取部分（Step 2），最后返回 result。"
)


def first_mention(cluster: Dict) -> Dict[str, str]:
    mentions = cluster.get("link", [])
    mention = mentions[0] if mentions else {}
    return {
        "text": str(mention.get("text", "")).strip(),
        "type": str(cluster.get("type", mention.get("type", ""))).strip(),
    }


def iter_entities(entity_link: Dict[str, Dict]) -> Iterable[Dict[str, str]]:
    for cluster in entity_link.values():
        entity = first_mention(cluster)
        if entity["text"] and entity["type"]:
            yield entity


def iter_relations(item: Dict) -> Iterable[Dict[str, str]]:
    entity_link = item.get("entityLink", {})
    for relation in item.get("relation", []):
        head = first_mention(entity_link.get(relation.get("link1"), {})).get("text", "")
        tail = first_mention(entity_link.get(relation.get("link2"), {})).get("text", "")
        rel_type = str(relation.get("type", "")).strip()
        if head and tail and rel_type:
            yield {"head": head, "tail": tail, "type": rel_type}


def build_user_prompt(text: str) -> str:
    lines = [
        "def information_extraction(text):",
        '    """先从 text 中抽取实体及其类型，再抽取实体之间的关系。',
        f"    实体类型：{ENTITY_TYPES}",
        f"    关系类型：{RELATION_TYPES}",
        "    返回 result 字典：",
        "        result['entities'] = [{'text': 实体名, 'type': 实体类型}, ...]",
        "        result['relations'] = [{'head': 头实体, 'tail': 尾实体, 'type': 关系类型}, ...]",
        '    """',
        f"    text = {json.dumps(text, ensure_ascii=False)}",
        "    result = {'entities': [], 'relations': []}",
        "    # 抽取的实体和关系列表如下（实现时建议先实现实体抽取，再实现关系抽取）",
    ]
    return "\n".join(lines)


def build_assistant_code(item: Dict) -> str:
    lines = ["# Step 1: 抽取实体"]
    for entity in iter_entities(item.get("entityLink", {})):
        lines.append(f"result['entities'].append({json.dumps(entity, ensure_ascii=False)})")
    lines.append("")
    lines.append("# Step 2: 抽取实体之间的关系")
    for relation in iter_relations(item):
        lines.append(f"result['relations'].append({json.dumps(relation, ensure_ascii=False)})")
    lines.append("return result")
    return "\n".join(lines)


def convert_item(item: Dict) -> Dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(str(item.get("doc", "")))},
            {"role": "assistant", "content": build_assistant_code(item)},
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert raw ER annotations into code-style ShareGPT messages.")
    parser.add_argument("--input", required=True, help="Raw annotation JSON file.")
    parser.add_argument("--output", required=True, help="Output code-style JSON file.")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    converted: List[Dict] = [convert_item(item) for item in data]
    Path(args.output).write_text(json.dumps(converted, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
