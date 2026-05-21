"""Scaffolding façade.

The actual rendering lives in :mod:`llm_lab.runtime.services.scaffolding_engine`
which walks a per-stack file tree under ``llm_lab/runtime/scaffolding/<slug>/``
and renders ``.j2`` files through Jinja2.

This module keeps the historical public API (``prepare_build_dir``) so the
container build path doesn't need to know about the engine.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from llm_lab.generation.services.code_parser import extract_frontend_code
from llm_lab.generation.services.code_parser import extract_python_code
from llm_lab.runtime.services.scaffolding_engine import RenderContext
from llm_lab.runtime.services.scaffolding_engine import TemplateNotFoundError
from llm_lab.runtime.services.scaffolding_engine import available_templates
from llm_lab.runtime.services.scaffolding_engine import render

if TYPE_CHECKING:
    from llm_lab.generation.models import GenerationJob

__all__ = ["available_templates", "prepare_build_dir"]

_DEFAULT_TEMPLATE = "generic-python"


def prepare_build_dir(
    job: GenerationJob,
    dest_path: Path,
    *,
    app_base: str = "/",  # noqa: ARG001 - kept for backward compat; ignored by new templates
) -> Path:
    """Render a full Docker build context for *job* into *dest_path*.

    The legacy ``app_base`` argument is retained for callers but is no longer
    threaded into generated SPAs — they now detect their mount point at
    runtime via ``window.location`` and the proxy-injected ``<base href>``.
    """
    dest_path.mkdir(parents=True, exist_ok=True)

    slug = _resolve_template(job)
    result = job.result_data or {}
    backend_raw: str = result.get("backend_code", "") or ""
    frontend_raw: str = result.get("frontend_code", "") or ""
    backend_code = (
        extract_python_code(backend_raw) or backend_raw.strip()
    )
    frontend_code = extract_frontend_code(frontend_raw) or frontend_raw.strip()
    frontend_code = _sanitize_frontend_code(frontend_code)
    backend_code = _sanitize_backend_code(backend_code)
    backend_deps: list[str] = list(result.get("backend_dependencies", []) or [])
    frontend_deps: list[str] = list(result.get("frontend_dependencies", []) or [])

    ctx = RenderContext(
        slug=slug,
        dest=dest_path,
        backend_code=backend_code,
        frontend_code=frontend_code,
        backend_deps=backend_deps,
        frontend_deps=frontend_deps,
        extra={"job_id": str(job.id) if getattr(job, "id", None) else ""},
    )
    return render(ctx)


def _resolve_template(job: GenerationJob) -> str:
    candidate = (
        job.scaffolding_template.slug
        if getattr(job, "scaffolding_template", None) and job.scaffolding_template
        else _DEFAULT_TEMPLATE
    )
    if candidate not in available_templates():
        return _DEFAULT_TEMPLATE
    return candidate


# Re-export for callers that still import the symbol from this module.
__all__ += ["TemplateNotFoundError"]


_LOCALHOST_URL_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?")

# Matches top-level declarations whose identifier we want to track for
# duplicate detection. We intentionally only handle the subset of forms LLMs
# commonly emit at module scope:
#   const Foo = ...
#   let Foo = ...
#   function Foo (...) { ... }
#   class Foo { ... }
#   const Foo: SomeType = ...
# Indented matches are skipped because they're inside another block (so JS
# scoping makes them legal).
_JS_TOPLEVEL_DECL_RE = re.compile(
    r"^(?P<kw>const|let|var|function|class)\s+(?P<name>[A-Za-z_$][\w$]*)\b",
)


def _sanitize_frontend_code(code: str) -> str:
    """Strip hardcoded ``http://localhost:<port>`` URLs from LLM-generated SPA code.

    The container is served from ``/app/<id>/`` via the reverse proxy, so any
    absolute reference back to ``localhost`` would (a) bypass session auth and
    (b) point a deployed client at its own machine. Replacing the prefix with
    the empty string turns ``axios.create({baseURL: 'http://localhost:8000'})``
    into ``axios.create({baseURL: ''})`` — axios then treats subsequent calls
    as relative, which the nginx ``location /api/`` block proxies to Flask.
    """
    if not code:
        return code
    code = _LOCALHOST_URL_RE.sub("", code)
    code = _dedupe_top_level_js_decls(code)
    code = _auto_import_missing_named_exports(code)
    return code


# Mapping from well-known npm package -> set of named exports that LLMs
# frequently *use* (e.g. ``<Navigate to="/" />``) but forget to import. We
# detect uses and patch the existing import statement (or insert a new one
# right after the last top-level ``import`` line). This is a guardrail
# against LLM "missing import" hallucinations that survive bundling because
# Rollup only fails on duplicate decls, not undeclared references.
_AUTO_IMPORT_MAP: dict[str, frozenset[str]] = {
    "react-router-dom": frozenset({
        "Navigate", "Outlet", "NavLink", "useLocation", "useSearchParams",
        "useMatch", "useResolvedPath", "createBrowserRouter", "RouterProvider",
        "MemoryRouter", "HashRouter", "BrowserRouter",
    }),
    "react": frozenset({
        "useState", "useEffect", "useCallback", "useMemo", "useRef",
        "useContext", "useReducer", "useLayoutEffect", "createContext",
        "Fragment", "forwardRef", "memo", "Suspense", "lazy",
    }),
    "react-hot-toast": frozenset({"Toaster", "ToastBar", "useToaster"}),
    "date-fns": frozenset({
        "format", "formatDistance", "formatDistanceToNow", "formatRelative",
        "parseISO", "parse", "addDays", "subDays", "addMonths", "subMonths",
        "isAfter", "isBefore", "isToday", "startOfDay", "endOfDay",
        "differenceInDays", "differenceInHours", "differenceInMinutes",
    }),
    "framer-motion": frozenset({"motion", "AnimatePresence", "useAnimation"}),
}

# Packages whose primary import is a default export. We only splice these in
# when the bare identifier is used AND no existing import for the package
# exists in the source. The package MUST be in the template's baseline deps
# (handled by the template authors) or auto-import would create a missing-
# package build error.
_AUTO_DEFAULT_IMPORT_MAP: dict[str, str] = {
    "clsx": "clsx",
    "classnames": "classnames",
    "react-hot-toast": "toast",
}


def _auto_import_missing_named_exports(code: str) -> str:
    """Add named imports the LLM forgot for well-known packages.

    Example: source uses ``<Navigate to="/" />`` but the
    ``react-router-dom`` import line lacks ``Navigate`` — we add it.
    Only operates on names listed in ``_AUTO_IMPORT_MAP`` to keep the
    rewrite predictable and avoid false positives. Existing import bindings
    are detected (including aliases like ``X as Y``) so we never duplicate
    them. If no existing import for the package exists, we insert one right
    after the last top-level import line.
    """
    if not code:
        return code

    import_re = re.compile(
        r"^import\s+(?P<spec>[^'\"`]+?)\s+from\s+['\"](?P<pkg>[^'\"]+)['\"]\s*;?[ \t]*$",
        re.MULTILINE,
    )
    spec_token_re = re.compile(r"\b([A-Za-z_$][\w$]*)(?:\s+as\s+([A-Za-z_$][\w$]*))?")

    # Catalog existing imports (locally-bound names per package) and the
    # locations of each `import { ... } from 'pkg'` statement we can extend.
    existing: dict[str, set[str]] = {}
    statement_for_pkg: dict[str, re.Match[str]] = {}
    for m in import_re.finditer(code):
        pkg = m.group("pkg")
        existing.setdefault(pkg, set())
        # Track LAST import statement per pkg (some LLMs split imports).
        statement_for_pkg[pkg] = m
        for tok in spec_token_re.finditer(m.group("spec")):
            local = tok.group(2) or tok.group(1)
            if local in {"as", "from", "default"}:
                continue
            existing[pkg].add(local)

    # All locally-bound identifiers from any package + top-level decls — used
    # to skip names that are already accounted for in some way.
    bound_all: set[str] = set()
    for names in existing.values():
        bound_all.update(names)
    for m in re.finditer(
        r"^(?:export\s+(?:default\s+)?)?(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)\b",
        code,
        re.MULTILINE,
    ):
        bound_all.add(m.group(1))

    # For each known package, find names that the source *uses* but hasn't
    # bound. "Used" = identifier appears as `<Name`, `</Name`, or `Name(`.
    additions: dict[str, list[str]] = {}
    for pkg, candidates in _AUTO_IMPORT_MAP.items():
        missing: list[str] = []
        already = existing.get(pkg, set())
        for name in candidates:
            if name in already or name in bound_all:
                continue
            usage = re.compile(rf"(?:<{name}\b|</{name}\b|\b{name}\s*\()")
            if usage.search(code):
                missing.append(name)
        if missing:
            additions[pkg] = sorted(missing)

    # Apply named-import additions. For packages with an existing import
    # statement, splice the names into the `{ ... }` block; if no brace block
    # exists yet, add one. For packages without any import, insert a new
    # import after the last `import` line.
    new_code = code
    for pkg, names in additions.items():
        if pkg in statement_for_pkg:
            stmt = statement_for_pkg[pkg]
            spec = stmt.group("spec")
            new_spec = _splice_named_imports(spec, names)
            # Replace just that import line. Re-find the statement in
            # new_code since prior edits may have shifted offsets.
            old_line = stmt.group(0)
            new_line = old_line.replace(spec, new_spec, 1)
            new_code = new_code.replace(old_line, new_line, 1)
        else:
            new_import = f"import {{ {', '.join(names)} }} from '{pkg}';\n"
            # Insert after the last `import` statement, or at start.
            last = None
            for m in import_re.finditer(new_code):
                last = m
            if last:
                insert_at = last.end()
                # Ensure we land at end-of-line.
                if insert_at < len(new_code) and new_code[insert_at] != "\n":
                    new_code = new_code[:insert_at] + "\n" + new_import + new_code[insert_at:]
                else:
                    new_code = new_code[: insert_at + 1] + new_import + new_code[insert_at + 1:]
            else:
                new_code = new_import + new_code

    # --- default imports: only add when no import for the package exists ---
    # Rescan the (possibly-edited) code so we don't double-add.
    existing_pkgs = {m.group("pkg") for m in import_re.finditer(new_code)}
    for pkg, default_name in _AUTO_DEFAULT_IMPORT_MAP.items():
        if pkg in existing_pkgs:
            continue
        if default_name in bound_all:
            continue
        usage = re.compile(rf"(?:<{default_name}\b|</{default_name}\b|\b{default_name}\s*\()")
        if not usage.search(new_code):
            continue
        new_import = f"import {default_name} from '{pkg}';\n"
        last = None
        for m in import_re.finditer(new_code):
            last = m
        if last:
            insert_at = last.end()
            if insert_at < len(new_code) and new_code[insert_at] != "\n":
                new_code = new_code[:insert_at] + "\n" + new_import + new_code[insert_at:]
            else:
                new_code = new_code[: insert_at + 1] + new_import + new_code[insert_at + 1:]
        else:
            new_code = new_import + new_code
        bound_all.add(default_name)

    return new_code


def _splice_named_imports(spec: str, add_names: list[str]) -> str:
    """Insert *add_names* into an import specifier's ``{ ... }`` block.

    If no named-imports block exists, append one to the specifier. Preserves
    a default import on the left if present.
    """
    brace_match = re.search(r"\{([^}]*)\}", spec)
    if brace_match:
        block = brace_match.group(1).rstrip()
        sep = ", " if block.strip() else ""
        new_block = f"{block}{sep}{', '.join(add_names)}"
        return spec[: brace_match.start()] + "{ " + new_block + " }" + spec[brace_match.end():]
    # No brace block. Keep whatever default/namespace import is there, then
    # append a named block.
    spec = spec.rstrip().rstrip(",")
    joiner = ", " if spec else ""
    return f"{spec}{joiner}{{ {', '.join(add_names)} }}"


def _dedupe_top_level_js_decls(code: str) -> str:
    """Resolve duplicate top-level bindings so esbuild / Rollup don't choke.

    Two LLM hallucinations regularly trigger ``SyntaxError: the symbol "Foo"
    has already been declared``:

    1. The same component is declared twice (``const Navigation = ...`` then
       a later ``const Navigation = ...``, often a stub + a refined version).
    2. A component is declared with the same name as an icon imported from
       a UI library (``import { Navigation } from 'lucide-react'`` collides
       with ``const Navigation = ...``).

    Strategy:

    * For (1): keep the first declaration intact; rename later duplicates to
      ``Foo__dup1`` etc. (dead code, tree-shaken). References still resolve
      to the first definition.
    * For (2): rewrite the import to alias the conflicting binding to
      ``Foo_imp``. The local component wins, which matches user intent (the
      icon is usually over-imported and the component is the one actually
      rendered). The icon import becomes ``Foo as Foo_imp`` — if nothing
      references ``Foo_imp`` it's tree-shaken.

    We deliberately do NOT rename references because doing so cheaply and
    safely is impossible without a real JS parser; both choices above leave
    one branch as dead code while keeping the build green.
    """
    # ---- pass 1: collect import bindings + the import block range to rewrite ----
    # An import binding is recorded as: name -> list of (start, end, replacement)
    # for the precise token inside the source so we can alias it later.
    imports: dict[str, list[tuple[int, int]]] = {}
    import_re = re.compile(
        r"^import\s+(?P<spec>[^'\"`]+?)\s+from\s+['\"][^'\"]+['\"]\s*;?[ \t]*$",
        re.MULTILINE,
    )
    spec_token_re = re.compile(r"\b([A-Za-z_$][\w$]*)(?:\s+as\s+([A-Za-z_$][\w$]*))?")

    for stmt in import_re.finditer(code):
        spec_start = stmt.start("spec")
        spec_text = stmt.group("spec")
        # The "spec" may include a default import + a `{ ... }` named block.
        # Walk both parts and record each binding's *local* name + the slice
        # that, if rewritten, would alias it.
        brace_match = re.search(r"\{([^}]*)\}", spec_text)
        scan_targets: list[tuple[int, str]] = []  # (offset_in_spec, text)
        if brace_match:
            named_start = brace_match.start(1)
            scan_targets.append((named_start, brace_match.group(1)))
            pre = spec_text[: brace_match.start()]
            scan_targets.append((0, pre))
        else:
            scan_targets.append((0, spec_text))

        for offset, text in scan_targets:
            for m in spec_token_re.finditer(text):
                name = m.group(1)
                alias = m.group(2)
                if name in {"as", "from", "default"}:
                    continue
                local_name = alias or name
                # Position of the local name in the full source.
                if alias:
                    tok_start = spec_start + offset + m.start(2)
                    tok_end = spec_start + offset + m.end(2)
                else:
                    tok_start = spec_start + offset + m.start(1)
                    tok_end = spec_start + offset + m.end(1)
                imports.setdefault(local_name, []).append((tok_start, tok_end))

    # ---- pass 2: walk declarations line-by-line, register/rename duplicates ----
    seen: dict[str, int] = {name: 1 for name in imports}

    # Build the output incrementally. We need to track byte offsets so import
    # rewrites can be applied as edits on the *original* source.
    edits: list[tuple[int, int, str]] = []  # (start, end, replacement)
    lines = code.splitlines(keepends=True)
    out_lines: list[str] = []

    for line in lines:
        if not line or line[0] in (" ", "\t"):
            out_lines.append(line)
            continue
        stripped = line
        prefix = ""
        for tag in ("export default ", "export "):
            if stripped.startswith(tag):
                prefix = tag
                stripped = stripped[len(tag):]
                break
        m = _JS_TOPLEVEL_DECL_RE.match(stripped)
        if not m:
            out_lines.append(line)
            continue
        name = m.group("name")
        if name not in seen:
            seen[name] = 1
            out_lines.append(line)
            continue

        # Collision. If the previous owner was an import, alias the import and
        # let the local declaration keep its name. Otherwise rename the local.
        if name in imports and imports[name]:
            alias = f"{name}_imp"
            # Guarantee the alias itself doesn't already collide.
            i = 1
            while alias in seen:
                alias = f"{name}_imp{i}"
                i += 1
            for tok_start, tok_end in imports[name]:
                edits.append((tok_start, tok_end, f"{name} as {alias}"))
            seen[alias] = 1
            # Local declaration keeps its name; mark it as the canonical owner
            # so future duplicates of the same name get the __dup treatment.
            seen[name] = 1
            del imports[name]
            out_lines.append(line)
        else:
            seen[name] += 1
            new_name = f"{name}__dup{seen[name] - 1}"
            replaced = stripped.replace(name, new_name, 1)
            out_lines.append(prefix + replaced)

    # If we never edited any imports, the line-based output is the result.
    if not edits:
        return "".join(out_lines)

    # Otherwise re-derive the source: start from the original (so import token
    # positions remain valid), apply import edits, then for the *declaration*
    # changes we re-render via line replacement. We do this by:
    #   1. Applying import edits to the original code by offset (back to front).
    #   2. Then re-running the declaration pass on the patched code — cheaper
    #      than tracking line offsets through the edit list.
    edits.sort(reverse=True)
    patched = code
    for start, end, repl in edits:
        patched = patched[:start] + repl + patched[end:]
    # Now redo declaration dedup on the patched code (imports already aliased
    # so they no longer collide; only true decl-decl duplicates remain).
    return _dedupe_decl_only(patched)


def _dedupe_decl_only(code: str) -> str:
    """Helper: pass-2 dedup but treating imports as non-colliding (already aliased)."""
    seen: dict[str, int] = {}
    lines = code.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        if not line or line[0] in (" ", "\t"):
            out.append(line)
            continue
        stripped = line
        prefix = ""
        for tag in ("export default ", "export "):
            if stripped.startswith(tag):
                prefix = tag
                stripped = stripped[len(tag):]
                break
        m = _JS_TOPLEVEL_DECL_RE.match(stripped)
        if not m:
            out.append(line)
            continue
        name = m.group("name")
        if seen.get(name):
            seen[name] += 1
            new_name = f"{name}__dup{seen[name] - 1}"
            replaced = stripped.replace(name, new_name, 1)
            out.append(prefix + replaced)
        else:
            seen[name] = 1
            out.append(line)
    return "".join(out)


def _parse_import_specifiers(spec: str) -> list[str]:  # kept for tests
    names: list[str] = []
    spec = re.sub(r"/\*.*?\*/", "", spec).strip()
    brace_match = re.search(r"\{([^}]*)\}", spec)
    pre = spec[: brace_match.start()] if brace_match else spec
    named_block = brace_match.group(1) if brace_match else ""
    for token in pre.split(","):
        token = token.strip().rstrip(",").strip()
        if not token:
            continue
        if token.startswith("*"):
            m = re.match(r"\*\s+as\s+([A-Za-z_$][\w$]*)", token)
            if m:
                names.append(m.group(1))
        else:
            m = re.match(r"^([A-Za-z_$][\w$]*)$", token)
            if m:
                names.append(m.group(1))
    for token in named_block.split(","):
        token = token.strip()
        if not token:
            continue
        m = re.match(r"([A-Za-z_$][\w$]*)(?:\s+as\s+([A-Za-z_$][\w$]*))?", token)
        if m:
            names.append(m.group(2) or m.group(1))
    return names


def _sanitize_backend_code(code: str) -> str:
    """Make LLM-generated Flask/FastAPI code more likely to actually boot.

    Three passes (each best-effort, never aborts on its own):

    1. Strip hardcoded ``http://localhost:<port>`` URLs that would leak into
       CORS allow-lists or env defaults.
    2. Add common Flask imports the LLM forgets (``jsonify``, ``request``,
       ``make_response``, ``Response``, ``redirect``, ``send_file``).
    3. Detect duplicate top-level function names (decorator-bound or plain)
       and rename later occurrences to ``foo__dup1`` so Flask's
       ``AssertionError: View function mapping is overwriting an existing
       endpoint`` doesn't kill the worker. We deliberately rename the
       function (Flask uses the function name as the endpoint by default)
       rather than the route — changing the route would silently break the
       frontend's API calls.
    """
    if not code:
        return code
    code = _LOCALHOST_URL_RE.sub("", code)
    code = _auto_import_missing_flask_names(code)
    code = _dedupe_top_level_py_functions(code)
    return code


# Flask names the LLM most commonly uses without importing. Keys are the
# bare identifier; we splice into an existing ``from flask import ...`` line
# if one exists.
_FLASK_AUTO_IMPORTS = (
    "jsonify", "request", "make_response", "redirect", "send_file",
    "send_from_directory", "url_for", "abort", "Response", "stream_with_context",
)


def _auto_import_missing_flask_names(code: str) -> str:
    """If code uses Flask helpers but the import line doesn't include them, add them.

    Only acts when a ``from flask import ...`` line already exists (so we
    know flask is being used) — never invents a new import block to avoid
    false positives in plain-Python templates.
    """
    flask_import_re = re.compile(
        r"^(?P<full>from\s+flask\s+import\s+(?P<names>[^\n#]+?))\s*$",
        re.MULTILINE,
    )
    m = flask_import_re.search(code)
    if not m:
        return code
    existing = {n.strip() for n in m.group("names").split(",") if n.strip()}
    additions: list[str] = []
    for name in _FLASK_AUTO_IMPORTS:
        if name in existing:
            continue
        # Require usage as `name(` or `name.` to avoid matching substrings.
        if re.search(rf"\b{name}\s*[(.]", code):
            additions.append(name)
    if not additions:
        return code
    merged = ", ".join(sorted(existing | set(additions)))
    new_line = f"from flask import {merged}"
    return code[: m.start("full")] + new_line + code[m.end("full"):]


def _dedupe_top_level_py_functions(code: str) -> str:
    """Rename duplicate top-level ``def name(...)`` to ``name__dup1`` etc.

    Walks lines at column 0 only. Functions inside classes / nested scopes
    are unaffected. Renames the def site; references elsewhere are left as
    they were — the renamed copy becomes dead code, which is exactly what
    we want (Flask boots, the LLM's first definition wins).
    """
    def_re = re.compile(r"^def\s+([A-Za-z_]\w*)\s*\(")
    seen: dict[str, int] = {}
    out: list[str] = []
    for line in code.splitlines(keepends=True):
        if not line or line[0] in (" ", "\t"):
            out.append(line)
            continue
        m = def_re.match(line)
        if not m:
            out.append(line)
            continue
        name = m.group(1)
        if name not in seen:
            seen[name] = 1
            out.append(line)
        else:
            seen[name] += 1
            new_name = f"{name}__dup{seen[name] - 1}"
            out.append(line.replace(name, new_name, 1))
    return "".join(out)
