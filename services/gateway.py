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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICES = {
    "/api/auth": "http://127.0.0.1:8001",
    "/api/users": "http://127.0.0.1:8001",
    "/api/cameras": "http://127.0.0.1:8002",
    "/api/entities": "http://127.0.0.1:8003",
    "/api/events": "http://127.0.0.1:8005",
    "/api/privacy-metrics": "http://127.0.0.1:8004",
    "/api/audit-logs": "http://127.0.0.1:8006",
    "/api/analytics": "http://127.0.0.1:8007",
    "/api/simulator": "http://127.0.0.1:8008",
    "/api/identity-requests": "http://127.0.0.1:8009",
    "/api/reports": "http://127.0.0.1:8007",
    "/healthz": "http://127.0.0.1:8001"
}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def route_request(request: Request, path: str):
    # Match request path to respective service URL
    full_path = f"/{path}"
    target_service_url = None
    
    # Special route override: Camera feed queries go to Vision Service
    if full_path.startswith("/api/cameras") and full_path.endswith("/feed"):
        target_service_url = "http://127.0.0.1:8003"
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
                
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=headers_to_forward
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Bad Gateway (Microservice Unresponsive): {e}")
