"""Reusable pagination helpers."""

from __future__ import annotations

from typing import Any

from django.db.models import QuerySet


def paginate_queryset(
    queryset: QuerySet[Any],
    page: int = 1,
    per_page: int = 20,
) -> tuple[QuerySet[Any], int, int, int]:
    """Return (page_qs, total, page, total_pages)."""
    total = queryset.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    page_qs = queryset[start : start + per_page]
    return page_qs, total, page, total_pages
