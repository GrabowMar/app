from http import HTTPStatus
from unittest.mock import patch

import pytest

from llm_lab.llm_models.models import LLMModel
from llm_lab.llm_models.tests.factories import LLMModelFactory


@pytest.fixture
def api_client(client, user):
    """Authenticated test client."""
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestModelsListAPI:
    def test_list_requires_auth(self, client):
        resp = client.get("/api/models/")
        assert resp.status_code == HTTPStatus.UNAUTHORIZED

    def test_list_empty(self, api_client):
        resp = api_client.get("/api/models/")
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_models(self, api_client):
        LLMModelFactory.create_batch(3)
        resp = api_client.get("/api/models/")
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        batch_size = 3
        assert data["total"] == batch_size
        assert len(data["items"]) == batch_size

    def test_search(self, api_client):
        LLMModelFactory(
            model_name="GPT-4o",
            model_id="openai/gpt-4o",
            canonical_slug="openai_gpt-4o",
        )
        LLMModelFactory(
            model_name="Claude",
            model_id="anthropic/claude",
            canonical_slug="anthropic_claude",
        )
        resp = api_client.get("/api/models/?search=GPT")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["model_name"] == "GPT-4o"

    def test_filter_by_provider(self, api_client):
        LLMModelFactory(
            provider="openai",
            model_id="openai/m1",
            canonical_slug="openai_m1",
        )
        LLMModelFactory(
            provider="anthropic",
            model_id="anthropic/m2",
            canonical_slug="anthropic_m2",
        )
        resp = api_client.get("/api/models/?provider=openai")
        data = resp.json()
        assert data["total"] == 1

    def test_pagination(self, api_client):
        total_models = 5
        page_size = 2
        expected_pages = 3
        for i in range(total_models):
            LLMModelFactory(model_id=f"p/m{i}", canonical_slug=f"p_m{i}")
        resp = api_client.get("/api/models/?per_page=2&page=1")
        data = resp.json()
        assert data["total"] == total_models
        assert len(data["items"]) == page_size
        assert data["pages"] == expected_pages


@pytest.mark.django_db
class TestModelDetailAPI:
    def test_get_model(self, api_client):
        m = LLMModelFactory(
            canonical_slug="openai_gpt-4o",
            model_id="openai/gpt-4o",
        )
        resp = api_client.get(f"/api/models/detail/{m.canonical_slug}/")
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["canonical_slug"] == "openai_gpt-4o"

    def test_not_found(self, api_client):
        resp = api_client.get("/api/models/detail/nonexistent/")
        assert resp.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.django_db
class TestModelStatsAPI:
    def test_stats_empty(self, api_client):
        resp = api_client.get("/api/models/stats/")
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["total"] == 0

    def test_stats_with_data(self, api_client):
        LLMModelFactory(
            provider="openai",
            model_id="o/m1",
            canonical_slug="o_m1",
            is_free=True,
        )
        LLMModelFactory(
            provider="anthropic",
            model_id="a/m2",
            canonical_slug="a_m2",
            is_free=False,
        )
        resp = api_client.get("/api/models/stats/")
        data = resp.json()
        expected_count = 2
        assert data["total"] == expected_count
        assert data["providers"] == expected_count
        assert data["free"] == 1


@pytest.mark.django_db
class TestProvidersAPI:
    def test_list_providers(self, api_client):
        LLMModelFactory(provider="openai", model_id="o/m1", canonical_slug="o_m1")
        LLMModelFactory(provider="anthropic", model_id="a/m2", canonical_slug="a_m2")
        resp = api_client.get("/api/models/providers/")
        assert resp.status_code == HTTPStatus.OK
        providers = resp.json()
        assert "openai" in providers
        assert "anthropic" in providers


@pytest.mark.django_db
class TestSyncAPI:
    @patch("llm_lab.llm_models.api.views.sync_models_from_openrouter")
    def test_sync(self, mock_sync, api_client):
        expected_fetched = 100
        expected_upserted = 95
        mock_sync.return_value = {
            "fetched": expected_fetched,
            "upserted": expected_upserted,
        }
        resp = api_client.post("/api/models/sync/")
        assert resp.status_code == HTTPStatus.OK
        data = resp.json()
        assert data["fetched"] == expected_fetched
        assert data["upserted"] == expected_upserted


@pytest.mark.django_db
class TestDeleteAPI:
    def test_delete(self, api_client):
        m = LLMModelFactory(
            model_id="del/test",
            canonical_slug="del_test",
        )
        resp = api_client.delete(f"/api/models/detail/{m.canonical_slug}/")
        assert resp.status_code == HTTPStatus.OK
        assert not LLMModel.objects.filter(canonical_slug="del_test").exists()
