import re
from typing import Literal

from pydantic import BaseModel, Field


UploadTargetField = Literal[
    "symbol",
    "quantity",
    "average_cost",
    "market_value",
    "company_name",
    "sector",
    "asset_class",
    "exchange",
    "currency",
]


class ColumnMappingSuggestion(BaseModel):
    target_field: UploadTargetField
    source_column: str
    confidence: float = Field(ge=0, le=1)
    reason: str


FIELD_SYNONYMS: dict[UploadTargetField, tuple[str, ...]] = {
    "symbol": ("ticker", "symbol", "stock", "scrip", "instrument"),
    "quantity": ("qty", "shares", "quantity", "units"),
    "average_cost": ("avg cost", "average price", "buy price", "cost"),
    "market_value": ("value", "market value", "current value"),
    "company_name": ("name", "company", "security name"),
    "sector": ("sector",),
    "asset_class": ("asset class",),
    "exchange": ("exchange",),
    "currency": ("currency",),
}

TARGET_FIELD_ORDER: tuple[UploadTargetField, ...] = (
    "symbol",
    "quantity",
    "average_cost",
    "market_value",
    "company_name",
    "sector",
    "asset_class",
    "exchange",
    "currency",
)

EXACT_CONFIDENCE = 1.0
CONTAINED_CONFIDENCE = 0.85


def suggest_column_mappings(columns: list[str]) -> list[ColumnMappingSuggestion]:
    """Suggest manual upload mappings from detected source columns.

    This function is deterministic and side-effect free. It does not persist or
    auto-apply mappings.
    """
    candidates = [_ColumnCandidate(original=column, normalized=_normalize_column(column)) for column in columns]
    suggestions: list[ColumnMappingSuggestion] = []
    used_columns: set[str] = set()

    for target_field in TARGET_FIELD_ORDER:
        match = _best_match(target_field=target_field, candidates=candidates, used_columns=used_columns)
        if match is None:
            continue

        candidate, synonym, confidence, reason = match
        used_columns.add(candidate.original)
        suggestions.append(
            ColumnMappingSuggestion(
                target_field=target_field,
                source_column=candidate.original,
                confidence=confidence,
                reason=reason.format(synonym=synonym),
            )
        )

    return suggestions


def suggest_column_mappings_from_rows(rows: list[dict]) -> list[ColumnMappingSuggestion]:
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for column in row:
            column_name = str(column)
            if column_name not in seen:
                seen.add(column_name)
                columns.append(column_name)
    return suggest_column_mappings(columns)


class _ColumnCandidate(BaseModel):
    original: str
    normalized: str


def _best_match(
    *,
    target_field: UploadTargetField,
    candidates: list[_ColumnCandidate],
    used_columns: set[str],
) -> tuple[_ColumnCandidate, str, float, str] | None:
    matches: list[tuple[int, int, _ColumnCandidate, str, float, str]] = []
    for candidate_index, candidate in enumerate(candidates):
        if candidate.original in used_columns or not candidate.normalized:
            continue
        for synonym_index, synonym in enumerate(FIELD_SYNONYMS[target_field]):
            normalized_synonym = _normalize_column(synonym)
            if candidate.normalized == normalized_synonym:
                matches.append(
                    (
                        0,
                        synonym_index,
                        candidate,
                        synonym,
                        EXACT_CONFIDENCE,
                        "Exact column match for '{synonym}'.",
                    )
                )
            elif _contains_phrase(candidate.normalized, normalized_synonym):
                matches.append(
                    (
                        1,
                        synonym_index,
                        candidate,
                        synonym,
                        CONTAINED_CONFIDENCE,
                        "Column contains synonym '{synonym}'.",
                    )
                )
    if not matches:
        return None

    _match_rank, _synonym_rank, candidate, synonym, confidence, reason = min(
        matches,
        key=lambda match: (match[0], match[1], len(match[2].normalized), match[2].normalized),
    )
    return candidate, synonym, confidence, reason


def _contains_phrase(column: str, phrase: str) -> bool:
    column_tokens = column.split()
    phrase_tokens = phrase.split()
    if not phrase_tokens or len(phrase_tokens) > len(column_tokens):
        return False
    window_size = len(phrase_tokens)
    return any(column_tokens[index : index + window_size] == phrase_tokens for index in range(len(column_tokens)))


def _normalize_column(column: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(column).strip().lower())
    return re.sub(r"\s+", " ", cleaned).strip()
