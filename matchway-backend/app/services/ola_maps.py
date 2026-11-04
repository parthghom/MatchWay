import urllib.request
import json
import os

def parse_route(response_json):
    """Parses Ola Maps routing response to extract distance and duration."""
    if not response_json or response_json.get("status") != "SUCCESS":
        raise ValueError("Routing failed or invalid response")

    try:
        leg = response_json["routes"][0]["legs"][0]
        distance = leg["distance"]  # metres
        duration = leg["duration"]  # seconds
        return round(distance / 1000.0, 2), round(duration / 60.0, 2)
    except (KeyError, IndexError) as e:
        raise ValueError(f"Missing expected route data: {e}")

def route_distance_km(origin_lat, origin_lng, dest_lat, dest_lng, http_post=None):
    """Returns the road distance and time between two points using Ola Maps API."""

    # Get API Key from env or .env file
    api_key = os.environ.get("OLA_MAPS_API_KEY")
    if not api_key:
        # Manual .env parsing
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("OLA_MAPS_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

    if not api_key:
        raise RuntimeError("Ola Maps key missing")

    if http_post is None:
        def default_http_post(url, headers):
            req = urllib.request.Request(url, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.loads(response.read().decode("utf-8"))
            except Exception as e:
                raise RuntimeError(f"HTTP request failed: {e}")
        http_post = default_http_post

    # Build URL
    # POST https://api.olamaps.io/routing/v1/directions?origin=18.7603,73.3814&destination=18.7335,73.4459&api_key=YOUR_API_KEY
    url = (
        f"https://api.olamaps.io/routing/v1/directions"
        f"?origin={origin_lat},{origin_lng}"
        f"&destination={dest_lat},{dest_lng}"
        f"&api_key={api_key}"
    )

    headers = {"X-Request-Id": "matchway-request"}

    response_json = http_post(url, headers)
    return parse_route(response_json)
