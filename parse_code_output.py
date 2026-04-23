import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List


ENTITY_APPEND_RE = re.compile(r"""result\['entities'\]\.append\((\{.*?\})\)""", re.DOTALL)
RELATION_APPEND_RE = re.compile(r"""result\['relations'\]\.append\((\{.*?\})\)""", re.DOTALL)


def _safe_dict(text: str) -> Dict[str, Any]:
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def strip_generation_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    fenced = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    return fenced.group(1).strip() if fenced else text


def parse_code_output(text: str) -> Dict[str, List[Dict[str, str]]]:
    text = strip_generation_text(text)
    entities: List[Dict[str, str]] = []
    relations: List[Dict[str, str]] = []

    for match in ENTITY_APPEND_RE.finditer(text):
        item = _safe_dict(match.group(1))
        if {"text", "type"} <= item.keys():
            entities.append({"text": str(item["text"]).strip(), "type": str(item["type"]).strip()})

    for match in RELATION_APPEND_RE.finditer(text):
        item = _safe_dict(match.group(1))
        if {"head", "tail", "type"} <= item.keys():
            relations.append(
                {
                    "head": str(item["head"]).strip(),
                    "tail": str(item["tail"]).strip(),
                    "type": str(item["type"]).strip(),
                }
            )

    return {"entities": entities, "relations": relations}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse code-style IE model output.")
    parser.add_argument("--input", required=True, help="Path to generated text/code.")
    parser.add_argument("--output", required=True, help="Path to write parsed JSON.")
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    parsed = parse_code_output(text)
    Path(args.output).write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
