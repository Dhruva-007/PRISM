"""
Tests for PRISM FastAPI endpoints.

Verifies:
- Health endpoints respond correctly
- Cities endpoint returns all 4 cities
- Ingest endpoint accepts valid requests
- Analysis endpoint validates requests
- Intervention endpoint validates analysis_id requirement
- Simulation endpoint validates prerequisites
- Memory endpoint validates required fields
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestHealthEndpoints:
    def test_liveness_check(self, test_client):
        response = test_client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

    def test_health_check_returns_json(self, test_client):
        response = test_client.get("/api/v1/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_cities_endpoint_returns_four_cities(self, test_client):
        response = test_client.get("/api/v1/cities")
        assert response.status_code == 200
        data = response.json()
        assert "cities" in data
        assert len(data["cities"]) == 4

    def test_cities_contains_expected_city_ids(self, test_client):
        response = test_client.get("/api/v1/cities")
        data = response.json()
        city_ids = [c["city_id"] for c in data["cities"]]
        assert "hyderabad" in city_ids
        assert "delhi" in city_ids
        assert "bangalore" in city_ids
        assert "mumbai" in city_ids

    def test_cities_have_required_fields(self, test_client):
        response = test_client.get("/api/v1/cities")
        data = response.json()
        required = [
            "city_id", "display_name", "state", "country",
            "latitude", "longitude", "map_zoom",
            "district_count", "construction_sites"
        ]
        for city in data["cities"]:
            for field in required:
                assert field in city, f"Missing field '{field}' in city {city.get('city_id')}"


class TestIngestEndpoints:
    def test_list_events_returns_200(self, test_client):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = []
        mock_client.collection.return_value = mock_query

        with patch("app.routers.ingest.get_firestore_client", return_value=mock_client):
            with patch("app.services.ingestion.ingestion_service.get_firestore_client",
                       return_value=mock_client):
                response = test_client.get("/api/v1/ingest/events?limit=5")
                assert response.status_code == 200
                data = response.json()
                assert "events" in data
                assert "total" in data
                assert "limit" in data

    def test_list_events_invalid_source_returns_400(self, test_client):
        mock_client = MagicMock()
        with patch("app.routers.ingest.get_firestore_client", return_value=mock_client):
            response = test_client.get("/api/v1/ingest/events?source=invalid_source")
            assert response.status_code == 400

    def test_list_events_invalid_event_type_returns_400(self, test_client):
        mock_client = MagicMock()
        with patch("app.routers.ingest.get_firestore_client", return_value=mock_client):
            response = test_client.get("/api/v1/ingest/events?event_type=invalid_type")
            assert response.status_code == 400

    def test_trigger_accepts_valid_city_id(self, test_client):
        with patch(
            "app.routers.ingest.run_ingestion",
            new_callable=AsyncMock,
        ) as mock_ingest:
            from app.models.community import IngestTriggerResponse
            mock_ingest.return_value = IngestTriggerResponse(
                status="complete",
                events_ingested=9,
                sources_attempted=["openaq", "open_meteo", "health", "construction"],
                sources_succeeded=["openaq", "open_meteo", "health", "construction"],
                sources_failed=[],
                message="Ingested 9 events from 4 sources.",
            )
            response = test_client.post(
                "/api/v1/ingest/trigger",
                json={"city_id": "delhi"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "complete"
            assert data["events_ingested"] == 9


class TestAnalysisEndpoints:
    def test_list_analyses_returns_200(self, test_client):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = []
        mock_client.collection.return_value = mock_query

        with patch(
            "app.services.intelligence.analysis_service.get_firestore_client",
            return_value=mock_client,
        ):
            response = test_client.get("/api/v1/analysis?limit=5")
            assert response.status_code == 200
            data = response.json()
            assert "analyses" in data

    def test_get_nonexistent_analysis_returns_404(self, test_client):
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(
            "app.services.intelligence.analysis_service.get_firestore_client",
            return_value=mock_client,
        ):
            response = test_client.get("/api/v1/analysis/nonexistent-id-12345")
            assert response.status_code == 404


class TestInterventionEndpoints:
    def test_generate_without_analysis_id_returns_422(self, test_client):
        response = test_client.post("/api/v1/interventions/generate", json={})
        assert response.status_code == 422

    def test_generate_with_nonexistent_analysis_returns_400(self, test_client):
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(
            "app.services.intelligence.analysis_service.get_firestore_client",
            return_value=mock_client,
        ):
            with patch(
                "app.services.intervention.intervention_service.get_analysis",
                new_callable=AsyncMock,
                return_value=None,
            ):
                response = test_client.post(
                    "/api/v1/interventions/generate",
                    json={"analysis_id": "nonexistent-id"},
                )
                assert response.status_code == 400

    def test_list_interventions_returns_200(self, test_client):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = []
        mock_client.collection.return_value = mock_query

        with patch(
            "app.services.intervention.intervention_service.get_firestore_client",
            return_value=mock_client,
        ):
            response = test_client.get("/api/v1/interventions?limit=5")
            assert response.status_code == 200


class TestSimulationEndpoints:
    def test_run_simulation_without_analysis_id_returns_422(self, test_client):
        response = test_client.post("/api/v1/simulation/run", json={})
        assert response.status_code == 422

    def test_get_simulation_returns_200_for_valid_format(self, test_client):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.stream.return_value = []
        mock_client.collection.return_value = mock_query

        with patch(
            "app.services.simulation.simulation_service.get_firestore_client",
            return_value=mock_client,
        ):
            response = test_client.get("/api/v1/simulation/test-analysis-id")
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert data["results"] == []


class TestMemoryEndpoints:
    def test_record_without_required_fields_returns_422(self, test_client):
        response = test_client.post("/api/v1/memory/record", json={})
        assert response.status_code == 422

    def test_record_short_reason_returns_422(self, test_client):
        response = test_client.post(
            "/api/v1/memory/record",
            json={
                "analysis_id": "test-id",
                "selected_strategy_id": "strategy-id",
                "selection_reason": "short",
            },
        )
        assert response.status_code == 422

    def test_list_memory_returns_200(self, test_client):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = []
        mock_client.collection.return_value = mock_query

        with patch(
            "app.services.memory.decision_store.get_firestore_client",
            return_value=mock_client,
        ):
            response = test_client.get("/api/v1/memory")
            assert response.status_code == 200
            data = response.json()
            assert "records" in data

    def test_get_nonexistent_memory_returns_404(self, test_client):
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_client.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch(
            "app.services.memory.decision_store.get_firestore_client",
            return_value=mock_client,
        ):
            response = test_client.get("/api/v1/memory/nonexistent-id")
            assert response.status_code == 404