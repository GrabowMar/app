"""Tests for the scaffolding façade + engine integration.

Exercises ``prepare_build_dir`` and engine internals against tmp_path. No Docker.
"""

from __future__ import annotations

import json

import pytest

from llm_lab.generation.tests.factories import GenerationJobFactory
from llm_lab.generation.tests.factories import ScaffoldingTemplateFactory
from llm_lab.runtime.services.scaffolding import _sanitize_frontend_code
from llm_lab.runtime.services.scaffolding import prepare_build_dir
from llm_lab.runtime.services.scaffolding_engine.engine import _extract_js_imports
from llm_lab.runtime.services.scaffolding_engine.engine import _merge_package_json
from llm_lab.runtime.services.scaffolding_engine.engine import _merge_requirements

pytestmark = pytest.mark.django_db


def _job(slug: str = "react-flask", **result_overrides):
    template = ScaffoldingTemplateFactory(slug=slug, name=slug)
    result_data = {
        "backend_code": (
            "from flask import Flask, jsonify\n"
            "app = Flask(__name__)\n"
            "@app.route('/api/health')\n"
            "def health():\n"
            "    return jsonify({'ok': True})\n"
        ),
        "frontend_code": (
            "import React from 'react';\n"
            "import { Routes, Route } from 'react-router-dom';\n"
            "import axios from 'axios';\n"
            "import './styles.css';\n"
            "export default function App() { return <div>hi</div>; }\n"
        ),
        "backend_dependencies": ["flask-sqlalchemy", "bcrypt", "pyjwt"],
    }
    result_data.update(result_overrides)
    return GenerationJobFactory(
        mode="scaffolding",
        scaffolding_template=template,
        result_data=result_data,
        status="completed",
    )


class TestMergeRequirements:
    def test_dedupes_case_insensitively(self):
        body = _merge_requirements(("flask>=3.0", "Flask-CORS"), ["flask"], ["bcrypt"])
        names = [
            line.split("=")[0].split("<")[0].split(">")[0].lower()
            for line in body.strip().splitlines()
        ]
        assert "flask" in names
        assert "flask-cors" in names
        assert "bcrypt" in names
        assert names.count("flask") == 1


class TestExtractJsImports:
    def test_skips_relative_and_builtins(self):
        code = (
            "import React from 'react';\n"
            "import axios from 'axios';\n"
            "import { Routes } from 'react-router-dom';\n"
            "import './local.css';\n"
            "import foo from '../foo';\n"
            "import bar from 'fs';\n"
            "import { x } from '@scope/pkg/sub';\n"
        )
        result = _extract_js_imports(code)
        assert "react" in result
        assert "axios" in result
        assert "react-router-dom" in result
        assert "@scope/pkg" in result
        assert "fs" not in result
        assert "./local.css" not in result


class TestMergePackageJson:
    def test_baseline_and_discovered(self):
        baseline_deps = {"react": "^18.3.1", "react-dom": "^18.3.1"}
        baseline_dev = {"vite": "^5.4.0"}
        existing = '{"name":"app","dependencies":{},"devDependencies":{}}'
        body = json.loads(
            _merge_package_json(existing, baseline_deps, baseline_dev, ["axios", "lucide-react"])
        )
        assert body["dependencies"]["react"].startswith("^18")
        assert body["dependencies"]["axios"] == "*"
        assert body["dependencies"]["lucide-react"] == "*"
        assert body["devDependencies"]["vite"].startswith("^5")


class TestPrepareBuildDirReactFlask:
    def test_writes_full_build_context(self, tmp_path):
        job = _job("react-flask")
        prepare_build_dir(job, tmp_path)

        assert (tmp_path / "Dockerfile").exists()
        assert "supervisord" in (tmp_path / "Dockerfile").read_text()
        assert (tmp_path / "supervisord.conf").exists()
        assert (tmp_path / "nginx.conf").exists()

        backend_req = (tmp_path / "backend" / "requirements.txt").read_text()
        assert "flask" in backend_req.lower()
        assert "gunicorn" in backend_req.lower()
        assert "flask-sqlalchemy" in backend_req.lower()
        assert "bcrypt" in backend_req.lower()
        app_py = (tmp_path / "backend" / "app.py").read_text()
        assert app_py.startswith("from flask")

        frontend = tmp_path / "frontend"
        assert (frontend / "index.html").exists()
        assert (frontend / "vite.config.js").exists()
        assert (frontend / "src" / "App.jsx").exists()
        main_jsx = (frontend / "src" / "main.jsx").read_text()
        assert "createRoot" in main_jsx

        package = json.loads((frontend / "package.json").read_text())
        assert "react" in package["dependencies"]
        assert "axios" in package["dependencies"]
        assert "vite" in package["devDependencies"]

    def test_no_app_base_baked_in(self, tmp_path):
        """SPAs no longer encode the path-prefix; the proxy injects <base href>."""
        job = _job("react-flask")
        prepare_build_dir(job, tmp_path, app_base="/app/abcd1234/")

        vite = (tmp_path / "frontend" / "vite.config.js").read_text()
        assert "/app/abcd1234/" not in vite
        index_html = (tmp_path / "frontend" / "index.html").read_text()
        assert "__APP_BASE__" not in index_html or "/app/abcd1234" not in index_html

    def test_handles_missing_frontend_code(self, tmp_path):
        job = _job("react-flask", frontend_code="")
        prepare_build_dir(job, tmp_path)
        app_jsx = (tmp_path / "frontend" / "src" / "App.jsx").read_text()
        assert app_jsx  # template placeholder kept

    def test_handles_missing_backend_code(self, tmp_path):
        job = _job("react-flask", backend_code="")
        prepare_build_dir(job, tmp_path)
        app_py = (tmp_path / "backend" / "app.py").read_text()
        assert "Flask" in app_py or "flask" in app_py


