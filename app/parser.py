import json
import re

from pydantic import BaseModel, Field, ValidationError


class ReviewComment(BaseModel):
    path: str
    line: int
    body: str


class ReviewResult(BaseModel):
    summary: str
    comments: list[ReviewComment] = Field(default_factory=list)


def _is_valid_json_object(text: str) -> bool:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(parsed, dict)


def _extract_balanced_json_object(text: str) -> str | None:
    start = -1
    depth = 0
    in_string = False
    escaped = False

    for index, char in enumerate(text):
        if start == -1:
            if char == "{":
                start = index
                depth = 1
                in_string = False
                escaped = False
            continue

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : index + 1]
                if _is_valid_json_object(candidate):
                    return candidate
                start = -1

    return None


def extract_json_from_text(text: str) -> str | None:
    stripped = text.strip()
    if not stripped:
        return None

    fenced_json_match = re.search(
        r"```json\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE
    )
    if fenced_json_match:
        candidate = fenced_json_match.group(1).strip()
        if _is_valid_json_object(candidate):
            return candidate

    if _is_valid_json_object(stripped):
        return stripped

    return _extract_balanced_json_object(text)


def parse_review_output(raw_output: str) -> ReviewResult:
    json_text = extract_json_from_text(raw_output)

    if json_text is not None:
        try:
            parsed = json.loads(json_text)
            return ReviewResult.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError, TypeError):
            pass

    return ReviewResult(summary=raw_output, comments=[])
