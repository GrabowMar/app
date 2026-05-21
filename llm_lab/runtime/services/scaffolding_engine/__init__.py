"""Scaffolding engine: render file-tree templates into a buildable Docker context.

Each template lives under ``llm_lab/runtime/scaffolding/<slug>/`` with a
``template.yaml`` manifest. Files ending in ``.j2`` are rendered through Jinja2
(the ``.j2`` suffix is dropped). All other files are copied verbatim.

The manifest declares baseline backend/frontend dependencies, which generated
artifact maps to which file (so the LLM's output replaces the placeholder), and
optional post-render hooks (registered Python callables).

Public surface:

* :func:`available_templates` — list discoverable template slugs.
* :func:`render` — build a single job into ``dest``.
"""

from llm_lab.runtime.services.scaffolding_engine.engine import RenderContext
from llm_lab.runtime.services.scaffolding_engine.engine import TemplateNotFoundError
from llm_lab.runtime.services.scaffolding_engine.engine import available_templates
from llm_lab.runtime.services.scaffolding_engine.engine import load_template
from llm_lab.runtime.services.scaffolding_engine.engine import render
from llm_lab.runtime.services.scaffolding_engine.hooks import HOOKS
from llm_lab.runtime.services.scaffolding_engine.hooks import register_hook

__all__ = [
    "HOOKS",
    "RenderContext",
    "TemplateNotFoundError",
    "available_templates",
    "load_template",
    "register_hook",
    "render",
]
