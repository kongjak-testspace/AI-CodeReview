def build_review_prompt(diff: str, language: str, extra_instructions: str = "") -> str:
    extra_section = ""
    if extra_instructions.strip():
        extra_section = f"\nAdditional instructions:\n{extra_instructions.strip()}\n"

    return f"""You are an expert pull request code reviewer.

Review only the provided unified diff.
Write the review in {language}.
Focus on correctness, bugs, security, performance, and maintainability.
Only comment on changed lines from the diff.

Your response must be strict JSON matching this schema:
{{
  "summary": "Overall review summary",
  "comments": [
    {{
      "path": "src/example.py",
      "line": 42,
      "body": "Specific inline review comment"
    }}
  ]
}}

Rules:
- Output JSON only.
- Do not wrap JSON in markdown code fences.
- Do not include any extra text before or after JSON.
- If there are no inline comments, return an empty comments array.
{extra_section}
Diff to review:
```diff
{diff}
```
"""
