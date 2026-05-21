"""Static analyzers package."""

from __future__ import annotations

from llm_lab.analysis.services.static._common import JS_TS_EXTENSIONS
from llm_lab.analysis.services.static._common import PYTHON_EXTENSIONS
from llm_lab.analysis.services.static.bandit import BANDIT_CONFIDENCE_MAP
from llm_lab.analysis.services.static.bandit import BANDIT_SEVERITY_MAP
from llm_lab.analysis.services.static.bandit import BanditAnalyzer
from llm_lab.analysis.services.static.eslint import ESLINT_SEVERITY_MAP
from llm_lab.analysis.services.static.eslint import ESLintAnalyzer
from llm_lab.analysis.services.static.legacy import DetectSecretsAnalyzer
from llm_lab.analysis.services.static.legacy import MyPyAnalyzer
from llm_lab.analysis.services.static.legacy import NpmAuditAnalyzer
from llm_lab.analysis.services.static.legacy import PipAuditAnalyzer
from llm_lab.analysis.services.static.legacy import RadonAnalyzer
from llm_lab.analysis.services.static.legacy import RuffAnalyzer
from llm_lab.analysis.services.static.legacy import SafetyAnalyzer
from llm_lab.analysis.services.static.legacy import SemgrepAnalyzer
from llm_lab.analysis.services.static.legacy import VultureAnalyzer
from llm_lab.analysis.services.static.pylint import PYLINT_CATEGORY_MAP
from llm_lab.analysis.services.static.pylint import PYLINT_SEVERITY_MAP
from llm_lab.analysis.services.static.pylint import PylintAnalyzer
from llm_lab.analysis.services.static.web import HTMLValidatorAnalyzer
from llm_lab.analysis.services.static.web import StylelintAnalyzer

__all__ = [
    "BANDIT_CONFIDENCE_MAP",
    "BANDIT_SEVERITY_MAP",
    "ESLINT_SEVERITY_MAP",
    "JS_TS_EXTENSIONS",
    "PYLINT_CATEGORY_MAP",
    "PYLINT_SEVERITY_MAP",
    "PYTHON_EXTENSIONS",
    "BanditAnalyzer",
    "DetectSecretsAnalyzer",
    "ESLintAnalyzer",
    "HTMLValidatorAnalyzer",
    "MyPyAnalyzer",
    "NpmAuditAnalyzer",
    "PipAuditAnalyzer",
    "PylintAnalyzer",
    "RadonAnalyzer",
    "RuffAnalyzer",
    "SafetyAnalyzer",
    "SemgrepAnalyzer",
    "StylelintAnalyzer",
    "VultureAnalyzer",
]
