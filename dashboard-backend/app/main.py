from fastapi import FastAPI, WebSocket
import asyncio

from app.routes import model, drift, customers, performance, business
from app.websocket.manager import manager
from app.services.event_service import monitor_changes

app = FastAPI(title="Real-Time Churn + Business Dashboard Backend")


# -------------------------------------
# REST APIs
# -------------------------------------

app.include_router(model.router, prefix="/api")
app.include_router(drift.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(performance.router, prefix="/api")
app.include_router(business.router, prefix="/api")


# -------------------------------------
# WebSocket
# -------------------------------------

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        manager.disconnect(websocket)


# -------------------------------------
# EVENT LOOP
# -------------------------------------

@app.on_event("startup")
async def start_events():
    asyncio.create_task(monitor_changes())