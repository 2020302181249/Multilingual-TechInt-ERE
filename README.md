# Anonymous Repository for Paper Submission

This repository contains a compact anonymous release for review. It includes sample data and the minimal code needed to show the proposed code-style entity-relation extraction format.

## Files

- `raw_sample.json`: 8 annotated raw samples. The sample covers the four main languages used in the paper: Chinese, English, Russian, and Spanish, with 2 samples for each language.
- `code_style_train_sample.json`: 8 training samples in ShareGPT/LLaMA-Factory `messages` format. These examples show how raw entity-relation annotations are converted into code-style function-completion data.
- `build_code_style_data.py`: Converts raw annotation records into code-style training data.
- `parse_code_output.py`: Parses model outputs such as `result['entities'].append(...)` and `result['relations'].append(...)` into structured JSON.


## Data Format

`raw_sample.json` uses the original annotation structure. Important fields are:

- `doc`: source text.
- `entityLink`: entity clusters. Each cluster contains entity mentions and entity type labels.
- `relation`: relation annotations between entity cluster ids.
- `lang`: language label.

`code_style_train_sample.json` uses this structure:

```json
{
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

The assistant response is a code-style extraction result, for example:

```python
result['entities'].append({"text": "...", "type": "..."})
result['relations'].append({"head": "...", "tail": "...", "type": "..."})
return result
```

## Usage

Convert raw samples into code-style samples:

```bash
python build_code_style_data.py --input raw_sample.json --output converted_code_style_sample.json
```

Parse one model output file:

```bash
python parse_code_output.py --input model_output.txt --output parsed_output.json
```

## Encoding Note

The Python source files are ASCII-safe. Chinese prompts and labels are written with Unicode escape sequences in `build_code_style_data.py`, so they remain valid even if a web page or upload tool does not display UTF-8 correctly.
