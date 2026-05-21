from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from ninja.testing import TestClient

from config.api import api
from llm_lab.analysis.tests.factories import AnalysisResultFactory
from llm_lab.analysis.tests.factories import AnalysisTaskFactory
from llm_lab.analysis.tests.factories import FindingFactory


@pytest.fixture(autouse=True)
def _no_redis(monkeypatch):
    """Silence realtime.publish — Redis is unavailable in the test environment."""
    monkeypatch.setattr("llm_lab.realtime.events.publish", lambda *a, **kw: None)


@pytest.fixture(autouse=True)
def _single_threaded_pool():
    """Replace the shared analyzer pool with a single-worker executor.

    SQLite (used in tests) does not support concurrent writers.  Running the
    analyzer pool with max_workers=1 serialises all DB writes and avoids
    'database is locked' errors without changing production behaviour.
    """
    single = ThreadPoolExecutor(max_workers=1, thread_name_prefix="test-analyzer")
    with patch("llm_lab.analysis.services.executor_service._get_pool", return_value=single):
        yield
    single.shutdown(wait=False)


@pytest.fixture
def analysis_task(user):
    return AnalysisTaskFactory(created_by=user)


@pytest.fixture
def analysis_result(analysis_task):
    return AnalysisResultFactory(task=analysis_task)


@pytest.fixture
def finding(analysis_result):
    return FindingFactory(result=analysis_result)


@pytest.fixture
def api_client(user):
    client = TestClient(api)
    client.user = user
    return client
