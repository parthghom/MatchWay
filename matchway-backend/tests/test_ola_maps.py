import pytest
from app.services.ola_maps import parse_route, route_distance_km
from app import state
from fastapi.testclient import TestClient
from fastapi import FastAPI

client = TestClient(FastAPI()) # Mock client for the route if needed, but we can use the app

def test_parse_route():
    sample = {
        "status": "SUCCESS",
        "routes": [{"legs": [{"distance": 11676, "duration": 1117}]}]
    }
    assert parse_route(sample) == (11.68, 18.62)

    with pytest.raises(ValueError):
        parse_route({})

    with pytest.raises(ValueError):
        parse_route({"status": "FAILED"})

def test_route_distance_km(monkeypatch):
    def fake_http_post(url, headers):
        return {
            "status": "SUCCESS",
            "routes": [{"legs": [{"distance": 11676, "duration": 1117}]}]
        }

    monkeypatch.setenv("OLA_MAPS_API_KEY", "test")
    res = route_distance_km(18.7, 73.3, 18.8, 73.4, http_post=fake_http_post)
    assert res == (11.68, 18.62)

def test_route_distance_km_no_key(monkeypatch):
    monkeypatch.delenv("OLA_MAPS_API_KEY", raising=False)
    # Ensure no .env file exists or is read by using a fake http_post but the key check happens first
    with pytest.raises(RuntimeError, match="Ola Maps key missing"):
        route_distance_km(18.7, 73.3, 18.8, 73.4)

def test_fare_estimate_ola(monkeypatch):
    from app.api.routes import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    test_client = TestClient(app)

    # Mock routing in state
    state.current.routing = lambda o_lat, o_lon, d_lat, d_lon: (10.0, 25.0)

    response = test_client.get("/fare/estimate?vehicle_type=cab&origin_lat=1&origin_lon=1&dest_lat=2&dest_lon=2&riders=1")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "ola_maps"
    assert data["km"] == 10.0
    assert data["minutes"] == 25.0

def test_fare_estimate_fallback(monkeypatch):
    from app.api.routes import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    test_client = TestClient(app)

    # Mock routing to raise exception
    state.current.routing = lambda o_lat, o_lon, d_lat, d_lon: (_ for _ in ()).throw(Exception("API Error"))
    # The lambda above doesn't work for throwing. Use a proper function.
    def raise_err(*args):
        raise Exception("API Error")
    state.current.routing = raise_err

    response = test_client.get("/fare/estimate?vehicle_type=cab&origin_lat=1&origin_lon=1&dest_lat=2&dest_lon=2&riders=1")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "straight_line"
    assert data["minutes"] is None

def test_fare_estimate_invalid_vehicle():
    from app.api.routes import router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    test_client = TestClient(app)
    
    state.current.routing = lambda *a: (10.0, 25.0)
    response = test_client.get("/fare/estimate?vehicle_type=plane&origin_lat=1&origin_lon=1&dest_lat=2&dest_lon=2")
    assert response.status_code == 400
