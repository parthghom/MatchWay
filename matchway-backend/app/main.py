from fastapi import FastAPI
from app import state
from app.data.pune_spots import seed_spots
from app.api.routes import router
from app.api import profile_routes, map_routes

app = FastAPI(title="MatchWay API")

app.include_router(router)
app.include_router(profile_routes.router)
app.include_router(map_routes.router)


@app.on_event("startup")
async def add_college_spots():
    # "Matchway Spot" at every Pune college entrance in app/data/pune_spots.py
    seed_spots(state.current.spots)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "MatchWay Backend is running"}
