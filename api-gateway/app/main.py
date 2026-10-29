
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
import httpx

app = FastAPI(title="Inventory API Gateway")

SERVICES = {
    "auth": "http://127.0.0.1:8001",
    "products": "http://127.0.0.1:8002",
    "inventory": "http://127.0.0.1:8003",
    "cart": "http://127.0.0.1:8004",
    "orders": "http://127.0.0.1:8005",
    "payments": "http://127.0.0.1:8006",
    "notifications": "http://127.0.0.1:8007",
    "reviews": "http://127.0.0.1:8008",
    "coupons": "http://127.0.0.1:8009",
    "returns": "http://127.0.0.1:8010",
    "analytics": "http://127.0.0.1:8011",
}


@app.get("/")
def home():
    return {
        "message": "API Gateway is running",
        "services": list(SERVICES.keys())
    }


@app.get("/health")
async def health():
    results = {}

    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, base_url in SERVICES.items():
            try:
                response = await client.get(base_url + "/")
                results[name] = (
                    "UP" if response.status_code == 200 else "ERROR"
                )
            except httpx.RequestError:
                results[name] = "DOWN"

    return {"services": results}


@app.api_route(
    "/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"]
)
async def gateway(service: str, path: str, request: Request):
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Unknown service")

    target_url = f"{SERVICES[service]}/{path}"

    if request.url.query:
        target_url += f"?{request.url.query}"

    body = await request.body()

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers={
                key: value
                for key, value in request.headers.items()
                if key.lower() not in [
                    "host", "content-length", "connection"
                ]
            }
        )

    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type")
    )
