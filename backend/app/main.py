from fastapi import FastAPI
from .routes.alerts import router as alerts_router
from .routes.ua import router as ua_router
from .routes.debug import router as debug_router
from .routes.db import router as db_router

app = FastAPI(title="Air Alert Risk API")

app.include_router(alerts_router)
app.include_router(ua_router)
app.include_router(debug_router)
app.include_router(db_router)

@app.get("/health")
def health():
    return {"status": "ok"}
