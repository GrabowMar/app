"""Documentation service — walks DOCS_ROOT and renders Markdown files."""

from __future__ import annotations

import os
import re
from pathlib import Path

import markdown as md
from django.conf import settings

DOCS_ROOT: Path = Path(getattr(settings, "DOCS_ROOT", settings.BASE_DIR / "docs"))

_MD = md.Markdown(
    extensions=[
        "fenced_code",
        "tables",
        "toc",
        "codehilite",
        "attr_list",
    ],
    extension_configs={
        "toc": {"permalink": True},
        "codehilite": {"guess_lang": False, "css_class": "highlight"},
    },
)


def _reset_md() -> md.Markdown:
    """Return a fresh Markdown instance (reset converts reuse errors)."""
    _MD.reset()
    return _MD


def _slug_from_path(path: Path) -> str:
    rel = path.relative_to(DOCS_ROOT)
    return str(rel.with_suffix("")).replace(os.sep, "/")


def _title_from_file(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8")
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except OSError:
        pass
    return path.stem.replace("-", " ").replace("_", " ").title()


def _build_tree(root: Path) -> list[dict]:
    """Recursively build a tree of {slug, title, path, children}."""
    items: list[dict] = []
    try:
        entries = sorted(root.iterdir(), key=lambda p: (p.is_dir(), p.name.lower()))
    except OSError:
        return items
    for entry in entries:
        if entry.name.startswith(".") or entry.name.startswith("_"):
            continue
        if entry.is_dir():
            children = _build_tree(entry)
            if children:
                items.append(
                    {
                        "slug": _slug_from_path(entry),
                        "title": entry.name.replace("-", " ").replace("_", " ").title(),
                        "path": str(entry),
                        "children": children,
                    },
                )
        elif entry.suffix.lower() == ".md":
            items.append(
                {
                    "slug": _slug_from_path(entry),
                    "title": _title_from_file(entry),
                    "path": str(entry),
                    "children": [],
                },
            )
    return items


def list_docs() -> list[dict]:
    """Walk DOCS_ROOT and return a nested tree of Markdown files."""
    return _build_tree(DOCS_ROOT)


def sanitize_slug(slug: str) -> str | None:
    """Return None if slug is unsafe (path traversal / absolute)."""
    if not slug:
        return None
    if slug.startswith("/"):
        return None
    parts = slug.replace("\\", "/").split("/")
    for part in parts:
        if part in ("", ".", ".."):
            return None
    return slug


def get_doc(slug: str) -> dict | None:
    """Render a single doc. Returns None if not found or slug is unsafe."""
    clean = sanitize_slug(slug)
    if clean is None:
        return None
    path = DOCS_ROOT / Path(*clean.split("/"))
    path = path.with_suffix(".md")
    if not path.exists() or not path.is_file():
        return None
    # Make sure the resolved path stays inside DOCS_ROOT
    try:
        path.resolve().relative_to(DOCS_ROOT.resolve())
    except ValueError:
        return None

    raw = path.read_text(encoding="utf-8")
    converter = _reset_md()
    html = converter.convert(raw)
    toc = getattr(converter, "toc", "")
    toc_tokens = getattr(converter, "toc_tokens", [])

    last_modified = path.stat().st_mtime

    return {
        "slug": clean,
        "title": _title_from_file(path),
        "html": html,
        "toc": toc,
        "toc_tokens": toc_tokens,
        "raw": raw,
        "last_modified": last_modified,
    }


def _iter_md_files() -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(DOCS_ROOT):
        dirnames[:] = [
            d
            for d in dirnames
            if not d.startswith(".") and not d.startswith("_")
        ]
        files.extend(
            Path(dirpath) / fn
            for fn in filenames
            if fn.lower().endswith(".md") and not fn.startswith(".")
        )
    return files


def search_docs(query: str) -> list[dict]:
    """Naive full-text search across all Markdown files."""
    if not query or not query.strip():
        return []
    terms = [t.lower() for t in query.strip().split() if t]
    results: list[dict] = []
    for path in _iter_md_files():
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        lower = content.lower()
        score = sum(lower.count(t) for t in terms)
        if score == 0:
            continue
        # Build a snippet around the first match
        first_idx = lower.find(terms[0])
        start = max(0, first_idx - 60)
        end = min(len(content), first_idx + 120)
        snippet = content[start:end].replace("\n", " ").strip()
        if start > 0:
            snippet = "…" + snippet
        if end < len(content):
            snippet = snippet + "…"
        slug = _slug_from_path(path)
        results.append(
            {
                "slug": slug,
                "title": _title_from_file(path),
                "snippet": snippet,
                "score": score,
            },
        )
    results.sort(key=lambda r: r["score"], reverse=True)
    return results
