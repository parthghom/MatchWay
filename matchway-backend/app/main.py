from fastapi import FastAPI
from app.api.routes import router
from app.api import profile_routes, map_routes

app = FastAPI(title="MatchWay API")

app.include_router(router)
app.include_router(profile_routes.router)
app.include_router(map_routes.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "MatchWay Backend is running"}