class TestOtherTemplates:
    @pytest.mark.parametrize("slug", ["vue-flask", "react-fastapi", "generic-python", "static-html"])
    def test_renders_without_error(self, tmp_path, slug):
        job = _job(slug)
        prepare_build_dir(job, tmp_path)
        assert (tmp_path / "Dockerfile").exists()


class TestSanitizeFrontendCode:
    def test_strips_localhost_urls(self):
        src = (
            "const api = axios.create({\n"
            "  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',\n"
            "});\n"
            "fetch('http://127.0.0.1:5000/api/x');\n"
            "fetch('https://localhost/api/y');\n"
        )
        out = _sanitize_frontend_code(src)
        assert "localhost" not in out
        assert "127.0.0.1" not in out
        assert "baseURL: import.meta.env.VITE_API_BASE_URL || ''" in out
        assert "fetch('/api/x')" in out
        assert "fetch('/api/y')" in out

    def test_full_pipeline_strips_in_app_jsx(self, tmp_path):
        bad = (
            "import React from 'react';\n"
            "import axios from 'axios';\n"
            "const api = axios.create({ baseURL: 'http://localhost:8000' });\n"
            "export default function App() { return <div>x</div>; }\n"
        )
        job = _job("react-flask", frontend_code=bad)
        prepare_build_dir(job, tmp_path)
        app_jsx = (tmp_path / "frontend" / "src" / "App.jsx").read_text()
        assert "localhost" not in app_jsx
        assert "baseURL: ''" in app_jsx


class TestDedupeTopLevelJsDecls:
    def test_renames_duplicate_const(self):
        from llm_lab.runtime.services.scaffolding import _dedupe_top_level_js_decls

        src = (
            "const Navigation = () => <div>v1</div>;\n"
            "const Navigation = ({user}) => <div>v2</div>;\n"
        )
        out = _dedupe_top_level_js_decls(src)
        assert out.count("const Navigation =") == 1
        assert "const Navigation__dup1 =" in out

    def test_keeps_nested_scope_intact(self):
        from llm_lab.runtime.services.scaffolding import _dedupe_top_level_js_decls

        src = (
            "function outer() {\n"
            "  const x = 1;\n"
            "}\n"
            "function inner() {\n"
            "  const x = 2;\n"
            "}\n"
        )
        # Both `const x` are indented → must not be touched.
        out = _dedupe_top_level_js_decls(src)
        assert out.count("const x = 1") == 1
        assert out.count("const x = 2") == 1

    def test_handles_function_and_class(self):
        from llm_lab.runtime.services.scaffolding import _dedupe_top_level_js_decls

        src = (
            "function Foo() {}\n"
            "class Foo { bar() {} }\n"
            "function Foo() { return 2; }\n"
        )
        out = _dedupe_top_level_js_decls(src)
        # First Foo (function) stays; class Foo and second function Foo get renamed.
        assert "function Foo()" in out
        assert "class Foo__dup1" in out
        assert "function Foo__dup2" in out

    def test_handles_export_prefix(self):
        from llm_lab.runtime.services.scaffolding import _dedupe_top_level_js_decls

        src = (
            "export const Widget = () => null;\n"
            "export const Widget = () => null;\n"
        )
        out = _dedupe_top_level_js_decls(src)
        assert out.count("export const Widget =") == 1
        assert "export const Widget__dup1 =" in out

    def test_sanitize_pipeline_dedupes(self):
        bad = (
            "import React from 'react';\n"
            "const Navigation = () => null;\n"
            "const Navigation = () => null;\n"
        )
        out = _sanitize_frontend_code(bad)
        assert "const Navigation__dup1" in out


class TestImportDeclConflict:
    def test_aliases_lucide_icon_when_local_component_collides(self):
        from llm_lab.runtime.services.scaffolding import _dedupe_top_level_js_decls

        src = (
            "import React from 'react';\n"
            "import { Home, Navigation, User } from 'lucide-react';\n"
            "const Navigation = () => <nav>x</nav>;\n"
            "export default function App() { return <Navigation />; }\n"
        )
        out = _dedupe_top_level_js_decls(src)
        # The import is aliased, the component keeps its name.
        assert "Navigation as Navigation_imp" in out
        assert "const Navigation =" in out
        assert "<Navigation />" in out

    def test_multiline_import_aliasing(self):
        from llm_lab.runtime.services.scaffolding import _dedupe_top_level_js_decls

        src = (
            "import {\n"
            "  Home,\n"
            "  Navigation,\n"
            "  User,\n"
            "} from 'lucide-react';\n"
            "const Navigation = () => null;\n"
        )
        out = _dedupe_top_level_js_decls(src)
        assert "Navigation as Navigation_imp" in out
        assert "const Navigation =" in out


