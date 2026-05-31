import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BlindWatch AI OS API Gateway",
    description="Entrypoint router for routing client traffic to distributed microservices.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "/api/v1/auth":              "http://127.0.0.1:8001",
    "/api/v1/users":             "http://127.0.0.1:8001",
    "/api/v1/cameras":           "http://127.0.0.1:8002",
    "/api/v1/live-feed":         "http://127.0.0.1:8003",
    "/api/v1/entities":          "http://127.0.0.1:8003",
    "/api/v1/vision":            "http://127.0.0.1:8003",
    "/api/v1/events":            "http://127.0.0.1:8005",
    "/api/v1/evidence":          "http://127.0.0.1:8005",
    "/api/v1/privacy":           "http://127.0.0.1:8004",
    "/api/v1/identity-requests": "http://127.0.0.1:8009",
    "/api/v1/audit":             "http://127.0.0.1:8006",
    "/api/v1/analytics":         "http://127.0.0.1:8007",
    "/api/v1/simulator":         "http://127.0.0.1:8008",
    "/api/v1/reports":           "http://127.0.0.1:8007",
    "/api/v1/notifications":     "http://127.0.0.1:8001",
    "/healthz":                  "http://127.0.0.1:8001"
}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_request(request: Request, path: str):
    # Match request path to respective service URL
    full_path = f"/{path}"
    if "/identity" in full_path:
        target_service_url = "http://127.0.0.1:8009"
    else:
        for prefix, service_url in SERVICES.items():
            if full_path.startswith(prefix):
                target_service_url = service_url
                break
            
    if not target_service_url:
        raise HTTPException(status_code=404, detail="Service route not resolved")
        
    url = f"{target_service_url}/{path}"
    
    # Read client request properties
    query_params = dict(request.query_params)
    request_body = await request.body()
    request_headers = dict(request.headers)
    
    # Remove client host headers
    if "host" in request_headers:
        del request_headers["host"]
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=request_headers,
                params=query_params,
                content=request_body,
                timeout=10.0
            )
            # Reconstruct response to client
            headers_to_forward = dict(response.headers)
            # Prevent duplicate content-length header mismatches
            if "content-length" in headers_to_forward:
                del headers_to_forward["content-length"]
            
            # Strip downstream CORS headers to let the Gateway CORSMiddleware handle it exclusively
            cors_headers = [k for k in headers_to_forward.keys() if k.lower().startswith("access-control-")]
            for k in cors_headers:
                del headers_to_forward[k]
                
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=headers_to_forward
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Bad Gateway (Microservice Unresponsive): {e}")

import datetime
import random
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "type": "NEW_EVENT",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "message": "Security threat signature detected at Sector C"
            })
            await asyncio.sleep(4.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "severity": "HIGH",
                "event_type": "Possible Weapon",
                "message": "Immediate confirmation required for threat code #88B"
            })
            await asyncio.sleep(7.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.websocket("/ws/live-feed")
async def ws_live_feed(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "entity": "ENT_93A7",
                "camera": "Gate Alpha North",
                "dwell_time": random.randint(15, 300)
            })
            await asyncio.sleep(3.0)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.websocket("/ws/live-feed/{camera_id}")
async def ws_live_feed_camera(websocket: WebSocket, camera_id: str):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "frame": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "entities": [
                    {
                        "entity_id": "ENT_A93F",
                        "x": random.randint(150, 750),
                        "y": random.randint(150, 550),
                        "risk_score": random.randint(10, 85)
                    }
                ]
            })
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

