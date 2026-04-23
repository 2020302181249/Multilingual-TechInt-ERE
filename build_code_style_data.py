import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List


ENTITY_TYPES = "?????????????????????????????"
RELATION_TYPES = "???????????????????????????????????????????????????????????"

SYSTEM_PROMPT = (
    "?????? Python ????????? text ?? text ?????????"
    "?????????????????????? result['entities'] ? result['relations'] ??"
    "???????????????? result['entities'].append ???? return result ???????????\n"
    "???????????????????Step 1?????????????????Step 2?????? result?"
)


def first_mention(cluster: Dict) -> Dict[str, str]:
    mentions = cluster.get("link", [])
    mention = mentions[0] if mentions else {}
    return {"text": str(mention.get("text", "")).strip(), "type": str(cluster.get("type", mention.get("type", ""))).strip()}


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
    return (
        "def information_extraction(text):\n"
        "    \"\"\"?? text ?????????????????????\n"
        f"    ?????{ENTITY_TYPES}\n"
        f"    ?????{RELATION_TYPES}\n"
        "    ?? result ???\n"
        "        result['entities'] = [{'text': ???, 'type': ????}, ...]\n"
        "        result['relations'] = [{'head': ???, 'tail': ???, 'type': ????}, ...]\n"
        "    \"\"\"\n"
        f"    text = {json.dumps(text, ensure_ascii=False)}\n"
        "    result = {'entities': [], 'relations': []}\n"
        "    # ??????????????????????????????????"
    )


def build_assistant_code(item: Dict) -> str:
    lines = ["# Step 1: ????"]
    for entity in iter_entities(item.get("entityLink", {})):
        lines.append(f"result['entities'].append({json.dumps(entity, ensure_ascii=False)})")
    lines.append("")
    lines.append("# Step 2: ?????????")
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