class TestAutoImportMissing:
    def test_adds_navigate_to_existing_router_import(self):
        from llm_lab.runtime.services.scaffolding import _auto_import_missing_named_exports

        src = (
            "import { Routes, Route, Link, useNavigate } from 'react-router-dom';\n"
            "const App = () => <Route element={<Navigate to='/' replace />} />;\n"
        )
        out = _auto_import_missing_named_exports(src)
        assert "Navigate" in out
        # Existing import line was extended, not duplicated.
        assert out.count("from 'react-router-dom'") == 1

    def test_does_not_duplicate_already_imported(self):
        from llm_lab.runtime.services.scaffolding import _auto_import_missing_named_exports

        src = (
            "import { Routes, Navigate } from 'react-router-dom';\n"
            "const App = () => <Navigate to='/' />;\n"
        )
        assert _auto_import_missing_named_exports(src) == src

    def test_skips_when_locally_declared(self):
        from llm_lab.runtime.services.scaffolding import _auto_import_missing_named_exports

        src = (
            "import { Routes } from 'react-router-dom';\n"
            "const Navigate = () => null;\n"
            "<Navigate />;\n"
        )
        assert _auto_import_missing_named_exports(src) == src

    def test_full_sanitize_fixes_missing_navigate(self):
        bad = (
            "import { Routes, Route, useNavigate } from 'react-router-dom';\n"
            "const App = () => (\n"
            "  <Routes>\n"
            "    <Route path='*' element={<Navigate to='/' replace />} />\n"
            "  </Routes>\n"
            ");\n"
        )
        out = _sanitize_frontend_code(bad)
        assert "Navigate" in out and "from 'react-router-dom'" in out


class TestAutoImportDefault:
    def test_adds_toast_default_import(self):
        from llm_lab.runtime.services.scaffolding import _auto_import_missing_named_exports

        src = (
            "import React from 'react';\n"
            "function App() { toast('hi'); return null; }\n"
        )
        out = _auto_import_missing_named_exports(src)
        assert "import toast from 'react-hot-toast'" in out

    def test_adds_clsx_default_import(self):
        from llm_lab.runtime.services.scaffolding import _auto_import_missing_named_exports

        src = (
            "import React from 'react';\n"
            "const c = clsx('a', 'b');\n"
        )
        out = _auto_import_missing_named_exports(src)
        assert "import clsx from 'clsx'" in out

    def test_skips_when_already_imported(self):
        from llm_lab.runtime.services.scaffolding import _auto_import_missing_named_exports

        src = (
            "import toast from 'react-hot-toast';\n"
            "toast('hi');\n"
        )
        out = _auto_import_missing_named_exports(src)
        assert out.count("from 'react-hot-toast'") == 1


class TestBackendSanitizer:
    def test_dedupes_duplicate_def(self):
        from llm_lab.runtime.services.scaffolding import _sanitize_backend_code

        src = (
            "from flask import Flask\n"
            "app = Flask(__name__)\n"
            "@app.route('/api/foo')\n"
            "def foo():\n"
            "    return 'a'\n"
            "@app.route('/api/foo2')\n"
            "def foo():\n"
            "    return 'b'\n"
        )
        out = _sanitize_backend_code(src)
        # Second def should be renamed
        assert "def foo__dup1" in out
        # First def preserved
        assert out.count("def foo(") == 1

    def test_auto_adds_missing_flask_imports(self):
        from llm_lab.runtime.services.scaffolding import _sanitize_backend_code

        src = (
            "from flask import Flask\n"
            "app = Flask(__name__)\n"
            "@app.route('/')\n"
            "def index():\n"
            "    return jsonify({'x': request.args.get('q')})\n"
        )
        out = _sanitize_backend_code(src)
        # The first import line should now include jsonify and request.
        first = [l for l in out.splitlines() if l.startswith("from flask")][0]
        assert "jsonify" in first
        assert "request" in first
        assert "Flask" in first

    def test_strips_localhost_from_backend(self):
        from llm_lab.runtime.services.scaffolding import _sanitize_backend_code

        src = 'CORS_ORIGINS = "http://localhost:3000"\n'
        out = _sanitize_backend_code(src)
        assert "localhost" not in out

    def test_no_op_when_no_flask_import(self):
        """Don't invent a flask import block for plain python."""
        from llm_lab.runtime.services.scaffolding import _sanitize_backend_code

        src = "x = 1\nprint(jsonify)\n"
        out = _sanitize_backend_code(src)
        assert "from flask import" not in out
