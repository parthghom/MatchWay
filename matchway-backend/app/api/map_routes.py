from fastapi import APIRouter, HTTPException
from app.services import ola_places

router = APIRouter(prefix="/maps")


def _fail(e):
    if isinstance(e, RuntimeError) and "key missing" in str(e):
        return HTTPException(status_code=503, detail="Maps is not configured on the server")
    if isinstance(e, ValueError):
        return HTTPException(status_code=400, detail=str(e))
    return HTTPException(status_code=502, detail="Maps service is unavailable right now")


@router.get("/search")
async def search(q: str, lat: float | None = None, lon: float | None = None):
    if len(q.strip()) < 2:
        return []
    try:
        return ola_places.search_places(q.strip(), lat, lon)
    except Exception as e:
        raise _fail(e)


@router.get("/place")
async def place(place_id: str):
    try:
        return ola_places.place_details(place_id)
    except Exception as e:
        raise _fail(e)


@router.get("/reverse")
async def reverse(lat: float, lon: float):
    try:
        return {"address": ola_places.reverse_geocode(lat, lon)}
    except Exception as e:
        raise _fail(e)


@router.get("/route")
async def route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float):
    try:
        return ola_places.route_line(origin_lat, origin_lon, dest_lat, dest_lon)
    except Exception as e:
        raise _fail(e)
