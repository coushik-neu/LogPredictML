from app.websocket.manager import manager


async def emit_model_update(data):
    await manager.broadcast({"event": "model_update", "data": data})


async def emit_drift_update(data):
    await manager.broadcast({"event": "drift_update", "data": data})


async def emit_churn_update(data):
    await manager.broadcast({"event": "churn_update", "data": data})


async def emit_business_update(data):
    await manager.broadcast({"event": "business_update", "data": data})