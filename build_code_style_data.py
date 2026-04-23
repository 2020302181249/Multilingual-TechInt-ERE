import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List


ENTITY_TYPES = "\u4f01\u4e1a\u3001\u673a\u6784\u3001\u4eba\u5458\u3001\u56fd\u5bb6\u3001\u5730\u70b9\u3001\u6280\u672f\u3001\u4ea7\u54c1\u3001\u653f\u7b56\u3001\u6cd5\u89c4\u3001\u65f6\u95f4"
RELATION_TYPES = "\u7ade\u4e89\u3001\u5408\u4f5c\u3001\u4ece\u5c5e\u3001\u4f4d\u4e8e\u3001\u62e5\u6709\u3001\u51fa\u751f\u5730\u3001\u7814\u53d1\u3001\u5236\u5b9a\u3001\u91c7\u7528\u3001\u5305\u542b\u3001\u515a\u6d3e\u3001\u4eb2\u5c5e\u3001\u540c\u4e8b\u3001\u96c7\u4f63\u3001\u521b\u529e\u4eba\u3001\u8d1f\u8d23\u4eba\u3001\u7ba1\u7406\u3001\u804c\u4f4d\u3001\u522b\u540d"

SYSTEM_PROMPT = (
    "\u8bf7\u8865\u5168\u4e0b\u9762\u7684 Python \u51fd\u6570\u4e3b\u4f53\uff0c\u4f7f\u5176\u6839\u636e text \u5148\u4ece text \u62bd\u53d6\u5b9e\u4f53\u53ca\u5176\u7c7b\u578b\uff0c"
    "\u518d\u5728\u5df2\u62bd\u53d6\u5b9e\u4f53\u4e4b\u95f4\u62bd\u53d6\u5173\u7cfb\uff0c\u5e76\u5c06\u7ed3\u679c\u4f9d\u6b21\u586b\u5165 result['entities'] \u548c result['relations'] \u4e2d\u3002"
    "\u53ea\u9700\u7ed9\u51fa\u51fd\u6570\u4f53\u4e2d\u76f8\u5e94\u7684\u4ee3\u7801\u884c\uff08\u4ece result['entities'].append \u5f00\u59cb\uff0c\u5230 return result \u7ed3\u675f\uff09\uff0c\u4e0d\u8981\u989d\u5916\u89e3\u91ca\u3002\n"
    "\u5728\u5b9e\u73b0\u51fd\u6570\u4f53\u65f6\uff0c\u8bf7\u5148\u5b8c\u6210\u5b9e\u4f53\u62bd\u53d6\u90e8\u5206\uff08Step 1\uff09\uff0c\u518d\u5b8c\u6210\u57fa\u4e8e\u5b9e\u4f53\u7684\u5173\u7cfb\u62bd\u53d6\u90e8\u5206\uff08Step 2\uff09\uff0c\u6700\u540e\u8fd4\u56de result\u3002"
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
    return (
        "def information_extraction(text):\n"
        "    \"\"\"\u5148\u4ece text \u4e2d\u62bd\u53d6\u5b9e\u4f53\u53ca\u5176\u7c7b\u578b\uff0c\u518d\u62bd\u53d6\u5b9e\u4f53\u4e4b\u95f4\u7684\u5173\u7cfb\u3002\n"
        f"    \u5b9e\u4f53\u7c7b\u578b\uff1a{ENTITY_TYPES}\n"
        f"    \u5173\u7cfb\u7c7b\u578b\uff1a{RELATION_TYPES}\n"
        "    \u8fd4\u56de result \u5b57\u5178\uff1a\n"
        "        result['entities'] = [{'text': \u5b9e\u4f53\u540d, 'type': \u5b9e\u4f53\u7c7b\u578b}, ...]\n"
        "        result['relations'] = [{'head': \u5934\u5b9e\u4f53, 'tail': \u5c3e\u5b9e\u4f53, 'type': \u5173\u7cfb\u7c7b\u578b}, ...]\n"
        "    \"\"\"\n"
        f"    text = {json.dumps(text, ensure_ascii=True)}\n"
        "    result = {'entities': [], 'relations': []}\n"
        "    # \u62bd\u53d6\u7684\u5b9e\u4f53\u548c\u5173\u7cfb\u5217\u8868\u5982\u4e0b\uff08\u5b9e\u73b0\u65f6\u5efa\u8bae\u5148\u5b9e\u73b0\u5b9e\u4f53\u62bd\u53d6\uff0c\u518d\u5b9e\u73b0\u5173\u7cfb\u62bd\u53d6\uff09"
    )


def build_assistant_code(item: Dict) -> str:
    lines = ["# Step 1: \u62bd\u53d6\u5b9e\u4f53"]
    for entity in iter_entities(item.get("entityLink", {})):
        lines.append(f"result['entities'].append({json.dumps(entity, ensure_ascii=True)})")
    lines.append("")
    lines.append("# Step 2: \u62bd\u53d6\u5b9e\u4f53\u4e4b\u95f4\u7684\u5173\u7cfb")
    for relation in iter_relations(item):
        lines.append(f"result['relations'].append({json.dumps(relation, ensure_ascii=True)})")
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
    Path(args.output).write_text(json.dumps(converted, ensure_ascii=True, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
