def build_synthesis_prompt(reviews: dict[str, str], diff: str, language: str) -> str:
    reviews_section = ""
    for cli_name, review_output in reviews.items():
        reviews_section += f"\n--- Review by {cli_name} ---\n{review_output}\n"

    return f"""You are an expert code review synthesizer.

You are given multiple independent code reviews of the same pull request diff, each produced by a different AI reviewer.
Your job is to synthesize them into a single, comprehensive, high-quality review.

Write the review in {language}.

Guidelines:
- Merge overlapping or duplicate comments into one.
- Keep all unique, valid findings from each reviewer.
- Resolve contradictions by favoring the more technically correct opinion.
- Preserve specific line numbers and file paths from the original reviews.
- Do not invent new issues that no reviewer mentioned.

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

Individual reviews:
{reviews_section}

Original diff for reference:
```diff
{diff}
```
"""


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
