"""File-tree template renderer driven by ``template.yaml`` manifests."""

from __future__ import annotations

import json
import logging
import re
import shutil
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment
from jinja2 import StrictUndefined

from llm_lab.runtime.services.scaffolding_engine.hooks import HOOKS

logger = logging.getLogger(__name__)

_TEMPLATES_ROOT = Path(__file__).resolve().parent.parent.parent / "scaffolding"

_NODE_BUILTINS = frozenset({
    "fs", "path", "url", "http", "https", "stream", "crypto", "os",
    "child_process", "util", "events", "buffer", "process",
})


def _empty_frontend_placeholder(slug: str) -> str:
    """Visible banner shipped when the generation job produced no frontend
    code — surfaces the silent failure mode in the rendered app itself."""
    msg = (
        f"Generation produced no frontend code for the '{slug}' template. "
        "Re-run the generation job or pick a model that emits frontend code."
    )
    if slug.startswith("vue"):
        return (
            "<template>\n"
            "  <div style=\"font-family:system-ui;padding:2rem;"
            "background:#fee;color:#900;border:2px solid #c00;\">\n"
            f"    <h1>⚠ No frontend code</h1>\n    <p>{msg}</p>\n"
            "  </div>\n</template>\n"
        )
    # Default: React JSX.
    return (
        "import React from 'react';\n"
        "export default function App() {\n"
        "  return (\n"
        "    <div style={{fontFamily:'system-ui',padding:'2rem',"
        "background:'#fee',color:'#900',border:'2px solid #c00'}}>\n"
        "      <h1>⚠ No frontend code</h1>\n"
        f"      <p>{msg}</p>\n"
        "    </div>\n  );\n}\n"
    )


def _empty_backend_placeholder(slug: str) -> str:
    """Minimal Flask app that returns a 503 with an explanation, so the
    /api/health endpoint exists but every other path reports the issue."""
    msg = (
        f"Generation produced no backend code for the '{slug}' template."
    )
    return (
        "from flask import Flask, jsonify\n"
        "app = Flask(__name__)\n\n"
        "@app.route('/api/health')\n"
        "def health():\n"
        "    return jsonify({'status':'degraded','reason':"
        f"{msg!r}}}), 503\n\n"
        "@app.errorhandler(404)\n"
        "def _nf(e):\n"
        "    return jsonify({'error':'no backend code generated',"
        f"'detail':{msg!r}}}), 503\n\n"
        "if __name__ == '__main__':\n"
        "    app.run(host='0.0.0.0', port=5000)\n"
    )


class TemplateNotFoundError(LookupError):
    """Raised when a template slug doesn't exist on disk."""


@dataclass
class _Manifest:
    slug: str
    display_name: str
    description: str = ""
    backend: dict[str, Any] = field(default_factory=dict)
    frontend: dict[str, Any] | None = None
    hooks: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class RenderContext:
    """Inputs for one render."""

    slug: str
    dest: Path
    backend_code: str = ""
    frontend_code: str = ""
    backend_deps: list[str] = field(default_factory=list)
    frontend_deps: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


def available_templates() -> list[str]:
    """Return slugs that exist under ``scaffolding/`` with a manifest."""
    if not _TEMPLATES_ROOT.is_dir():
        return []
    return sorted(
        d.name for d in _TEMPLATES_ROOT.iterdir()
        if d.is_dir() and (d / "template.yaml").is_file()
    )


def load_template(slug: str) -> _Manifest:
    root = _TEMPLATES_ROOT / slug
    manifest_path = root / "template.yaml"
    if not manifest_path.is_file():
        raise TemplateNotFoundError(f"template '{slug}' not found at {root}")
    data = yaml.safe_load(manifest_path.read_text()) or {}
    return _Manifest(
        slug=data.get("slug", slug),
        display_name=data.get("display_name", slug),
        description=data.get("description", ""),
        backend=data.get("backend") or {},
        frontend=data.get("frontend"),
        hooks=data.get("hooks") or {},
    )


