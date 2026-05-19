SAFE_LANGUAGE_GUARDRAILS = """
Use educational, non-directive language.
Do not say: buy this, sell this, guaranteed return, this will outperform.
Prefer phrases such as:
- This suggests
- One risk to review is
- You may want to compare
- Based on the provided data
"""

PORTFOLIO_SUMMARY_PROMPT = """
Summarize the portfolio using only the structured context.
Cover total value, diversification, missing data, risk flags, and next review areas.
"""

QUESTION_ANSWERING_PROMPT = """
Answer the user's question using only the structured portfolio context.
If the data is missing, say what is missing and what the user may want to compare.
"""


def build_prompt(*, mode: str, context: dict) -> str:
    prompt = PORTFOLIO_SUMMARY_PROMPT if mode == "summary" else QUESTION_ANSWERING_PROMPT
    return f"{SAFE_LANGUAGE_GUARDRAILS}\n{prompt}\nContext keys: {', '.join(context.keys())}"
