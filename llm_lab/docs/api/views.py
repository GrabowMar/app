"""Docs API views."""

from __future__ import annotations

from ninja import Router
from ninja import Schema
from ninja.security import SessionAuth

from llm_lab.docs import services

router = Router(tags=["docs"])

_session = SessionAuth()


class DocNodeOut(Schema):
    slug: str
    title: str
    children: list[DocNodeOut] = []


DocNodeOut.model_rebuild()


class DocPageOut(Schema):
    slug: str
    title: str
    html: str
    toc: str
    raw: str
    last_modified: float


class DocSearchResult(Schema):
    slug: str
    title: str
    snippet: str
    score: int


@router.get("/tree", response=list[DocNodeOut], auth=_session)
def get_tree(request):
    return services.list_docs()


@router.get("/search", response=list[DocSearchResult], auth=_session)
def search(request, q: str = ""):
    return services.search_docs(q)


@router.get("/page", response=DocPageOut | None, auth=_session)
def get_page(request, slug: str):
    return services.get_doc(slug)
