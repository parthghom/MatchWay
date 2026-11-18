import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import ola_places
from app.services.ola_places import decode_polyline, parse_predictions, parse_place_details, parse_route_line


def test_decode_polyline_known_example():
    # Standard example from the polyline format description
    pts = decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
    assert pts == [[38.5, -120.2], [40.7, -120.95], [43.252, -126.453]]


def test_decode_polyline_empty_and_bad():
    assert decode_polyline("") == []
    with pytest.raises(ValueError):
        decode_polyline("_")


def test_parse_predictions():
    data = {"predictions": [{
        "place_id": "p1", "description": "City Mall, Pune, Maharashtra",
        "structured_formatting": {"main_text": "City Mall"},
        "geometry": {"location": {"lat": 18.5, "lng": 73.8}},
    }, {"place_id": "p2", "description": "Station Road, Pune"}]}
    out = parse_predictions(data)
    assert out[0] == {"place_id": "p1", "name": "City Mall", "address": "City Mall, Pune, Maharashtra", "lat": 18.5, "lon": 73.8, "distance_m": None}
    assert out[1]["name"] == "Station Road" and out[1]["lat"] is None
    assert parse_predictions({}) == []


def test_parse_place_details():
    data = {"result": {"name": "City Mall", "formatted_address": "Pune", "geometry": {"location": {"lat": 18.5, "lng": 73.8}}}}
    assert parse_place_details(data)["lon"] == 73.8
    with pytest.raises(ValueError):
        parse_place_details({"result": {}})


def test_parse_route_line():
    data = {"status": "SUCCESS", "routes": [{
        "overview_polyline": "_p~iF~ps|U_ulLnnqC",
        "legs": [{"distance": 11676, "duration": 1117}]}]}
    out = parse_route_line(data)
    assert out["km"] == 11.68 and out["minutes"] == 18.62 and len(out["points"]) == 2
    with pytest.raises(ValueError):
        parse_route_line({"status": "FAILED"})


def test_search_places_uses_key_and_location(monkeypatch):
    monkeypatch.setenv("OLA_MAPS_API_KEY", "k")
    seen = {}

    def fake_get(url, headers):
        seen["url"] = url
        return {"predictions": []}

    ola_places.search_places("mall", 18.7, 73.3, http_get=fake_get)
    assert "input=mall" in seen["url"] and "api_key=k" in seen["url"] and "location=18.7%2C73.3" in seen["url"]


def test_missing_key(monkeypatch):
    monkeypatch.delenv("OLA_MAPS_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="key missing"):
        ola_places.search_places("mall")


def test_api_search_short_query_and_no_key(monkeypatch):
    c = TestClient(app)
    assert c.get("/maps/search", params={"q": "a"}).json() == []
    monkeypatch.delenv("OLA_MAPS_API_KEY", raising=False)
    r = c.get("/maps/search", params={"q": "mall"})
    assert r.status_code == 503


def test_api_route(monkeypatch):
    monkeypatch.setattr(ola_places, "route_line", lambda *a: {"km": 1.0, "minutes": 2.0, "points": [[1, 2]]})
    r = TestClient(app).get("/maps/route", params={"origin_lat": 1, "origin_lon": 2, "dest_lat": 3, "dest_lon": 4})
    assert r.status_code == 200 and r.json()["km"] == 1.0


def test_search_places_limits_to_50km(monkeypatch):
    monkeypatch.setenv("OLA_MAPS_API_KEY", "k")
    seen = {}

    def fake_get(url, headers):
        seen["url"] = url
        return {"predictions": []}

    ola_places.search_places("mall", 18.7, 73.3, http_get=fake_get)
    assert "radius=50000" in seen["url"] and "strictbounds=true" in seen["url"]


def test_fetch_map_file_adds_our_key_only(monkeypatch):
    monkeypatch.setenv("OLA_MAPS_API_KEY", "ours")
    seen = {}

    def fake_get(url):
        seen["url"] = url
        return b"tile", "application/x-protobuf"

    body, ctype = ola_places.fetch_map_file("tiles/vector/v1/data/x/1/2/3.pbf", "api_key=theirs&a=1", http_get_bytes=fake_get)
    assert body == b"tile" and ctype == "application/x-protobuf"
    assert "api_key=ours" in seen["url"] and "theirs" not in seen["url"] and "a=1" in seen["url"]


def test_fetch_map_file_blocks_other_apis(monkeypatch):
    monkeypatch.setenv("OLA_MAPS_API_KEY", "k")
    for bad in ("places/v1/autocomplete", "routing/v1/directions", "tiles/../places/v1/details"):
        with pytest.raises(ValueError):
            ola_places.fetch_map_file(bad, "")


def test_map_proxy_route(monkeypatch):
    monkeypatch.setenv("OLA_MAPS_API_KEY", "k")
    monkeypatch.setattr(ola_places, "_http_get_bytes", lambda url: (b"{}", "application/json"))
    client = TestClient(app)
    ok = client.get("/maps/ola/tiles/vector/v1/styles/default-dark-standard/style.json")
    assert ok.status_code == 200 and ok.content == b"{}"
    assert client.get("/maps/ola/places/v1/autocomplete").status_code == 400


def test_fetch_map_file_encodes_spaces_in_font_names(monkeypatch):
    monkeypatch.setenv("OLA_MAPS_API_KEY", "k")
    seen = {}

    def fake_get(url):
        seen["url"] = url
        return b"f", "application/x-protobuf"

    ola_places.fetch_map_file("tiles/vector/v1/fonts/Gentona Semi Bold,Noto Sans Bold/0-255.pbf", "", http_get_bytes=fake_get)
    assert " " not in seen["url"] and "Gentona%20Semi%20Bold%2CNoto%20Sans%20Bold" in seen["url"]


def test_parse_predictions_keeps_distance():
    data = {"predictions": [{"place_id": "p1", "description": "A, Pune", "distance_meters": 2100}]}
    assert parse_predictions(data)[0]["distance_m"] == 2100


def _reverse_data():
    return {"results": [
        {"name": "Big Mall", "formatted_address": "Big Mall, Katraj, Pune",
         "geometry": {"location": {"lat": 18.4500, "lng": 73.8600}}},          # about 500 m from the pin
        {"name": "Chai Point", "formatted_address": "Chai Point, Katraj, Pune",
         "geometry": {"location": {"lat": 18.45002, "lng": 73.85501}}},        # about 2 m from the pin
    ]}


def test_reverse_picks_closest_place_not_first():
    best = ola_places.best_reverse_result(_reverse_data(), 18.45, 73.855)
    assert best["name"] == "Chai Point" and best["label"] == "Chai Point"
    assert best["distance_m"] < 10


def test_reverse_says_near_when_pin_is_not_on_the_place():
    data = {"results": [_reverse_data()["results"][0]]}
    best = ola_places.best_reverse_result(data, 18.45, 73.855)
    assert best["label"] == "Near Big Mall" and best["distance_m"] > 25


def test_reverse_uses_distance_meters_and_handles_empty():
    data = {"results": [{"name": "A", "formatted_address": "A, Pune", "distance_meters": 80},
                        {"name": "B", "formatted_address": "B, Pune", "distance_meters": 12}]}
    assert ola_places.best_reverse_result(data, 0, 0)["label"] == "B"
    assert ola_places.best_reverse_result({}, 0, 0)["label"] == ""
    assert ola_places.best_reverse_result({"results": [{"formatted_address": "X Road, Pune"}]}, 0, 0)["label"] == "X Road"