def render(ctx: RenderContext) -> Path:
    """Render template ``ctx.slug`` into ``ctx.dest`` and return that path."""
    manifest = load_template(ctx.slug)
    src_root = _TEMPLATES_ROOT / ctx.slug
    ctx.dest.mkdir(parents=True, exist_ok=True)

    env = Environment(
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        autoescape=False,  # we're rendering source files, not HTML for browsers
    )

    jinja_vars = {
        "slug": manifest.slug,
        "display_name": manifest.display_name,
        **(ctx.extra or {}),
    }

    for src_file in sorted(src_root.rglob("*")):
        if src_file.is_dir():
            continue
        rel = src_file.relative_to(src_root)
        if rel.parts and rel.parts[0] == "template.yaml":
            continue
        if rel.name == "template.yaml":
            continue

        if src_file.suffix == ".j2":
            out_rel = rel.with_suffix("")
            target = ctx.dest / out_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            tmpl = env.from_string(src_file.read_text())
            target.write_text(tmpl.render(**jinja_vars))
        else:
            target = ctx.dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, target)

    # Inject LLM-generated code into the declared entry points. If the LLM
    # returned nothing for an entry the manifest says exists, write a clearly
    # visible placeholder rather than silently shipping the scaffold's
    # static stub — otherwise the user gets a "blank app" with no signal
    # in the build log that anything went wrong.
    backend_entry = manifest.backend.get("entry")
    if backend_entry:
        be_path = ctx.dest / backend_entry
        if ctx.backend_code:
            be_path.write_text(ctx.backend_code)
        elif not be_path.exists() or be_path.read_text().strip() == "":
            be_path.parent.mkdir(parents=True, exist_ok=True)
            be_path.write_text(_empty_backend_placeholder(manifest.slug))

    if manifest.frontend:
        frontend_entry = manifest.frontend.get("entry")
        if frontend_entry:
            fe_path = ctx.dest / frontend_entry
            if ctx.frontend_code:
                fe_path.write_text(ctx.frontend_code)
            else:
                # Overwrite any static placeholder (e.g. the scaffold's
                # "Scaffolded app placeholder" component) with a banner so
                # the user can see at a glance that generation produced no
                # frontend_code for this job.
                fe_path.parent.mkdir(parents=True, exist_ok=True)
                fe_path.write_text(_empty_frontend_placeholder(manifest.slug))

    # Merge requirements.txt with discovered backend deps.
    req_rel = manifest.backend.get("requirements_path", "backend/requirements.txt")
    baseline_reqs = tuple(manifest.backend.get("baseline_requirements") or ())
    req_path = ctx.dest / req_rel
    if baseline_reqs or ctx.backend_deps:
        existing: list[str] = []
        if req_path.exists():
            existing = [
                line.strip() for line in req_path.read_text().splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        merged = _merge_requirements(baseline_reqs, existing, ctx.backend_deps)
        req_path.parent.mkdir(parents=True, exist_ok=True)
        req_path.write_text(merged)

    # Merge package.json with discovered frontend deps.
    if manifest.frontend:
        pkg_rel = manifest.frontend.get("package_json_path", "frontend/package.json")
        pkg_path = ctx.dest / pkg_rel
        if pkg_path.exists():
            discovered = _extract_js_imports(
                (ctx.dest / manifest.frontend["entry"]).read_text()
                if manifest.frontend.get("entry") and (ctx.dest / manifest.frontend["entry"]).exists()
                else "",
            )
            merged_pkg = _merge_package_json(
                pkg_path.read_text(),
                manifest.frontend.get("baseline_dependencies") or {},
                manifest.frontend.get("baseline_dev_dependencies") or {},
                discovered + list(ctx.frontend_deps),
            )
            pkg_path.write_text(merged_pkg)

    # Run post-render hooks.
    for hook_name in manifest.hooks.get("post_render") or []:
        hook = HOOKS.get(hook_name)
        if hook is None:
            logger.warning("scaffolding: unknown hook '%s' for template %s", hook_name, manifest.slug)
            continue
        try:
            hook(ctx.dest, manifest=manifest, context=ctx)
        except Exception as exc:  # noqa: BLE001
            logger.warning("scaffolding: hook %s raised %s", hook_name, exc)

    return ctx.dest


def _spec_name(spec: str) -> str:
    return re.split(r"[<>=!~\[ ]", spec.strip(), maxsplit=1)[0].lower()


def _merge_requirements(
    baseline: tuple[str, ...],
    existing: list[str],
    discovered: list[str],
) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for source in (baseline, existing, discovered):
        for spec in source:
            spec = spec.strip()
            if not spec or spec.startswith("#"):
                continue
            name = _spec_name(spec)
            if not name or name in seen:
                continue
            seen.add(name)
            out.append(spec)
    return "\n".join(out) + "\n"


def _extract_js_imports(code: str) -> list[str]:
    """Return non-relative npm package names imported from *code*."""
    if not code:
        return []
    pattern = re.compile(
        r"""(?:^|\n)\s*(?:import|export)\s+
            (?:[^'"`;]*?\sfrom\s+)?
            ['"]([^'"\n]+)['"]""",
        re.VERBOSE,
    )
    pkgs: set[str] = set()
    for m in pattern.finditer(code):
        spec = m.group(1).strip()
        if not spec or spec.startswith((".", "/")):
            continue
        if spec.startswith("@"):
            parts = spec.split("/", 2)
            pkg = "/".join(parts[:2]) if len(parts) >= 2 else spec
        else:
            pkg = spec.split("/", 1)[0]
        if pkg in _NODE_BUILTINS:
            continue
        pkgs.add(pkg)
    return sorted(pkgs)


def _merge_package_json(
    existing_text: str,
    baseline_deps: dict[str, str],
    baseline_dev_deps: dict[str, str],
    discovered: list[str],
) -> str:
    try:
        data = json.loads(existing_text)
    except Exception:  # noqa: BLE001
        data = {}
    deps = dict(data.get("dependencies") or {})
    dev_deps = dict(data.get("devDependencies") or {})
    for name, ver in baseline_deps.items():
        deps.setdefault(name, ver)
    for name, ver in baseline_dev_deps.items():
        dev_deps.setdefault(name, ver)
    for pkg in discovered:
        if pkg in deps or pkg in dev_deps:
            continue
        deps[pkg] = "*"
    data["dependencies"] = dict(sorted(deps.items()))
    data["devDependencies"] = dict(sorted(dev_deps.items()))
    return json.dumps(data, indent=2) + "\n"
