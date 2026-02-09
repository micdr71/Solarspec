"""Tests for SolarSpec API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from solarspec.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_index_page(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert "SolarSpec" in response.text


class TestAnalyzeEndpoint:
    def test_analyze_missing_address(self, client: TestClient) -> None:
        response = client.post("/api/analyze", json={"address": ""})
        # Empty address will fail geocoding
        assert response.status_code in (400, 500)

    def test_analyze_invalid_json(self, client: TestClient) -> None:
        response = client.post("/api/analyze", content=b"not json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422


class TestDesignEndpoint:
    def test_design_missing_fields(self, client: TestClient) -> None:
        response = client.post("/api/design", json={"address": "test"})
        assert response.status_code == 422  # validation error

    def test_design_invalid_consumption(self, client: TestClient) -> None:
        response = client.post("/api/design", json={
            "address": "test",
            "annual_consumption_kwh": "not a number",
            "roof_area_m2": 40,
        })
        assert response.status_code == 422


class TestGenerateEndpoint:
    def test_generate_missing_fields(self, client: TestClient) -> None:
        response = client.post("/api/generate", json={"address": "test"})
        assert response.status_code == 422
