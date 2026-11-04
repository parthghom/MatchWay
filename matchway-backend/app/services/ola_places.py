# Ola Maps helpers for the map screen: place search (autocomplete), place
# details (name -> coordinates) and the drawn route line.
# The API key stays on the server; the app only talks to our own endpoints.
# decode_polyline turns Ola's compressed route string into [lat, lon] points:
# each number is stored as a 5-bit chunk difference from the previous point.
import json
import os
import urllib.parse
import urllib.request

BASE = "https://api.olamaps.io"


def _api_key():
    key = os.environ.get("OLA_MAPS_API_KEY")
    if not key:
        raise RuntimeError("Ola Maps key missing")
    return key


def _http_get(url, headers=None):
    req = urllib.request.Request(url, method="GET", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {e}")


def _http_post(url, headers=None):
    req = urllib.request.Request(url, method="POST", headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {e}")


def parse_predictions(data):
    """Turns an Ola autocomplete response into a short list for the app."""
    out = []
    for p in (data or {}).get("predictions", []) or []:
        sf = p.get("structured_formatting") or {}
        loc = ((p.get("geometry") or {}).get("location")) or {}
        out.append({
            "place_id": p.get("place_id"),
            "name": sf.get("main_text") or (p.get("description") or "").split(",")[0],
            "address": p.get("description") or "",
            "lat": loc.get("lat"),
            "lon": loc.get("lng"),
        })
    return out


def search_places(text, lat=None, lon=None, http_get=None):
    key = _api_key()
    http_get = http_get or _http_get
    params = {"input": text, "api_key": key}
    if lat is not None and lon is not None:
        params["location"] = f"{lat},{lon}"
    url = f"{BASE}/places/v1/autocomplete?" + urllib.parse.urlencode(params)
    return parse_predictions(http_get(url, {"X-Request-Id": "matchway-search"}))


def parse_place_details(data):
    result = (data or {}).get("result") or {}
    loc = ((result.get("geometry") or {}).get("location")) or {}
    if loc.get("lat") is None or loc.get("lng") is None:
        raise ValueError("Place has no coordinates")
    return {
        "name": result.get("name") or "",
        "address": result.get("formatted_address") or "",
        "lat": loc["lat"],
        "lon": loc["lng"],
    }


def place_details(place_id, http_get=None):
    key = _api_key()
    http_get = http_get or _http_get
    params = {"place_id": place_id, "api_key": key}
    url = f"{BASE}/places/v1/details?" + urllib.parse.urlencode(params)
    return parse_place_details(http_get(url, {"X-Request-Id": "matchway-details"}))


def reverse_geocode(lat, lon, http_get=None):
    """Coordinates -> a readable address (used for 'Current location')."""
    key = _api_key()
    http_get = http_get or _http_get
    params = {"latlng": f"{lat},{lon}", "api_key": key}
    url = f"{BASE}/places/v1/reverse-geocode?" + urllib.parse.urlencode(params)
    data = http_get(url, {"X-Request-Id": "matchway-reverse"})
    results = (data or {}).get("results") or []
    return results[0].get("formatted_address", "") if results else ""


def decode_polyline(encoded):
    """Decodes a Google-style encoded polyline (5 decimal places) by hand."""
    points = []
    index = lat = lon = 0
    n = len(encoded or "")
    while index < n:
        for which in (0, 1):
            shift = result = 0
            while True:
                if index >= n:
                    raise ValueError("Bad polyline")
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if (result & 1) else (result >> 1)
            if which == 0:
                lat += delta
            else:
                lon += delta
        points.append([lat / 1e5, lon / 1e5])
    return points


def parse_route_line(data):
    if not data or data.get("status") not in ("SUCCESS", "OK", "ok"):
        raise ValueError("Routing failed or invalid response")
    try:
        route = data["routes"][0]
        leg = route["legs"][0]
        km = round(leg["distance"] / 1000.0, 2)
        minutes = round(leg["duration"] / 60.0, 2)
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Missing expected route data: {e}")
    encoded = route.get("overview_polyline")
    if isinstance(encoded, dict):
        encoded = encoded.get("points")
    points = decode_polyline(encoded) if encoded else []
    return {"km": km, "minutes": minutes, "points": points}


def route_line(o_lat, o_lon, d_lat, d_lon, http_post=None):
    key = _api_key()
    http_post = http_post or _http_post
    params = {"origin": f"{o_lat},{o_lon}", "destination": f"{d_lat},{d_lon}", "api_key": key}
    url = f"{BASE}/routing/v1/directions?" + urllib.parse.urlencode(params)
    return parse_route_line(http_post(url, {"X-Request-Id": "matchway-route"}))
